# EGO-Planner Bridge I/O Contract

This contract is for TASK_02 diagnostics only. It keeps the official
EGO-Planner process outside the PIRL-NavRL Python package and describes the
minimum sidecar messages needed for a later ROS bridge.

## Frames And Timing

- World frame: `map`
- Drone body frame: `base_link`
- Units: meters, seconds, radians
- Quaternion convention: `[x, y, z, w]`
- Time source: PyBullet simulation time for smoke tests; ROS time for a real
  sidecar run.

## State Bridge

Direction: PyBullet drone state -> ROS odometry-shaped payload.

Required fields:

```json
{
  "frame_id": "map",
  "child_frame_id": "base_link",
  "timestamp": 0.0,
  "position": [-4.0, 0.0, 1.0],
  "velocity": [0.0, 0.0, 0.0],
  "orientation": [0.0, 0.0, 0.0, 1.0]
}
```

Target ROS shape for official sidecar work: `nav_msgs/Odometry`.

## Obstacle Bridge

Direction: PyBullet obstacle primitives -> synthetic pointcloud.

The first version samples only static `cylinder` and `sphere` primitives:

```json
{
  "frame_id": "map",
  "timestamp": 0.0,
  "points": [[-1.25, 0.0, 0.0], [-1.25, 0.0, 0.5]]
}
```

Target ROS shape for official sidecar work: `sensor_msgs/PointCloud2`.
Depth-image emulation is deliberately out of scope for TASK_02.

## Goal Bridge

Direction: PyBullet goal -> EGO planning target.

The first version supports one target point:

```json
{
  "frame_id": "map",
  "timestamp": 0.0,
  "position": [4.0, 0.0, 1.0]
}
```

Target ROS shape is expected to be a simple position goal command. Exact topic
mapping must be verified against the selected EGO launch file with `rqt_graph`
and `rosnode info`.

## Command Bridge

Direction: EGO trajectory or position command -> desired velocity -> PyBullet
action-like diagnostic vector.

First tracker:

```text
desired_velocity = kp * (next_waypoint - current_position)
desired_velocity = clip(desired_velocity, max_speed)
```

The Python smoke test logs both `desired_velocity` and a normalized
`[-1, 1]` action-like vector. A later gym-pybullet-drones integration should
map this into the selected environment's velocity or RPM action space.

## TASK_02 Local Status

The local smoke path uses mock EGO-like waypoints when ROS or catkin are not
available. The JSONL field `bridge_status` distinguishes:

- `mock_ros_unavailable`: ROS/catkin executables are missing; mock bridge used.
- `ros_sidecar_available_not_launched`: ROS/catkin appear installed, but the
  official sidecar was not launched by the smoke script.
