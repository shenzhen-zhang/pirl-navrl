"""EGO-like static obstacle diagnostic scene for PyBullet smoke tests."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

Vector3 = tuple[float, float, float]


@dataclass(frozen=True)
class ScenarioBounds:
    x: tuple[float, float] = (-5.0, 5.0)
    y: tuple[float, float] = (-5.0, 5.0)
    z: tuple[float, float] = (0.0, 3.0)

    def clamp(self, position: Sequence[float]) -> Vector3:
        return (
            min(max(float(position[0]), self.x[0]), self.x[1]),
            min(max(float(position[1]), self.y[0]), self.y[1]),
            min(max(float(position[2]), self.z[0]), self.z[1]),
        )


@dataclass(frozen=True)
class ObstaclePrimitive:
    kind: Literal["cylinder", "sphere"]
    center: Vector3
    radius: float
    height: float | None = None

    def to_bridge_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "center": list(self.center),
            "radius": self.radius,
            "height": self.height,
        }


@dataclass(frozen=True)
class EgoLikeStaticScenario:
    scenario_id: str
    seed: int
    bounds: ScenarioBounds
    start: Vector3
    goal: Vector3
    obstacles: tuple[ObstaclePrimitive, ...]
    max_episode_steps: int = 48
    dt: float = 0.2
    max_speed: float = 1.0

    @property
    def space_meters(self) -> tuple[float, float, float]:
        return (
            self.bounds.x[1] - self.bounds.x[0],
            self.bounds.y[1] - self.bounds.y[0],
            self.bounds.z[1] - self.bounds.z[0],
        )

    def bridge_obstacles(self) -> list[dict[str, object]]:
        return [obstacle.to_bridge_dict() for obstacle in self.obstacles]

    def distance_to_goal(self, position: Sequence[float]) -> float:
        return _distance(_as_vector3(position), self.goal)

    def min_clearance(self, position: Sequence[float]) -> float:
        point = _as_vector3(position)
        return min(_clearance_to_obstacle(point, obstacle) for obstacle in self.obstacles)

    def mock_ego_trajectory(self, position: Sequence[float], *, points: int = 4) -> list[Vector3]:
        """Return a short EGO-style waypoint sequence without running ROS."""

        current = _as_vector3(position)
        first_waypoint = self._next_mock_waypoint(current)
        trajectory: list[Vector3] = []
        for index in range(1, points + 1):
            alpha = index / points
            waypoint = (
                current[0] + alpha * (first_waypoint[0] - current[0]),
                current[1] + alpha * (first_waypoint[1] - current[1]),
                current[2] + alpha * (first_waypoint[2] - current[2]),
            )
            trajectory.append(self.bounds.clamp(waypoint))
        return trajectory

    def _next_mock_waypoint(self, current: Vector3) -> Vector3:
        blocker = _nearest_corridor_blocker(current, self.goal, self.obstacles)
        if blocker is None:
            return self.goal

        lateral_sign = 1.0 if blocker.center[1] <= current[1] else -1.0
        lateral_offset = lateral_sign * (blocker.radius + 1.25)
        waypoint = (blocker.center[0] + 0.6, blocker.center[1] + lateral_offset, self.goal[2])
        return self.bounds.clamp(waypoint)


def make_ego_like_static_v0(seed: int = 0) -> EgoLikeStaticScenario:
    """Create the fixed first diagnostic scene requested by TASK_02."""

    return EgoLikeStaticScenario(
        scenario_id="ego_like_static_v0",
        seed=seed,
        bounds=ScenarioBounds(),
        start=(-4.0, 0.0, 1.0),
        goal=(4.0, 0.0, 1.0),
        obstacles=(
            ObstaclePrimitive("cylinder", (-1.7, -0.25, 1.0), 0.45, 2.0),
            ObstaclePrimitive("cylinder", (0.25, 0.35, 1.0), 0.55, 2.0),
            ObstaclePrimitive("sphere", (1.85, -0.45, 1.15), 0.45, None),
        ),
        max_episode_steps=48,
        dt=0.2,
        max_speed=1.0,
    )


def _as_vector3(value: Sequence[float]) -> Vector3:
    if len(value) != 3:
        raise ValueError("expected exactly 3 values")
    return (float(value[0]), float(value[1]), float(value[2]))


def _distance(a: Vector3, b: Vector3) -> float:
    return math.sqrt(sum((left - right) ** 2 for left, right in zip(a, b)))


def _clearance_to_obstacle(point: Vector3, obstacle: ObstaclePrimitive) -> float:
    if obstacle.kind == "sphere":
        return _distance(point, obstacle.center) - obstacle.radius

    height = obstacle.height if obstacle.height is not None else 2.0
    half_height = height / 2.0
    horizontal = math.hypot(point[0] - obstacle.center[0], point[1] - obstacle.center[1]) - obstacle.radius
    vertical_excess = max(abs(point[2] - obstacle.center[2]) - half_height, 0.0)
    if vertical_excess == 0:
        return horizontal
    return math.hypot(max(horizontal, 0.0), vertical_excess)


def _nearest_corridor_blocker(
    current: Vector3,
    goal: Vector3,
    obstacles: Sequence[ObstaclePrimitive],
) -> ObstaclePrimitive | None:
    line_x = goal[0] - current[0]
    line_y = goal[1] - current[1]
    line_length_sq = line_x * line_x + line_y * line_y
    if line_length_sq == 0:
        return None

    nearest: tuple[float, ObstaclePrimitive] | None = None
    for obstacle in obstacles:
        center_x = obstacle.center[0] - current[0]
        center_y = obstacle.center[1] - current[1]
        projection = (center_x * line_x + center_y * line_y) / line_length_sq
        if projection <= 0.05 or projection >= 0.95:
            continue
        closest_x = current[0] + projection * line_x
        closest_y = current[1] + projection * line_y
        lateral_distance = math.hypot(obstacle.center[0] - closest_x, obstacle.center[1] - closest_y)
        if lateral_distance <= obstacle.radius + 0.8:
            distance_ahead = math.hypot(closest_x - current[0], closest_y - current[1])
            if nearest is None or distance_ahead < nearest[0]:
                nearest = (distance_ahead, obstacle)
    return None if nearest is None else nearest[1]
