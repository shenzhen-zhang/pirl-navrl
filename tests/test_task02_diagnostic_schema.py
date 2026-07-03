import json

from pirl_navrl.evaluation.diagnostic_logger import DiagnosticJsonlWriter


def test_diagnostic_jsonl_preserves_task02_required_fields(tmp_path) -> None:
    path = tmp_path / "task02.jsonl"
    metadata = {
        "task_id": "TASK_02",
        "output_type": "diagnostic",
        "platform_id": "gym_pybullet_drones_pybullet",
        "external_planner": "ego_planner_official_sidecar",
        "ego_planner_commit": "abc123",
        "scenario_id": "ego_like_static_v0",
        "seed": 0,
        "bridge_status": "mock_ros_unavailable",
    }

    with DiagnosticJsonlWriter(path, metadata) as writer:
        writer.write(
            {
                "step": 0,
                "position": [-4.0, 0.0, 1.0],
                "goal": [4.0, 0.0, 1.0],
                "desired_velocity": [1.0, 0.0, 0.0],
                "min_clearance": 1.0,
            }
        )

    record = json.loads(path.read_text(encoding="utf-8").strip())
    for field in [
        "task_id",
        "output_type",
        "platform_id",
        "external_planner",
        "ego_planner_commit",
        "scenario_id",
        "seed",
        "step",
        "position",
        "goal",
        "desired_velocity",
        "min_clearance",
        "bridge_status",
    ]:
        assert field in record
