import json
import subprocess
import sys

import pytest

from pirl_navrl.evaluation.rollout_recorder import (
    RolloutInitialStateRecord,
    RolloutJsonlWriter,
    RolloutStepRecord,
)


def make_initial_state_record() -> RolloutInitialStateRecord:
    return RolloutInitialStateRecord(
        task_id="TASK_03",
        output_type="diagnostic",
        platform_id="diagnostic_kinematic_env",
        scenario_id="task03_static_nav_v0",
        seed=0,
        policy_id="goal_seeking_velocity_debug",
        step=0,
        position=(-4.0, 0.0, 1.0),
        velocity=(0.0, 0.0, 0.0),
        goal=(4.0, 0.0, 1.0),
        distance_to_goal=8.0,
        min_clearance=2.75,
        collision=False,
        success=False,
        timeout=False,
    )


def make_step_record() -> RolloutStepRecord:
    return RolloutStepRecord(
        task_id="TASK_03",
        output_type="diagnostic",
        platform_id="diagnostic_kinematic_env",
        scenario_id="task03_static_nav_v0",
        seed=0,
        policy_id="goal_seeking_velocity_debug",
        step=1,
        position=(-3.9, 0.0, 1.0),
        velocity=(1.0, 0.0, 0.0),
        goal=(4.0, 0.0, 1.0),
        action=(1.0, 0.0, 0.0),
        distance_to_goal=7.9,
        min_clearance=1.0,
        collision=False,
        success=False,
        timeout=False,
    )


def test_task03_viewer_trace_schema_contains_required_fields(tmp_path) -> None:
    path = tmp_path / "trace.jsonl"
    metadata = {
        "platform_id": "diagnostic_kinematic_env",
        "scenario_id": "task03_static_nav_v0",
        "seed": 0,
        "policy_id": "goal_seeking_velocity_debug",
        "scenario": {
            "start": [-4.0, 0.0, 1.0],
            "goal": [4.0, 0.0, 1.0],
            "bounds": {"x": [-5.0, 5.0], "y": [-5.0, 5.0], "z": [0.0, 3.0]},
            "static_obstacles": [],
            "dynamic_obstacles": [],
        },
    }
    with RolloutJsonlWriter(path, metadata) as writer:
        writer.write_initial_state(make_initial_state_record())
        writer.write_step(make_step_record())

    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert records[0]["record_type"] == "metadata"
    assert records[0]["scenario"]["bounds"]["x"] == [-5.0, 5.0]
    assert records[1]["record_type"] == "initial_state"
    assert records[1]["step"] == 0
    assert records[2]["record_type"] == "step"
    assert "position" in records[2]
    assert "action" in records[2]
    assert "goal" in records[2]


def test_task03_viewer_direct_mode_does_not_require_gui(tmp_path) -> None:
    pytest.importorskip("pybullet")
    path = tmp_path / "trace.jsonl"
    metadata = {
        "platform_id": "diagnostic_kinematic_env",
        "scenario_id": "task03_static_nav_v0",
        "seed": 0,
        "policy_id": "goal_seeking_velocity_debug",
        "scenario": {
            "start": [-4.0, 0.0, 1.0],
            "goal": [4.0, 0.0, 1.0],
            "bounds": {"x": [-5.0, 5.0], "y": [-5.0, 5.0], "z": [0.0, 3.0]},
            "static_obstacles": [],
            "dynamic_obstacles": [],
        },
    }
    with RolloutJsonlWriter(path, metadata) as writer:
        writer.write_initial_state(make_initial_state_record())
        writer.write_step(make_step_record())

    subprocess.run(
        [sys.executable, "scripts/view_task03_rollout.py", "--trace", str(path), "--direct"],
        check=True,
    )

    assert not list(tmp_path.glob("*.mp4"))
    assert not list(tmp_path.glob("*.gif"))
