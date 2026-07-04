#!/usr/bin/env python3
"""Check the TASK_04 RL-ready gym-pybullet-drones environment."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pirl_navrl.platforms.gym_pybullet_drones.rl_env import Task04GymPybulletDronesRLEnv  # noqa: E402


REQUIRED_INFO_KEYS = {
    "position",
    "velocity",
    "distance_to_goal",
    "min_clearance",
    "collision",
    "success",
    "timeout",
    "reward_terms",
    "platform_id",
    "scenario_id",
    "seed",
}


def main() -> None:
    try:
        env = Task04GymPybulletDronesRLEnv(gui=False)
        obs, info = env.reset(seed=0)
        assert env.observation_space.contains(obs), "reset observation outside observation_space"
        assert env.action_space.shape == (3,), "unexpected action_space shape"
        assert REQUIRED_INFO_KEYS.issubset(info), f"reset info missing keys: {REQUIRED_INFO_KEYS - set(info)}"
        obs_shape = obs.shape
        last_reward = 0.0
        for _ in range(5):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            assert obs.shape == obs_shape, "observation shape changed across steps"
            assert env.observation_space.contains(obs), "step observation outside observation_space"
            assert math.isfinite(float(reward)), "reward must be finite"
            assert isinstance(terminated, bool), "terminated must be bool"
            assert isinstance(truncated, bool), "truncated must be bool"
            assert REQUIRED_INFO_KEYS.issubset(info), f"step info missing keys: {REQUIRED_INFO_KEYS - set(info)}"
            assert np.all(np.isfinite(obs)), "observation must be finite"
            last_reward = float(reward)
            if terminated or truncated:
                break

        sb3_check_env = "not_available"
        try:
            from stable_baselines3.common.env_checker import check_env

            check_env(env, warn=True)
            sb3_check_env = "passed"
        except ImportError:
            sb3_check_env = "skipped_stable_baselines3_not_available"

        env.close()
        print(
            json.dumps(
                {
                    "task_id": "TASK_04",
                    "output_type": "diagnostic",
                    "status": "ok",
                    "platform_id": "gym_pybullet_drones_velocity_adapter_debug",
                    "observation_shape": list(obs_shape),
                    "action_shape": list(env.action_space.shape),
                    "last_reward": last_reward,
                    "sb3_check_env": sb3_check_env,
                },
                indent=2,
                sort_keys=True,
            )
        )
    except RuntimeError as exc:
        print(f"[error] TASK_04 gym-pybullet-drones integration unavailable: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
