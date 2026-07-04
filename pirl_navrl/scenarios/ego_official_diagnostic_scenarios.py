"""TASK_02 official EGO-Planner diagnostic scenario definitions."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Literal

Vector3 = tuple[float, float, float]
ObstacleKind = Literal["cylinder", "sphere", "pointcloud_cluster"]
MotionType = Literal["static", "linear", "sudden_linear"]


@dataclass(frozen=True)
class EgoDiagnosticObstacle:
    obstacle_id: str
    kind: ObstacleKind
    initial_position: Vector3
    radius: float
    height: float | None = None
    motion_type: MotionType = "static"
    velocity: Vector3 | None = None
    start_time: float | None = None

    def obstacle_mode(self) -> str:
        return self.motion_type


@dataclass(frozen=True)
class EgoOfficialDiagnosticScenario:
    scenario_id: str
    seed: int
    start: Vector3
    goal: Vector3
    duration: float
    obstacles: tuple[EgoDiagnosticObstacle, ...]
    notes: str

    @property
    def obstacle_mode(self) -> str:
        modes = {obstacle.motion_type for obstacle in self.obstacles}
        if modes == {"static"}:
            return "static"
        if "sudden_linear" in modes:
            return "sudden_linear"
        return "linear"

    def to_trace_metadata(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "start": list(self.start),
            "goal": list(self.goal),
            "duration": self.duration,
            "obstacle_mode": self.obstacle_mode,
            "obstacles": [asdict(obstacle) for obstacle in self.obstacles],
            "notes": self.notes,
        }


def make_ego_static_obstacle_v0(seed: int = 127) -> EgoOfficialDiagnosticScenario:
    """Static official-EGO diagnostic scene using the original mockamap loop."""

    return EgoOfficialDiagnosticScenario(
        scenario_id="ego_static_obstacle_v0",
        seed=seed,
        start=(-18.0, 0.0, 0.0),
        goal=(-8.0, 10.0, 1.0),
        duration=90.0,
        obstacles=(
            EgoDiagnosticObstacle(
                obstacle_id="official_mockamap_static_cloud",
                kind="pointcloud_cluster",
                initial_position=(0.0, 0.0, 1.0),
                radius=20.0,
                height=3.0,
                motion_type="static",
            ),
        ),
        notes=(
            "Official run_in_sim.launch supplies the static obstacle field via "
            "mockamap_node -> /map_generator/global_cloud and local sensing via "
            "pcl_render_node. The configured obstacle represents that official "
            "static pointcloud source, not a custom injected PyBullet obstacle."
        ),
    )


def make_ego_dynamic_obstacle_v0(seed: int = 127) -> EgoOfficialDiagnosticScenario:
    """Dynamic-obstacle diagnostic config and future injection hook."""

    return EgoOfficialDiagnosticScenario(
        scenario_id="ego_dynamic_obstacle_v0",
        seed=seed,
        start=(-18.0, 0.0, 0.0),
        goal=(-8.0, 10.0, 1.0),
        duration=90.0,
        obstacles=(
            EgoDiagnosticObstacle(
                obstacle_id="future_linear_crossing_cluster",
                kind="pointcloud_cluster",
                initial_position=(-13.0, 4.0, 1.0),
                radius=0.8,
                height=2.0,
                motion_type="linear",
                velocity=(0.0, -0.45, 0.0),
                start_time=0.0,
            ),
        ),
        notes=(
            "Current official run_in_sim.launch does not expose a custom dynamic "
            "obstacle injection path. TASK_02 records this scenario as a trace "
            "schema/config hook only; it must not be reported as verified dynamic "
            "avoidance until a ROS pointcloud updater or map-generator override is added."
        ),
    )


def make_ego_sudden_motion_obstacle_v0(seed: int = 127) -> EgoOfficialDiagnosticScenario:
    """Sudden-motion obstacle diagnostic config and future injection hook."""

    return EgoOfficialDiagnosticScenario(
        scenario_id="ego_sudden_motion_obstacle_v0",
        seed=seed,
        start=(-18.0, 0.0, 0.0),
        goal=(-8.0, 10.0, 1.0),
        duration=90.0,
        obstacles=(
            EgoDiagnosticObstacle(
                obstacle_id="future_sudden_crossing_cluster",
                kind="pointcloud_cluster",
                initial_position=(-12.0, 5.5, 1.0),
                radius=0.8,
                height=2.0,
                motion_type="sudden_linear",
                velocity=(0.0, -0.7, 0.0),
                start_time=12.0,
            ),
        ),
        notes=(
            "Current official run_in_sim.launch cannot directly inject a cluster "
            "that starts stationary and then moves. This scenario is retained as "
            "a diagnostic hook/TODO and must not be claimed as a successful sudden "
            "motion avoidance validation yet."
        ),
    )


SCENARIO_FACTORIES = {
    "ego_static_obstacle_v0": make_ego_static_obstacle_v0,
    "ego_dynamic_obstacle_v0": make_ego_dynamic_obstacle_v0,
    "ego_sudden_motion_obstacle_v0": make_ego_sudden_motion_obstacle_v0,
}


def make_ego_official_diagnostic_scenario(
    scenario_id: str,
    *,
    seed: int = 127,
) -> EgoOfficialDiagnosticScenario:
    try:
        return SCENARIO_FACTORIES[scenario_id](seed=seed)
    except KeyError as exc:
        options = ", ".join(sorted(SCENARIO_FACTORIES))
        raise ValueError(f"unknown TASK_02 scenario {scenario_id!r}; options: {options}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario_id", choices=sorted(SCENARIO_FACTORIES))
    parser.add_argument("--seed", type=int, default=127)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scenario = make_ego_official_diagnostic_scenario(args.scenario_id, seed=args.seed)
    print(json.dumps(scenario.to_trace_metadata(), sort_keys=True))


if __name__ == "__main__":
    main()
