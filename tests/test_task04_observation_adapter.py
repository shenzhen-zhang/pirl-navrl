import numpy as np

from pirl_navrl.platforms.gym_pybullet_drones.observation_adapter import (
    FLAT_OBSERVATION_SIZE,
    build_observation_dict,
    flatten_observation,
    observation_space_for_scenario,
)
from pirl_navrl.scenarios.core import make_task03_static_nav_v0


def test_task04_observation_adapter_fields_space_and_finiteness() -> None:
    scenario = make_task03_static_nav_v0(seed=0)
    platform_obs = np.zeros((1, 20), dtype=np.float32)
    platform_obs[0, 0:3] = scenario.start
    platform_obs[0, 10:13] = (0.1, 0.2, 0.3)

    obs = build_observation_dict(
        platform_observation=platform_obs,
        scenario=scenario,
        step_count=0,
        elapsed=0.0,
    )
    flat = flatten_observation(obs)
    space = observation_space_for_scenario(scenario)

    for field in [
        "position",
        "velocity",
        "goal",
        "relative_goal",
        "distance_to_goal",
        "nearest_obstacle_relative_position",
        "nearest_obstacle_distance",
        "min_clearance",
        "step_fraction",
    ]:
        assert field in obs
    assert flat.shape == (FLAT_OBSERVATION_SIZE,)
    assert np.all(np.isfinite(flat))
    assert space.contains(flat)
