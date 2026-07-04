import numpy as np
import pytest


def test_task04_rl_env_reset_step_contract() -> None:
    pytest.importorskip("gym_pybullet_drones")
    from pirl_navrl.platforms.gym_pybullet_drones.rl_env import Task04GymPybulletDronesRLEnv

    env = Task04GymPybulletDronesRLEnv(gui=False)
    try:
        obs, info = env.reset(seed=0)
        assert env.observation_space.contains(obs)
        assert env.action_space.shape == (3,)
        assert info["platform_id"] == "gym_pybullet_drones_velocity_adapter_debug"

        next_obs, reward, terminated, truncated, info = env.step(np.zeros(3, dtype=np.float32))

        assert env.observation_space.contains(next_obs)
        assert isinstance(float(reward), float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert terminated == bool(info["success"] or info["collision"])
        assert "reward_terms" in info
        assert info["scenario_id"] == "task03_static_nav_v0"
        assert info["custom_obstacles_physical"] is True
        assert info["obstacle_body_ids"]
        assert "physical_collision" in info
        assert "safety_collision" in info
    finally:
        env.close()


def test_task04_adapter_creates_pybullet_obstacle_bodies() -> None:
    pytest.importorskip("gym_pybullet_drones")
    from pirl_navrl.platforms.gym_pybullet_drones.simple_adapter import GymPybulletDronesSimpleAdapter
    from pirl_navrl.scenarios.core import make_task03_static_nav_v0

    scenario = make_task03_static_nav_v0(seed=0)
    adapter = GymPybulletDronesSimpleAdapter(gui=False)
    try:
        adapter.reset(scenario)

        assert len(adapter.obstacle_body_ids) == len(scenario.static_obstacles)
        assert adapter.pybullet_client is not None
        assert adapter.drone_body_id is not None
    finally:
        adapter.close()
