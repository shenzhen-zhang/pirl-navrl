#!/usr/bin/env python3
"""Run a TASK_04 diagnostic rollout on real gym-pybullet-drones."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pirl_navrl.evaluation.rollout_recorder import (  # noqa: E402
    RolloutInitialStateRecord,
    RolloutJsonlWriter,
    RolloutStepRecord,
    RolloutSummary,
)
from pirl_navrl.platforms.gym_pybullet_drones.rl_env import Task04GymPybulletDronesRLEnv  # noqa: E402
from pirl_navrl.policies.simple_policies import GoalSeekingVelocityPolicy  # noqa: E402
from pirl_navrl.scenarios.core import make_scenario  # noqa: E402


DEFAULT_CONFIG_PATH = ROOT_DIR / "configs/task04_gym_pybullet_static_nav_debug.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--gui", action="store_true")
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_initial(writer: RolloutJsonlWriter, env: Task04GymPybulletDronesRLEnv, info: dict[str, Any]) -> None:
    writer.write_initial_state(
        RolloutInitialStateRecord(
            task_id="TASK_04",
            output_type="diagnostic",
            platform_id=info["platform_id"],
            scenario_id=info["scenario_id"],
            seed=int(info["seed"]),
            policy_id="goal_seeking_velocity_debug",
            step=0,
            position=tuple(info["position"]),
            velocity=tuple(info["velocity"]),
            goal=env.scenario.goal,
            distance_to_goal=float(info["distance_to_goal"]),
            min_clearance=float(info["min_clearance"]),
            collision=bool(info["collision"]),
            success=bool(info["success"]),
            timeout=bool(info["timeout"]),
        )
    )


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    if args.output is not None:
        config["output_path"] = str(args.output)
    if args.gui:
        config["visualize"] = True

    scenario = make_scenario(config["scenario_id"], seed=int(config["seed"]))
    output_path = Path(config["output_path"])
    if not output_path.is_absolute():
        output_path = ROOT_DIR / output_path

    env = Task04GymPybulletDronesRLEnv(
        scenario=scenario,
        max_speed=float(config["max_speed"]),
        gui=bool(config.get("visualize")),
    )
    policy = GoalSeekingVelocityPolicy(max_speed=float(config["max_speed"]))
    policy.reset(scenario)

    obs, info = env.reset(seed=scenario.seed)
    del obs
    min_clearance = float(info["min_clearance"])
    last_info = info
    metadata = {
        "task_id": "TASK_04",
        "output_type": "diagnostic",
        "platform_id": config["platform_id"],
        "scenario_id": scenario.scenario_id,
        "seed": scenario.seed,
        "policy_id": policy.policy_id,
        "scenario": scenario.to_dict(),
        "custom_obstacles_physical": True,
    }

    try:
        with RolloutJsonlWriter(output_path, metadata) as writer:
            write_initial(writer, env, info)
            for step_index in range(scenario.max_steps):
                observation = {
                    "position": last_info["position"],
                    "velocity": last_info["velocity"],
                    "goal": scenario.goal,
                }
                desired_velocity = policy.act(observation)
                normalized_action = [float(value) / float(config["max_speed"]) for value in desired_velocity]
                flattened_obs, reward, terminated, truncated, info = env.step(normalized_action)
                del flattened_obs, reward
                min_clearance = min(min_clearance, float(info["min_clearance"]))
                writer.write_step(
                    RolloutStepRecord(
                        task_id="TASK_04",
                        output_type="diagnostic",
                        platform_id=info["platform_id"],
                        scenario_id=info["scenario_id"],
                        seed=int(info["seed"]),
                        policy_id=policy.policy_id,
                        step=step_index + 1,
                        position=tuple(info["position"]),
                        velocity=tuple(info["velocity"]),
                        goal=scenario.goal,
                        action=tuple(info["applied_action"]),
                        distance_to_goal=float(info["distance_to_goal"]),
                        min_clearance=float(info["min_clearance"]),
                        collision=bool(info["collision"]),
                        success=bool(info["success"]),
                        timeout=bool(info["timeout"]),
                        safety_collision=bool(info["safety_collision"]),
                        physical_collision=bool(info["physical_collision"]),
                        custom_obstacles_physical=bool(info["custom_obstacles_physical"]),
                        obstacle_body_ids=dict(info["obstacle_body_ids"]),
                    )
                )
                last_info = info
                if terminated or truncated:
                    break

            summary = RolloutSummary(
                task_id="TASK_04",
                output_type="diagnostic",
                platform_id=config["platform_id"],
                scenario_id=scenario.scenario_id,
                seed=scenario.seed,
                policy_id=policy.policy_id,
                steps=int(last_info.get("step", step_index + 1)),
                final_distance_to_goal=float(last_info["distance_to_goal"]),
                min_clearance=float(min_clearance),
                collision=bool(last_info["collision"]),
                success=bool(last_info["success"]),
                timeout=bool(last_info["timeout"]),
            )
            writer.write_summary(summary)
    finally:
        env.close()

    print(json.dumps(summary.__dict__, indent=2, sort_keys=True))
    if config.get("visualize"):
        subprocess.run(
            [sys.executable, str(ROOT_DIR / "scripts/view_task03_rollout.py"), "--trace", str(output_path)],
            check=True,
        )


if __name__ == "__main__":
    main()
