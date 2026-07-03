from pirl_navrl.bridges.ego_planner_bridge.ego_to_pybullet import (
    position_command_to_desired_velocity,
    trajectory_to_desired_velocity,
)
from pirl_navrl.bridges.ego_planner_bridge.pybullet_to_ego import (
    goal_to_ego_target,
    obstacles_to_synthetic_pointcloud,
    pybullet_state_to_ego_odometry,
)


def test_state_bridge_odometry_schema() -> None:
    odometry = pybullet_state_to_ego_odometry(
        position=[1.0, 2.0, 3.0],
        velocity=[0.1, 0.2, 0.3],
        orientation=[0.0, 0.0, 0.0, 1.0],
        timestamp=1.25,
    )

    assert odometry["frame_id"] == "map"
    assert odometry["child_frame_id"] == "base_link"
    assert odometry["timestamp"] == 1.25
    assert odometry["position"] == (1.0, 2.0, 3.0)
    assert odometry["velocity"] == (0.1, 0.2, 0.3)
    assert odometry["orientation"] == (0.0, 0.0, 0.0, 1.0)


def test_obstacle_bridge_generates_pointcloud() -> None:
    cloud = obstacles_to_synthetic_pointcloud(
        [
            {"kind": "cylinder", "center": [0.0, 0.0, 1.0], "radius": 0.5, "height": 2.0},
            {"kind": "sphere", "center": [1.0, 0.0, 1.0], "radius": 0.4},
        ],
        resolution=0.5,
    )

    assert cloud["frame_id"] == "map"
    assert len(cloud["points"]) > 20
    assert all(len(point) == 3 for point in cloud["points"])


def test_goal_bridge_schema() -> None:
    target = goal_to_ego_target([4.0, 0.0, 1.0], timestamp=2.0)

    assert target == {"frame_id": "map", "timestamp": 2.0, "position": (4.0, 0.0, 1.0)}


def test_command_bridge_clips_velocity() -> None:
    desired = position_command_to_desired_velocity(
        [0.0, 0.0, 0.0],
        [10.0, 0.0, 0.0],
        kp=1.0,
        max_speed=1.5,
    )

    assert desired == (1.5, 0.0, 0.0)


def test_empty_trajectory_returns_zero_velocity() -> None:
    assert trajectory_to_desired_velocity([0.0, 0.0, 0.0], []) == (0.0, 0.0, 0.0)
