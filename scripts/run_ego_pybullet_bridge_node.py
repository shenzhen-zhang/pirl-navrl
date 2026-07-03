#!/usr/bin/env python3
"""ROS-side bridge node for official EGO-Planner -> PyBullet diagnostics.

This file intentionally avoids importing the Python package because ROS Noetic
uses Python 3.8 while the main project targets Python 3.10+.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import rospy
import sensor_msgs.point_cloud2 as pc2
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from quadrotor_msgs.msg import PositionCommand
from sensor_msgs.msg import PointCloud2


START = (-4.0, 0.0, 1.0)
GOAL = (4.0, 0.0, 1.0)
OBSTACLES = (
    {"kind": "cylinder", "center": (-1.7, -0.25, 1.0), "radius": 0.45, "height": 2.0},
    {"kind": "cylinder", "center": (0.25, 0.35, 1.0), "radius": 0.55, "height": 2.0},
    {"kind": "sphere", "center": (1.85, -0.45, 1.15), "radius": 0.45, "height": None},
)
BOUNDS = ((-5.0, 5.0), (-5.0, 5.0), (0.0, 3.0))


class EgoPybulletBridgeNode:
    def __init__(
        self,
        output_path: Path,
        duration: float,
        rate_hz: float,
        kp: float,
        max_speed: float,
        goal_delay: float,
    ) -> None:
        self.output_path = output_path
        self.duration = duration
        self.rate_hz = rate_hz
        self.kp = kp
        self.max_speed = max_speed
        self.goal_delay = goal_delay
        self.goal_published = False
        self.position = list(START)
        self.velocity = [0.0, 0.0, 0.0]
        self.last_command = None
        self.records = 0
        self.min_clearance = float("inf")
        self.odom_pub = rospy.Publisher("/visual_slam/odom", Odometry, queue_size=10)
        self.cloud_pub = rospy.Publisher("/pirl_navrl/cloud", PointCloud2, queue_size=3)
        self.goal_pub = rospy.Publisher("/move_base_simple/goal", PoseStamped, queue_size=1, latch=True)
        self.cmd_sub = rospy.Subscriber("/planning/pos_cmd", PositionCommand, self.command_callback, queue_size=10)
        self.pointcloud_points = sample_obstacle_points(OBSTACLES, resolution=0.35)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.output_path.open("w", encoding="utf-8")

    def command_callback(self, msg: PositionCommand) -> None:
        self.last_command = msg

    def close(self) -> None:
        self.handle.close()

    def run(self) -> dict:
        rate = rospy.Rate(self.rate_hz)
        start_time = rospy.Time.now()
        previous_time = start_time
        while not rospy.is_shutdown():
            now = rospy.Time.now()
            elapsed = (now - start_time).to_sec()
            if elapsed >= self.duration:
                break
            dt = max((now - previous_time).to_sec(), 1.0 / self.rate_hz)
            previous_time = now

            desired_velocity = self.compute_desired_velocity()
            self.velocity = list(desired_velocity)
            self.position = clamp_position(
                (
                    self.position[0] + self.velocity[0] * dt,
                    self.position[1] + self.velocity[1] * dt,
                    self.position[2] + self.velocity[2] * dt,
                )
            )
            clearance = min_clearance(self.position)
            self.min_clearance = min(self.min_clearance, clearance)
            distance_to_goal = distance(self.position, GOAL)

            self.publish_odom(now)
            self.publish_cloud(now)
            if elapsed >= self.goal_delay and not self.goal_published:
                self.publish_goal(now)
                self.goal_published = True
            self.write_record(elapsed, desired_velocity, clearance, distance_to_goal)
            self.records += 1
            if distance_to_goal < 0.35 and self.last_command is not None:
                break
            rate.sleep()

        summary = {
            "records": self.records,
            "final_position": self.position,
            "final_distance_to_goal": distance(self.position, GOAL),
            "min_clearance": self.min_clearance,
            "command_received": self.last_command is not None,
            "output_path": str(self.output_path),
        }
        return summary

    def compute_desired_velocity(self) -> tuple[float, float, float]:
        if self.last_command is None:
            return (0.0, 0.0, 0.0)
        target = (
            self.last_command.position.x,
            self.last_command.position.y,
            self.last_command.position.z,
        )
        raw = tuple(self.kp * (target[i] - self.position[i]) for i in range(3))
        return clip_norm(raw, self.max_speed)

    def publish_odom(self, stamp: rospy.Time) -> None:
        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = "world"
        odom.child_frame_id = "base_link"
        odom.pose.pose.position.x = self.position[0]
        odom.pose.pose.position.y = self.position[1]
        odom.pose.pose.position.z = self.position[2]
        odom.pose.pose.orientation.w = 1.0
        odom.twist.twist.linear.x = self.velocity[0]
        odom.twist.twist.linear.y = self.velocity[1]
        odom.twist.twist.linear.z = self.velocity[2]
        self.odom_pub.publish(odom)

    def publish_cloud(self, stamp: rospy.Time) -> None:
        header = rospy.Header()
        header.stamp = stamp
        header.frame_id = "world"
        cloud = pc2.create_cloud_xyz32(header, self.pointcloud_points)
        self.cloud_pub.publish(cloud)

    def publish_goal(self, stamp: rospy.Time) -> None:
        goal = PoseStamped()
        goal.header.stamp = stamp
        goal.header.frame_id = "world"
        goal.pose.position.x = GOAL[0]
        goal.pose.position.y = GOAL[1]
        goal.pose.position.z = GOAL[2]
        goal.pose.orientation.w = 1.0
        self.goal_pub.publish(goal)

    def write_record(
        self,
        elapsed: float,
        desired_velocity: tuple[float, float, float],
        clearance: float,
        distance_to_goal: float,
    ) -> None:
        command_position = None
        command_velocity = None
        if self.last_command is not None:
            command_position = [
                self.last_command.position.x,
                self.last_command.position.y,
                self.last_command.position.z,
            ]
            command_velocity = [
                self.last_command.velocity.x,
                self.last_command.velocity.y,
                self.last_command.velocity.z,
            ]
        record = {
            "task_id": "TASK_02",
            "output_type": "diagnostic",
            "platform_id": "gym_pybullet_drones_pybullet",
            "external_planner": "ego_planner_official_sidecar",
            "bridge_status": "official_ego_ros_sidecar",
            "planner_mode": "official_ego_planner",
            "scenario_id": "ego_like_static_v0",
            "seed": 0,
            "step": self.records,
            "elapsed": elapsed,
            "position": self.position,
            "goal": list(GOAL),
            "desired_velocity": list(desired_velocity),
            "ego_command_position": command_position,
            "ego_command_velocity": command_velocity,
            "command_received": self.last_command is not None,
            "goal_published": self.goal_published,
            "min_clearance": clearance,
            "distance_to_goal": distance_to_goal,
            "obstacles": OBSTACLES,
            "pointcloud_points": len(self.pointcloud_points),
        }
        self.handle.write(json.dumps(record, sort_keys=True) + "\n")
        self.handle.flush()


def sample_obstacle_points(obstacles, resolution: float) -> list[tuple[float, float, float]]:
    points: list[tuple[float, float, float]] = []
    for obstacle in obstacles:
        center = obstacle["center"]
        radius = obstacle["radius"]
        if obstacle["kind"] == "sphere":
            rings = max(4, int(math.ceil(math.pi * radius / resolution)))
            columns = max(8, int(math.ceil(2.0 * math.pi * radius / resolution)))
            for ring in range(rings + 1):
                phi = math.pi * ring / rings
                z = center[2] + radius * math.cos(phi)
                radial = radius * math.sin(phi)
                for column in range(columns):
                    theta = 2.0 * math.pi * column / columns
                    points.append((center[0] + radial * math.cos(theta), center[1] + radial * math.sin(theta), z))
        else:
            height = obstacle["height"] or 2.0
            columns = max(8, int(math.ceil(2.0 * math.pi * radius / resolution)))
            layers = max(2, int(math.ceil(height / resolution)))
            bottom = center[2] - height / 2.0
            for layer in range(layers + 1):
                z = bottom + height * layer / layers
                for column in range(columns):
                    theta = 2.0 * math.pi * column / columns
                    points.append((center[0] + radius * math.cos(theta), center[1] + radius * math.sin(theta), z))
    return points


def clip_norm(vector: tuple[float, float, float], max_norm: float) -> tuple[float, float, float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0 or norm <= max_norm:
        return vector
    scale = max_norm / norm
    return (vector[0] * scale, vector[1] * scale, vector[2] * scale)


def clamp_position(position: tuple[float, float, float]) -> list[float]:
    return [
        min(max(position[0], BOUNDS[0][0]), BOUNDS[0][1]),
        min(max(position[1], BOUNDS[1][0]), BOUNDS[1][1]),
        min(max(position[2], BOUNDS[2][0]), BOUNDS[2][1]),
    ]


def min_clearance(position: list[float]) -> float:
    return min(clearance_to_obstacle(position, obstacle) for obstacle in OBSTACLES)


def clearance_to_obstacle(position: list[float], obstacle: dict) -> float:
    center = obstacle["center"]
    if obstacle["kind"] == "sphere":
        return distance(position, center) - obstacle["radius"]
    height = obstacle["height"] or 2.0
    horizontal = math.hypot(position[0] - center[0], position[1] - center[1]) - obstacle["radius"]
    vertical_excess = max(abs(position[2] - center[2]) - height / 2.0, 0.0)
    if vertical_excess == 0.0:
        return horizontal
    return math.hypot(max(horizontal, 0.0), vertical_excess)


def distance(left, right) -> float:
    return math.sqrt(sum((left[i] - right[i]) ** 2 for i in range(3)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration", type=float, default=18.0)
    parser.add_argument("--rate-hz", type=float, default=20.0)
    parser.add_argument("--kp", type=float, default=1.4)
    parser.add_argument("--max-speed", type=float, default=1.0)
    parser.add_argument("--goal-delay", type=float, default=3.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rospy.init_node("pirl_navrl_ego_pybullet_bridge")
    node = EgoPybulletBridgeNode(args.output, args.duration, args.rate_hz, args.kp, args.max_speed, args.goal_delay)
    try:
        summary = node.run()
    finally:
        node.close()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
