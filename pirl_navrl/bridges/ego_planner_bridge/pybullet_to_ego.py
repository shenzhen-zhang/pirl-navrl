"""State, obstacle, and goal bridge helpers for an EGO-Planner sidecar."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any, Literal

Vector3 = tuple[float, float, float]
Quaternion = tuple[float, float, float, float]


@dataclass(frozen=True)
class EgoOdometry:
    """ROS odometry-shaped payload without requiring ROS Python packages."""

    frame_id: str
    child_frame_id: str
    timestamp: float
    position: Vector3
    velocity: Vector3
    orientation: Quaternion


@dataclass(frozen=True)
class EgoPointCloud:
    """PointCloud2-shaped payload represented as JSON-friendly primitives."""

    frame_id: str
    timestamp: float
    points: list[Vector3]


@dataclass(frozen=True)
class EgoGoal:
    """Single-goal planning target for the EGO sidecar contract."""

    frame_id: str
    timestamp: float
    position: Vector3


@dataclass(frozen=True)
class BridgeObstacle:
    """Obstacle primitive accepted by the synthetic pointcloud bridge."""

    kind: Literal["cylinder", "sphere"]
    center: Vector3
    radius: float
    height: float | None = None


def _as_vector3(value: Sequence[float], name: str) -> Vector3:
    if len(value) != 3:
        raise ValueError(f"{name} must contain exactly 3 values")
    return (float(value[0]), float(value[1]), float(value[2]))


def _as_quaternion(value: Sequence[float], name: str) -> Quaternion:
    if len(value) != 4:
        raise ValueError(f"{name} must contain exactly 4 values")
    return (float(value[0]), float(value[1]), float(value[2]), float(value[3]))


def _obstacle_from_mapping(obstacle: Mapping[str, Any] | BridgeObstacle) -> BridgeObstacle:
    if isinstance(obstacle, BridgeObstacle):
        return obstacle
    kind = str(obstacle["kind"])
    if kind not in {"cylinder", "sphere"}:
        raise ValueError(f"unsupported obstacle kind: {kind}")
    height = obstacle.get("height")
    return BridgeObstacle(
        kind=kind,  # type: ignore[arg-type]
        center=_as_vector3(obstacle["center"], "obstacle.center"),
        radius=float(obstacle["radius"]),
        height=None if height is None else float(height),
    )


def pybullet_state_to_ego_odometry(
    position: Sequence[float],
    velocity: Sequence[float],
    orientation: Sequence[float] = (0.0, 0.0, 0.0, 1.0),
    *,
    timestamp: float = 0.0,
    frame_id: str = "map",
    child_frame_id: str = "base_link",
) -> dict[str, Any]:
    """Convert PyBullet state vectors into a ROS odometry-shaped dictionary."""

    odometry = EgoOdometry(
        frame_id=frame_id,
        child_frame_id=child_frame_id,
        timestamp=float(timestamp),
        position=_as_vector3(position, "position"),
        velocity=_as_vector3(velocity, "velocity"),
        orientation=_as_quaternion(orientation, "orientation"),
    )
    return asdict(odometry)


def goal_to_ego_target(
    goal: Sequence[float],
    *,
    timestamp: float = 0.0,
    frame_id: str = "map",
) -> dict[str, Any]:
    """Convert a PyBullet goal point into a single EGO planning target."""

    target = EgoGoal(
        frame_id=frame_id,
        timestamp=float(timestamp),
        position=_as_vector3(goal, "goal"),
    )
    return asdict(target)


def obstacles_to_synthetic_pointcloud(
    obstacles: Sequence[Mapping[str, Any] | BridgeObstacle],
    *,
    resolution: float = 0.4,
    timestamp: float = 0.0,
    frame_id: str = "map",
) -> dict[str, Any]:
    """Sample static obstacle primitives into a compact synthetic pointcloud."""

    if resolution <= 0:
        raise ValueError("resolution must be positive")

    points: list[Vector3] = []
    for raw_obstacle in obstacles:
        obstacle = _obstacle_from_mapping(raw_obstacle)
        if obstacle.radius <= 0:
            raise ValueError("obstacle radius must be positive")
        if obstacle.kind == "sphere":
            points.extend(_sample_sphere(obstacle.center, obstacle.radius, resolution))
        else:
            height = obstacle.height if obstacle.height is not None else 2.0
            if height <= 0:
                raise ValueError("cylinder height must be positive")
            points.extend(_sample_cylinder(obstacle.center, obstacle.radius, height, resolution))

    cloud = EgoPointCloud(frame_id=frame_id, timestamp=float(timestamp), points=points)
    return asdict(cloud)


def _sample_sphere(center: Vector3, radius: float, resolution: float) -> list[Vector3]:
    rings = max(4, int(math.ceil(math.pi * radius / resolution)))
    columns = max(8, int(math.ceil(2.0 * math.pi * radius / resolution)))
    points: list[Vector3] = []
    for ring in range(rings + 1):
        phi = math.pi * ring / rings
        z = center[2] + radius * math.cos(phi)
        radial = radius * math.sin(phi)
        for column in range(columns):
            theta = 2.0 * math.pi * column / columns
            points.append(
                (
                    center[0] + radial * math.cos(theta),
                    center[1] + radial * math.sin(theta),
                    z,
                )
            )
    return points


def _sample_cylinder(center: Vector3, radius: float, height: float, resolution: float) -> list[Vector3]:
    columns = max(8, int(math.ceil(2.0 * math.pi * radius / resolution)))
    layers = max(2, int(math.ceil(height / resolution)))
    bottom = center[2] - height / 2.0
    points: list[Vector3] = []
    for layer in range(layers + 1):
        z = bottom + height * layer / layers
        for column in range(columns):
            theta = 2.0 * math.pi * column / columns
            points.append(
                (
                    center[0] + radius * math.cos(theta),
                    center[1] + radius * math.sin(theta),
                    z,
                )
            )
    return points
