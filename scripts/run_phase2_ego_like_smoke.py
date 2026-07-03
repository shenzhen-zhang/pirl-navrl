#!/usr/bin/env python3
"""Run TASK_02 EGO-like static obstacle bridge smoke test."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from pirl_navrl.bridges.ego_planner_bridge.ego_to_pybullet import (
    desired_velocity_to_normalized_action,
    trajectory_to_desired_velocity,
)
from pirl_navrl.bridges.ego_planner_bridge.pybullet_to_ego import (
    goal_to_ego_target,
    obstacles_to_synthetic_pointcloud,
    pybullet_state_to_ego_odometry,
)
from pirl_navrl.evaluation.diagnostic_logger import DiagnosticJsonlWriter
from pirl_navrl.scenarios.ego_like_static_v0 import (
    EgoLikeStaticScenario,
    ObstaclePrimitive,
    make_ego_like_static_v0,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT_DIR / "configs" / "phase2_ego_like_smoke.json"


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    output_path = ROOT_DIR / config["output_path"]
    scenario = make_ego_like_static_v0(seed=int(config["seed"]))
    bridge_status, bridge_blocker = detect_bridge_status()
    ego_commit = get_git_commit(ROOT_DIR / "external" / "ego-planner")

    pybullet_client = start_pybullet_scene(scenario)
    try:
        summary = run_smoke(
            scenario=scenario,
            config=config,
            output_path=output_path,
            ego_commit=ego_commit,
            bridge_status=bridge_status,
            bridge_blocker=bridge_blocker,
            pybullet_client=pybullet_client,
        )
    finally:
        if pybullet_client is not None:
            import pybullet as p

            p.disconnect(pybullet_client)

    print(json.dumps(summary, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def detect_bridge_status() -> tuple[str, str | None]:
    missing = [tool for tool in ("roscore", "catkin_make") if shutil.which(tool) is None]
    if missing:
        return (
            "mock_ros_unavailable",
            "missing ROS/catkin executables: " + ", ".join(missing),
        )
    return ("ros_sidecar_available_not_launched", None)


def get_git_commit(path: Path) -> str:
    if not (path / ".git").exists():
        return "missing"
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        return "unknown"


def start_pybullet_scene(scenario: EgoLikeStaticScenario) -> int | None:
    try:
        import pybullet as p
    except ImportError:
        return None

    client = p.connect(p.DIRECT)
    p.setGravity(0, 0, -9.81, physicsClientId=client)
    p.createCollisionShape(p.GEOM_PLANE, physicsClientId=client)
    p.createMultiBody(baseMass=0.0, baseCollisionShapeIndex=0, physicsClientId=client)
    for obstacle in scenario.obstacles:
        create_obstacle_body(p, client, obstacle)
    return client


def create_obstacle_body(pybullet: Any, client: int, obstacle: ObstaclePrimitive) -> None:
    if obstacle.kind == "cylinder":
        collision = pybullet.createCollisionShape(
            pybullet.GEOM_CYLINDER,
            radius=obstacle.radius,
            height=obstacle.height if obstacle.height is not None else 2.0,
            physicsClientId=client,
        )
        visual = pybullet.createVisualShape(
            pybullet.GEOM_CYLINDER,
            radius=obstacle.radius,
            length=obstacle.height if obstacle.height is not None else 2.0,
            rgbaColor=[0.7, 0.2, 0.2, 1.0],
            physicsClientId=client,
        )
    else:
        collision = pybullet.createCollisionShape(
            pybullet.GEOM_SPHERE,
            radius=obstacle.radius,
            physicsClientId=client,
        )
        visual = pybullet.createVisualShape(
            pybullet.GEOM_SPHERE,
            radius=obstacle.radius,
            rgbaColor=[0.2, 0.35, 0.8, 1.0],
            physicsClientId=client,
        )
    pybullet.createMultiBody(
        baseMass=0.0,
        baseCollisionShapeIndex=collision,
        baseVisualShapeIndex=visual,
        basePosition=list(obstacle.center),
        physicsClientId=client,
    )


def run_smoke(
    *,
    scenario: EgoLikeStaticScenario,
    config: dict[str, Any],
    output_path: Path,
    ego_commit: str,
    bridge_status: str,
    bridge_blocker: str | None,
    pybullet_client: int | None,
) -> dict[str, Any]:
    position = list(scenario.start)
    velocity = [0.0, 0.0, 0.0]
    pointcloud = obstacles_to_synthetic_pointcloud(
        scenario.bridge_obstacles(),
        resolution=float(config["pointcloud_resolution"]),
    )
    metadata = {
        "task_id": "TASK_02",
        "output_type": "diagnostic",
        "platform_id": "gym_pybullet_drones_pybullet",
        "external_planner": "ego_planner_official_sidecar",
        "ego_planner_commit": ego_commit,
        "scenario_id": scenario.scenario_id,
        "seed": scenario.seed,
        "bridge_status": bridge_status,
        "bridge_blocker": bridge_blocker,
        "planner_mode": "mock_ego_like",
        "pybullet_mode": "DIRECT" if pybullet_client is not None else "unavailable_kinematic",
    }

    min_clearance_seen = float("inf")
    with DiagnosticJsonlWriter(output_path, metadata) as writer:
        for step in range(int(config["horizon_steps"])):
            timestamp = step * float(config["dt"])
            odometry = pybullet_state_to_ego_odometry(
                position,
                velocity,
                timestamp=timestamp,
                frame_id="map",
                child_frame_id="base_link",
            )
            target = goal_to_ego_target(scenario.goal, timestamp=timestamp)
            trajectory = scenario.mock_ego_trajectory(position)
            desired_velocity = trajectory_to_desired_velocity(
                position,
                trajectory,
                kp=float(config["kp"]),
                max_speed=float(config["max_speed"]),
                lookahead_index=1,
            )
            normalized_action = desired_velocity_to_normalized_action(
                desired_velocity,
                max_speed=float(config["max_speed"]),
            )
            velocity = list(desired_velocity)
            position = list(
                scenario.bounds.clamp(
                    [
                        position[0] + velocity[0] * float(config["dt"]),
                        position[1] + velocity[1] * float(config["dt"]),
                        position[2] + velocity[2] * float(config["dt"]),
                    ]
                )
            )
            clearance = scenario.min_clearance(position)
            min_clearance_seen = min(min_clearance_seen, clearance)
            distance_to_goal = scenario.distance_to_goal(position)
            if pybullet_client is not None:
                import pybullet as p

                p.stepSimulation(physicsClientId=pybullet_client)

            writer.write(
                {
                    "step": step,
                    "position": position,
                    "velocity": velocity,
                    "goal": list(scenario.goal),
                    "desired_velocity": list(desired_velocity),
                    "normalized_action": list(normalized_action),
                    "min_clearance": clearance,
                    "distance_to_goal": distance_to_goal,
                    "odometry": odometry,
                    "goal_target": target,
                    "pointcloud_points": len(pointcloud["points"]),
                }
            )
            if distance_to_goal < 0.35:
                break

    return {
        "bridge_status": bridge_status,
        "ego_planner_commit": ego_commit,
        "final_distance_to_goal": scenario.distance_to_goal(position),
        "min_clearance": min_clearance_seen,
        "output_path": str(output_path),
        "records": step + 1,
    }


if __name__ == "__main__":
    main()
