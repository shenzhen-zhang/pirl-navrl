"""Small adapter layer for gym-pybullet-drones observations and actions."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Number
from typing import Any, Iterable


def _shape_product(shape: Any) -> int:
    product = 1
    for dim in shape or ():
        product *= int(dim)
    return product


def _flatten(value: Any) -> list[float]:
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, dict):
        items: list[float] = []
        for key in sorted(value):
            items.extend(_flatten(value[key]))
        return items
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_flatten(item))
        return items
    if isinstance(value, Number):
        return [float(value)]
    return []


def _space_bound(space: Any, attr: str, fallback: float, size: int) -> list[float]:
    bound = getattr(space, attr, None)
    values = _flatten(bound)
    if not values:
        return [fallback] * size
    if len(values) == 1 and size > 1:
        return values * size
    return values[:size]


@dataclass(frozen=True)
class DroneObservation:
    """Compact state summary used by the diagnostic risk scorer."""

    vector: list[float]
    altitude_m: float
    planar_distance_m: float
    speed_mps: float


class GymPybulletDronesAdapter:
    """Convert gym-pybullet-drones data into simple PIRL-NavRL contracts.

    The adapter intentionally does not implement simulator dynamics. It only
    normalizes observations/actions around an existing gym-pybullet-drones env.
    """

    def __init__(self, action_space: Any | None = None, action_dim: int = 4) -> None:
        self.action_space = action_space
        shape = getattr(action_space, "shape", None)
        self.action_shape = tuple(int(dim) for dim in shape) if shape else None
        self.action_dim = _shape_product(self.action_shape) if self.action_shape else action_dim

    def observation_to_vector(self, observation: Any) -> list[float]:
        return _flatten(observation)

    def summarize_observation(self, observation: Any) -> DroneObservation:
        vector = self.observation_to_vector(observation)
        x = vector[0] if len(vector) > 0 else 0.0
        y = vector[1] if len(vector) > 1 else 0.0
        z = vector[2] if len(vector) > 2 else 0.0

        # gym-pybullet-drones KIN observations commonly put linear velocity at
        # indices 10:13. Fall back to zero if the active observation is smaller.
        vx = vector[10] if len(vector) > 10 else 0.0
        vy = vector[11] if len(vector) > 11 else 0.0
        vz = vector[12] if len(vector) > 12 else 0.0

        return DroneObservation(
            vector=vector,
            altitude_m=z,
            planar_distance_m=(x * x + y * y) ** 0.5,
            speed_mps=(vx * vx + vy * vy + vz * vz) ** 0.5,
        )

    def action_to_env(self, command: Iterable[float]) -> list[float]:
        values = _flatten(command)
        if len(values) < self.action_dim:
            values.extend([0.0] * (self.action_dim - len(values)))
        values = values[: self.action_dim]

        low = _space_bound(self.action_space, "low", -1.0, self.action_dim)
        high = _space_bound(self.action_space, "high", 1.0, self.action_dim)
        return [min(max(v, low[i]), high[i]) for i, v in enumerate(values)]

    def format_action_for_env(self, action: Iterable[float]) -> Any:
        values = self.action_to_env(action)
        if not self.action_shape:
            return values
        try:
            import numpy as np
        except Exception:
            return values
        return np.asarray(values, dtype=float).reshape(self.action_shape)
