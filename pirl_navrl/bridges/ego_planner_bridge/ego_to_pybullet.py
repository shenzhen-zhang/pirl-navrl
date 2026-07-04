"""Future command helpers for mapping EGO-style commands to PyBullet actions."""

from __future__ import annotations

import math
from collections.abc import Sequence

Vector3 = tuple[float, float, float]


def _as_vector3(value: Sequence[float], name: str) -> Vector3:
    if len(value) != 3:
        raise ValueError(f"{name} must contain exactly 3 values")
    return (float(value[0]), float(value[1]), float(value[2]))


def _clip_vector_norm(vector: Vector3, max_norm: float) -> Vector3:
    if max_norm <= 0:
        raise ValueError("max_norm must be positive")
    norm = math.sqrt(sum(component * component for component in vector))
    if norm <= max_norm or norm == 0:
        return vector
    scale = max_norm / norm
    return tuple(component * scale for component in vector)  # type: ignore[return-value]


def position_command_to_desired_velocity(
    current_position: Sequence[float],
    command_position: Sequence[float],
    *,
    kp: float = 1.0,
    max_speed: float = 1.0,
) -> Vector3:
    """Convert a position command into a clipped desired velocity."""

    if kp <= 0:
        raise ValueError("kp must be positive")
    current = _as_vector3(current_position, "current_position")
    command = _as_vector3(command_position, "command_position")
    raw_velocity = tuple(kp * (target - here) for here, target in zip(current, command))
    return _clip_vector_norm(raw_velocity, max_speed)


def trajectory_to_desired_velocity(
    current_position: Sequence[float],
    trajectory: Sequence[Sequence[float]],
    *,
    kp: float = 1.0,
    max_speed: float = 1.0,
    lookahead_index: int = 0,
) -> Vector3:
    """Track the selected waypoint from an EGO trajectory as desired velocity."""

    if not trajectory:
        return (0.0, 0.0, 0.0)
    if lookahead_index < 0:
        raise ValueError("lookahead_index must be non-negative")
    waypoint = trajectory[min(lookahead_index, len(trajectory) - 1)]
    return position_command_to_desired_velocity(
        current_position,
        waypoint,
        kp=kp,
        max_speed=max_speed,
    )


def desired_velocity_to_normalized_action(
    desired_velocity: Sequence[float],
    *,
    max_speed: float = 1.0,
) -> Vector3:
    """Represent desired velocity as a bounded action-like vector for diagnostics."""

    velocity = _as_vector3(desired_velocity, "desired_velocity")
    clipped = _clip_vector_norm(velocity, max_speed)
    return tuple(component / max_speed for component in clipped)  # type: ignore[return-value]
