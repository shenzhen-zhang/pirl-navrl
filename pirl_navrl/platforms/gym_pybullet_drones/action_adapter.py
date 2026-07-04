"""Action conversion helpers for TASK_04 gym-pybullet-drones integration."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ActionAdapterResult:
    raw_desired_velocity: tuple[float, float, float]
    clipped_desired_velocity: tuple[float, float, float]
    applied_action: tuple[float, float, float]
    velocity_aviary_action: tuple[float, float, float, float]


def _as_velocity3(value) -> np.ndarray:
    array = np.asarray(value, dtype=np.float32).reshape(-1)
    if array.shape != (3,):
        raise ValueError(f"expected desired velocity shape (3,), got {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError("desired velocity must be finite")
    return array


def _validate_max_speed(max_speed: float) -> None:
    if max_speed <= 0.0:
        raise ValueError("max_speed must be > 0")


def clip_desired_velocity(desired_velocity, max_speed: float) -> np.ndarray:
    _validate_max_speed(max_speed)
    velocity = _as_velocity3(desired_velocity)
    norm = float(np.linalg.norm(velocity))
    if norm <= max_speed or norm == 0.0:
        return velocity.astype(np.float32)
    return (velocity * (max_speed / norm)).astype(np.float32)


def normalize_desired_velocity(desired_velocity, max_speed: float) -> np.ndarray:
    clipped = clip_desired_velocity(desired_velocity, max_speed)
    return np.clip(clipped / float(max_speed), -1.0, 1.0).astype(np.float32)


def adapt_desired_velocity(
    desired_velocity,
    action_mode: str = "normalized_velocity",
    *,
    max_speed: float = 1.0,
) -> ActionAdapterResult:
    if action_mode != "normalized_velocity":
        raise ValueError("TASK_04 supports only action_mode='normalized_velocity'")
    raw = _as_velocity3(desired_velocity)
    clipped = clip_desired_velocity(raw, max_speed)
    applied = normalize_desired_velocity(clipped, max_speed)
    speed_fraction = min(float(np.linalg.norm(clipped)) / float(max_speed), 1.0)
    norm = float(np.linalg.norm(clipped))
    direction = np.zeros(3, dtype=np.float32) if norm == 0.0 else clipped / norm
    velocity_aviary = (
        float(direction[0]),
        float(direction[1]),
        float(direction[2]),
        float(speed_fraction),
    )
    return ActionAdapterResult(
        raw_desired_velocity=tuple(float(v) for v in raw),
        clipped_desired_velocity=tuple(float(v) for v in clipped),
        applied_action=tuple(float(v) for v in applied),
        velocity_aviary_action=velocity_aviary,
    )


def desired_velocity_to_action(
    desired_velocity,
    action_mode: str = "normalized_velocity",
    *,
    max_speed: float = 1.0,
) -> np.ndarray:
    return np.asarray(
        adapt_desired_velocity(
            desired_velocity,
            action_mode,
            max_speed=max_speed,
        ).applied_action,
        dtype=np.float32,
    )
