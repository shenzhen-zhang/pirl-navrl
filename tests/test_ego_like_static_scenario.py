from pirl_navrl.scenarios.ego_like_static_v0 import make_ego_like_static_v0


def test_ego_like_static_v0_shape() -> None:
    scenario = make_ego_like_static_v0(seed=0)

    assert scenario.scenario_id == "ego_like_static_v0"
    assert scenario.space_meters == (10.0, 10.0, 3.0)
    assert scenario.start == (-4.0, 0.0, 1.0)
    assert scenario.goal == (4.0, 0.0, 1.0)
    assert len(scenario.obstacles) == 3


def test_min_clearance_detects_static_obstacle() -> None:
    scenario = make_ego_like_static_v0(seed=0)

    assert scenario.min_clearance(scenario.start) > 1.0
    assert scenario.min_clearance(scenario.obstacles[0].center) < 0.0


def test_mock_ego_trajectory_has_waypoints_inside_bounds() -> None:
    scenario = make_ego_like_static_v0(seed=0)
    trajectory = scenario.mock_ego_trajectory(scenario.start)

    assert len(trajectory) == 4
    for waypoint in trajectory:
        assert scenario.bounds.x[0] <= waypoint[0] <= scenario.bounds.x[1]
        assert scenario.bounds.y[0] <= waypoint[1] <= scenario.bounds.y[1]
        assert scenario.bounds.z[0] <= waypoint[2] <= scenario.bounds.z[1]
    assert trajectory[-1][1] != 0.0
