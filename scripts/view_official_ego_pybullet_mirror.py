#!/usr/bin/env python3
"""Host-side PyBullet mirror for the official EGO-Planner simulator loop."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pybullet as p
import pybullet_data


class OfficialEgoMirrorViewer:
    def __init__(
        self,
        trace_path: Path,
        *,
        direct: bool,
        idle_timeout: float,
        startup_timeout: float,
        show_text: bool,
        point_size: float,
    ) -> None:
        self.trace_path = trace_path
        self.direct = direct
        self.idle_timeout = idle_timeout
        self.startup_timeout = startup_timeout
        self.show_text = show_text
        self.point_size = point_size
        self.client = None
        self.drone = None
        self.goal_marker = None
        self.last_position = None
        self.last_command_position = None
        self.last_record_time = time.monotonic()
        self.scene_ready = False
        self.state_count = 0

    def run(self) -> None:
        self.trace_path.parent.mkdir(parents=True, exist_ok=True)
        self.client = p.connect(p.DIRECT if self.direct else p.GUI)
        self.configure_scene()

        offset = 0
        start_wait = time.monotonic()
        saw_record = False
        while True:
            if self.trace_path.exists():
                with self.trace_path.open("r", encoding="utf-8") as handle:
                    handle.seek(offset)
                    lines = handle.readlines()
                    offset = handle.tell()
                for line in lines:
                    if not line.strip():
                        continue
                    self.update(json.loads(line))
                    saw_record = True
                    self.last_record_time = time.monotonic()
            p.stepSimulation(physicsClientId=self.client)
            if not saw_record and time.monotonic() - start_wait > self.startup_timeout:
                raise TimeoutError(f"no records appeared in {self.trace_path} within {self.startup_timeout}s")
            if self.scene_ready and time.monotonic() - self.last_record_time > self.idle_timeout:
                break
            time.sleep(1.0 / 40.0)

    def close(self) -> None:
        if self.client is not None:
            p.disconnect(self.client)

    def configure_scene(self) -> None:
        p.setAdditionalSearchPath(pybullet_data.getDataPath(), physicsClientId=self.client)
        p.resetSimulation(physicsClientId=self.client)
        p.setGravity(0, 0, -9.81, physicsClientId=self.client)
        if not self.direct:
            p.configureDebugVisualizer(p.COV_ENABLE_GUI, 1, physicsClientId=self.client)
            p.configureDebugVisualizer(p.COV_ENABLE_SHADOWS, 1, physicsClientId=self.client)
            p.configureDebugVisualizer(p.COV_ENABLE_RGB_BUFFER_PREVIEW, 0, physicsClientId=self.client)
            p.configureDebugVisualizer(p.COV_ENABLE_DEPTH_BUFFER_PREVIEW, 0, physicsClientId=self.client)
            p.configureDebugVisualizer(p.COV_ENABLE_SEGMENTATION_MARK_PREVIEW, 0, physicsClientId=self.client)
            p.resetDebugVisualizerCamera(
                cameraDistance=24.0,
                cameraYaw=-48,
                cameraPitch=-58,
                cameraTargetPosition=[-12.5, 4.0, 1.0],
                physicsClientId=self.client,
            )
        p.loadURDF("plane.urdf", physicsClientId=self.client)
        self.create_axes()

    def update(self, record: dict) -> None:
        record_type = record.get("record_type", "state")
        if record_type == "metadata":
            self.create_goal_marker(record.get("goal"))
            return
        if record_type == "map":
            self.create_map(record["points"])
            self.scene_ready = True
            return
        if record_type != "state":
            return

        position = record.get("odom_position")
        if position is None:
            return
        if self.drone is None:
            self.drone = self.create_sphere(position, 0.28, [1.0, 0.78, 0.02, 1.0])
        else:
            p.resetBasePositionAndOrientation(self.drone, position, [0, 0, 0, 1], physicsClientId=self.client)
        if self.last_position is not None:
            p.addUserDebugLine(
                self.last_position,
                position,
                lineColorRGB=[1.0, 0.82, 0.05],
                lineWidth=3.0,
                lifeTime=0,
                physicsClientId=self.client,
            )
        self.last_position = position

        command_position = record.get("ego_command_position")
        if command_position is not None:
            if self.last_command_position is not None:
                p.addUserDebugLine(
                    self.last_command_position,
                    command_position,
                    lineColorRGB=[0.1, 0.9, 0.25],
                    lineWidth=2.0,
                    lifeTime=0,
                    physicsClientId=self.client,
                )
            self.last_command_position = command_position

        self.state_count += 1
        if self.show_text and self.state_count % 25 == 0:
            distance_to_goal = record.get("distance_to_goal")
            distance_text = "nan" if distance_to_goal is None else f"{distance_to_goal:.2f}"
            p.addUserDebugText(
                f"official EGO  dist={distance_text}  cmd={record.get('command_received')}",
                [-21.0, -10.0, 3.2],
                textColorRGB=[1.0, 1.0, 1.0],
                textSize=1.2,
                lifeTime=1.0,
                physicsClientId=self.client,
            )

    def create_map(self, points: list[list[float]]) -> None:
        if not points:
            return
        colors = [[0.72, 0.18, 0.12] for _ in points]
        p.addUserDebugPoints(
            points,
            colors,
            pointSize=self.point_size,
            lifeTime=0,
            physicsClientId=self.client,
        )

    def create_goal_marker(self, goal: list[float] | None) -> None:
        if goal is None or self.goal_marker is not None:
            return
        self.goal_marker = self.create_sphere(goal, 0.42, [0.05, 0.85, 0.25, 1.0])

    def create_axes(self) -> None:
        p.addUserDebugLine([-22, 0, 0.03], [2, 0, 0.03], [0.7, 0.7, 0.7], 1.0, physicsClientId=self.client)
        p.addUserDebugLine([-18, -12, 0.03], [-18, 14, 0.03], [0.7, 0.7, 0.7], 1.0, physicsClientId=self.client)

    def create_sphere(self, position: list[float], radius: float, color: list[float]) -> int:
        collision = p.createCollisionShape(p.GEOM_SPHERE, radius=radius, physicsClientId=self.client)
        visual = p.createVisualShape(p.GEOM_SPHERE, radius=radius, rgbaColor=color, physicsClientId=self.client)
        return p.createMultiBody(
            baseMass=0.0,
            baseCollisionShapeIndex=collision,
            baseVisualShapeIndex=visual,
            basePosition=position,
            physicsClientId=self.client,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--direct", action="store_true")
    parser.add_argument("--idle-timeout", type=float, default=10.0)
    parser.add_argument("--startup-timeout", type=float, default=90.0)
    parser.add_argument("--show-text", action="store_true")
    parser.add_argument("--point-size", type=float, default=2.2)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    viewer = OfficialEgoMirrorViewer(
        args.trace,
        direct=args.direct,
        idle_timeout=args.idle_timeout,
        startup_timeout=args.startup_timeout,
        show_text=args.show_text,
        point_size=args.point_size,
    )
    try:
        viewer.run()
    finally:
        viewer.close()


if __name__ == "__main__":
    main()
