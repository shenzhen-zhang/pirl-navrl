"""Reward helpers for TASK_04 RL-ready diagnostic environments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class Task04RewardConfig:
    progress_weight: float = 1.0
    distance_weight: float = 0.03
    action_weight: float = 0.02
    clearance_weight: float = 0.1
    clearance_margin: float = 0.8
    collision_penalty: float = 10.0
    success_bonus: float = 10.0
    timeout_penalty: float = 2.0


def compute_task04_reward(
    previous_obs: dict[str, Any],
    current_obs: dict[str, Any],
    action,
    event_flags: dict[str, bool],
    config: Task04RewardConfig | None = None,
) -> tuple[float, dict[str, float]]:
    cfg = config or Task04RewardConfig()
    previous_distance = float(previous_obs["distance_to_goal"])
    current_distance = float(current_obs["distance_to_goal"])
    action_norm = float(np.linalg.norm(np.asarray(action, dtype=np.float32).reshape(-1)))
    min_clearance = float(current_obs["min_clearance"])

    progress = cfg.progress_weight * (previous_distance - current_distance)
    distance_penalty = -cfg.distance_weight * current_distance
    action_penalty = -cfg.action_weight * action_norm
    clearance_penalty = -cfg.clearance_weight * max(0.0, cfg.clearance_margin - min_clearance)
    collision_penalty = -cfg.collision_penalty if event_flags.get("collision") else 0.0
    success_bonus = cfg.success_bonus if event_flags.get("success") else 0.0
    timeout_penalty = -cfg.timeout_penalty if event_flags.get("timeout") else 0.0

    terms = {
        "progress_to_goal": progress,
        "distance_penalty": distance_penalty,
        "action_norm_penalty": action_penalty,
        "clearance_penalty": clearance_penalty,
        "collision_penalty": collision_penalty,
        "success_bonus": success_bonus,
        "timeout_penalty": timeout_penalty,
    }
    reward = float(sum(terms.values()))
    if not np.isfinite(reward):
        raise ValueError("TASK_04 reward must be finite")
    return reward, {key: float(value) for key, value in terms.items()}
