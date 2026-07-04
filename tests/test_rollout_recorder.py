import json

import pytest

from pirl_navrl.evaluation.rollout_recorder import (
    RolloutInitialStateRecord,
    RolloutJsonlWriter,
    RolloutStepRecord,
    RolloutSummary,
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
        safety_collision=False,
        physical_collision=False,
        custom_obstacles_physical=True,
        obstacle_body_ids={"obs": 3},
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


def test_rollout_jsonl_writer_writes_required_fields(tmp_path) -> None:
    path = tmp_path / "rollout.jsonl"
    metadata = {
        "platform_id": "diagnostic_kinematic_env",
        "scenario_id": "task03_static_nav_v0",
        "seed": 0,
        "policy_id": "goal_seeking_velocity_debug",
    }

    with RolloutJsonlWriter(path, metadata) as writer:
        writer.write_initial_state(make_initial_state_record())
        writer.write_step(make_step_record())

    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    initial = records[1]
    step = records[2]
    assert initial["record_type"] == "initial_state"
    assert initial["step"] == 0
    assert initial["position"] == [-4.0, 0.0, 1.0]
    assert initial["velocity"] == [0.0, 0.0, 0.0]
    for field in [
        "task_id",
        "output_type",
        "platform_id",
        "scenario_id",
        "seed",
        "policy_id",
        "step",
        "position",
        "velocity",
        "goal",
        "action",
        "distance_to_goal",
        "min_clearance",
        "collision",
        "success",
        "timeout",
    ]:
        assert field in step
    assert step["output_type"] == "diagnostic"


def test_rollout_summary_and_output_type_validation() -> None:
    summary = RolloutSummary(
        task_id="TASK_03",
        output_type="diagnostic",
        platform_id="diagnostic_kinematic_env",
        scenario_id="task03_static_nav_v0",
        seed=0,
        policy_id="goal_seeking_velocity_debug",
        steps=3,
        final_distance_to_goal=1.2,
        min_clearance=0.4,
        collision=False,
        success=False,
        timeout=True,
    )

    assert summary.record_type == "summary"
    with pytest.raises(ValueError):
        RolloutStepRecord(
            **{**make_step_record().__dict__, "output_type": "metric"}
        )
