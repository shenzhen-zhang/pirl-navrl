import math

from pirl_navrl.evaluation.reward import compute_task04_reward


def obs(distance: float, clearance: float = 1.0) -> dict:
    return {"distance_to_goal": distance, "min_clearance": clearance}


def test_task04_reward_progress_direction() -> None:
    reward, terms = compute_task04_reward(
        obs(5.0),
        obs(4.0),
        (0.2, 0.0, 0.0),
        {"collision": False, "success": False, "timeout": False},
    )

    assert terms["progress_to_goal"] > 0.0
    assert math.isfinite(reward)


def test_task04_reward_collision_penalty_and_success_bonus() -> None:
    collision_reward, collision_terms = compute_task04_reward(
        obs(2.0),
        obs(2.0, clearance=0.0),
        (0.0, 0.0, 0.0),
        {"collision": True, "success": False, "timeout": False},
    )
    success_reward, success_terms = compute_task04_reward(
        obs(0.4),
        obs(0.1),
        (0.0, 0.0, 0.0),
        {"collision": False, "success": True, "timeout": False},
    )

    assert collision_terms["collision_penalty"] < 0.0
    assert success_terms["success_bonus"] > 0.0
    assert success_reward > collision_reward
