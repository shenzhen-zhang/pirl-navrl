import json
from pathlib import Path


def test_phase1_config_schema() -> None:
    config = json.loads(Path("configs/phase1_simple_demo.json").read_text(encoding="utf-8"))

    assert config["task_id"] == "TASK_01"
    assert config["platform_id"] == "gym-pybullet-drones"
    assert config["result_kind"] == "diagnostic"
    assert config["demo"]["steps"] > 0
    assert config["demo"]["output_path"].endswith(".jsonl")

    risk = config["risk"]
    assert 0.0 < risk["threshold"] < 1.0
    assert risk["min_altitude_m"] > 0.0
    assert risk["max_speed_mps"] > 0.0
    assert risk["max_abs_action"] > 0.0
    assert abs((risk["action_weight"] + risk["state_weight"]) - 1.0) < 1e-9
