"""Observation adapter for TASK_04 RL-ready gym-pybullet-drones envs."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from gymnasium import spaces

from pirl_navrl.scenarios.core import ObstacleConfig, ScenarioConfig

OBSERVATION_KEYS = (
    "position",
    "velocity",
    "goal",
    "relative_goal",
    "distance_to_goal",
    "nearest_obstacle_relative_position",
    "nearest_obstacle_distance",
    "min_clearance",
    "step_fraction",
)

FLAT_OBSERVATION_SIZE = 19


def _vec3(value) -> np.ndarray:
    array = np.asarray(value, dtype=np.float32).reshape(-1)
    if array.size < 3:
        padded = np.zeros(3, dtype=np.float32)
        padded[: array.size] = array
        return padded
    return array[:3].astype(np.float32)


def extract_position_velocity(platform_observation: Any) -> tuple[np.ndarray, np.ndarray]:
    array = np.asarray(platform_observation, dtype=np.float32)
    if array.ndim >= 2:
        state = array.reshape(array.shape[0], -1)[0]
    else:
        state = array.reshape(-1)
    position = _vec3(state[0:3])
    if state.size >= 13:
        velocity = _vec3(state[10:13])
    elif state.size >= 9:
        velocity = _vec3(state[6:9])
    else:
        velocity = np.zeros(3, dtype=np.float32)
    return position, velocity


def obstacle_center(obstacle: ObstacleConfig, elapsed: float) -> np.ndarray:
    return np.asarray(obstacle.position_at(elapsed), dtype=np.float32)


def obstacle_surface_clearance(position: np.ndarray, obstacle: ObstacleConfig, elapsed: float) -> float:
    center = obstacle_center(obstacle, elapsed)
    if obstacle.kind == "cylinder":
        distance = float(np.linalg.norm(position[:2] - center[:2]))
    else:
        distance = float(np.linalg.norm(position - center))
    return distance - float(obstacle.radius)


def nearest_obstacle_features(
    position: np.ndarray,
    scenario: ScenarioConfig,
    elapsed: float,
) -> tuple[np.ndarray, float, float]:
    nearest_relative = np.zeros(3, dtype=np.float32)
    nearest_distance = math.inf
    min_clearance = math.inf
    for obstacle in scenario.all_obstacles():
        center = obstacle_center(obstacle, elapsed)
        relative = center - position
        center_distance = float(np.linalg.norm(relative))
        clearance = obstacle_surface_clearance(position, obstacle, elapsed)
        if clearance < min_clearance:
            min_clearance = clearance
            nearest_distance = center_distance
            nearest_relative = relative.astype(np.float32)
    if not math.isfinite(min_clearance):
        min_clearance = 1.0e6
        nearest_distance = 1.0e6
    return nearest_relative, float(nearest_distance), float(min_clearance)


def build_observation_dict(
    *,
    platform_observation: Any,
    scenario: ScenarioConfig,
    step_count: int,
    elapsed: float,
) -> dict[str, Any]:
    position, velocity = extract_position_velocity(platform_observation)
    goal = np.asarray(scenario.goal, dtype=np.float32)
    relative_goal = goal - position
    distance_to_goal = float(np.linalg.norm(relative_goal))
    nearest_relative, nearest_distance, min_clearance = nearest_obstacle_features(position, scenario, elapsed)
    step_fraction = min(float(step_count) / float(max(1, scenario.max_steps)), 1.0)
    obs = {
        "position": position,
        "velocity": velocity,
        "goal": goal,
        "relative_goal": relative_goal.astype(np.float32),
        "distance_to_goal": distance_to_goal,
        "nearest_obstacle_relative_position": nearest_relative,
        "nearest_obstacle_distance": nearest_distance,
        "min_clearance": min_clearance,
        "step_fraction": step_fraction,
    }
    flat = flatten_observation(obs)
    if not np.all(np.isfinite(flat)):
        raise ValueError("TASK_04 observation contains non-finite values")
    return obs


def flatten_observation(obs_dict: dict[str, Any]) -> np.ndarray:
    values = np.concatenate(
        [
            _vec3(obs_dict["position"]),
            _vec3(obs_dict["velocity"]),
            _vec3(obs_dict["goal"]),
            _vec3(obs_dict["relative_goal"]),
            np.asarray([obs_dict["distance_to_goal"]], dtype=np.float32),
            _vec3(obs_dict["nearest_obstacle_relative_position"]),
            np.asarray(
                [
                    obs_dict["nearest_obstacle_distance"],
                    obs_dict["min_clearance"],
                    obs_dict["step_fraction"],
                ],
                dtype=np.float32,
            ),
        ]
    ).astype(np.float32)
    flat_size = values.shape[0]
    if flat_size != FLAT_OBSERVATION_SIZE:
        raise ValueError(f"unexpected flattened observation size {flat_size}")
    return values


def observation_space_for_scenario(scenario: ScenarioConfig) -> spaces.Box:
    del scenario
    high = np.full((FLAT_OBSERVATION_SIZE,), 1.0e6, dtype=np.float32)
    low = -high
    low[-1] = 0.0
    high[-1] = 1.0
    return spaces.Box(low=low, high=high, dtype=np.float32)
