# EGO-Planner Sidecar Bridge

This directory contains only PIRL-NavRL bridge contracts and Python diagnostic
adapters. It does not vendor or modify EGO-Planner C++ planner code.

## Official Repository

Local checkout:

```bash
external/ego-planner/
```

Clone command:

```bash
GIT_CLONE_FLAGS="--depth 1" bash scripts/setup_external_repos.sh --include-ego
```

Official repository: <https://github.com/ZJU-FAST-Lab/ego-planner>

Local TASK_02 checkout recorded during implementation:

```text
bfda51284c8c1b476043255a8145ef925a3778a5
```

License observed in the local checkout: GNU GPL v3.

## Official Build Route

The official README requires Ubuntu with ROS desktop, catkin, and Armadillo.
The upstream route is:

```bash
sudo apt-get install libarmadillo-dev
cd external/ego-planner
catkin_make -DCMAKE_BUILD_TYPE=Release
source devel/setup.bash
roslaunch ego_planner rviz.launch
roslaunch ego_planner run_in_sim.launch
```

TASK_02 does not run or modify official planner internals. The current active
route is the official EGO-Planner Docker/ROS sidecar diagnostic.

## Local Docker Route On Ubuntu 22.04

The current host is Ubuntu 22.04, while official EGO-Planner targets ROS1 Noetic
on Ubuntu 20.04. Use the provided Docker wrapper:

```bash
bash scripts/run_ego_planner_noetic_docker.sh build
bash scripts/run_ego_planner_noetic_docker.sh headless
bash scripts/run_ego_planner_noetic_docker.sh rviz
```

Observed local status:

- `catkin_make -DCMAKE_BUILD_TYPE=Release` passes in `osrf/ros:noetic-desktop-full`.
- `roslaunch ego_planner run_in_sim.launch` starts the official sidecar nodes.
- Publishing `/move_base_simple/goal` produces `/planning/pos_cmd`.
- `roslaunch ego_planner simple_run.launch` starts RViz through X11.

## Official EGO Diagnostic Scene Runner

Main TASK_02 route:

```bash
bash scripts/run_official_ego_diagnostic_scene.sh --scenario ego_static_obstacle_v0
bash scripts/run_official_ego_diagnostic_scene.sh --scenario ego_dynamic_obstacle_v0
bash scripts/run_official_ego_diagnostic_scene.sh --scenario ego_sudden_motion_obstacle_v0
```

This runs the official `ego_planner/run_in_sim.launch` unchanged in the Noetic
Docker container. That launch owns the original map generator, `pcl_render_node`
local sensing, EGO planner, `traj_server`, SO3 controller, and quadrotor
simulator. The host PyBullet window is only a live mirror of the official ROS
topics:

- red voxel columns: official `/map_generator/global_cloud`, downsampled into
  clear PyBullet obstacle blocks
- yellow sphere/line: official `/visual_slam/odom`
- green line: official `/planning/pos_cmd`
- green sphere: the published `/move_base_simple/goal`

The compatibility shortcut below runs the static scenario:

```bash
bash scripts/run_official_ego_pybullet_mirror.sh
```

Short local validation on this machine:

```json
{
  "command_received": true,
  "final_distance_to_goal": 0.2239981077623934,
  "final_position": [-8.099465204895884, 9.799844148774891, 0.9851858001733191],
  "goal": [-8.0, 10.0, 1.0],
  "map_received": true,
  "records": 720
}
```

This is the route to use when the question is whether the visualized behavior
matches the original repository. It mirrors original EGO simulator behavior
instead of replacing the original controller with a Python point-mass tracker.

The PyBullet mirror renders obstacle maps as regular voxel columns by default.
For debugging the raw pointcloud instead:

```bash
python3 scripts/view_official_ego_pybullet_mirror.py \
  --trace results/official_ego_diagnostic/ego_static_obstacle_v0/trace.jsonl \
  --map-style points
```

## Diagnostic Scene Suite

Scenario definitions live in
`pirl_navrl/scenarios/ego_official_diagnostic_scenarios.py`.

- `ego_static_obstacle_v0`: observes official EGO behavior in the upstream
  static `mockamap_node` pointcloud.
- `ego_dynamic_obstacle_v0`: records a continuous-motion obstacle config and
  future injection hook. Current official launch does not inject it.
- `ego_sudden_motion_obstacle_v0`: records a sudden-motion obstacle config and
  future injection hook. Current official launch does not inject it.

Do not claim dynamic or sudden-motion avoidance success until a ROS pointcloud
updater or map-generator override is connected to official EGO.

## Removed Simplified PyBullet Bridge

The earlier mock EGO-like route and simplified ROS/PyBullet bridge were removed
from the active TASK_02 route because they were useful only for early
interface/debug experiments and produced misleading planner-effect narratives:

- The original EGO loop is `map_generator/mockamap -> pcl_render_node ->
  EGO grid map/planner -> traj_server -> so3_control ->
  quadrotor_simulator_so3 -> /visual_slam/odom`.
- This simplified bridge was `synthetic pointcloud -> EGO planner ->
  /planning/pos_cmd -> Python point-mass tracker -> synthetic odom`.
- Therefore it bypasses the original local sensing, SO3 controller, and
  quadrotor dynamics, so it can verify topic connectivity but not original
  avoidance quality.

For original repository behavior, use only the official mirror or RViz route:

```bash
bash scripts/run_official_ego_pybullet_mirror.sh
bash scripts/run_ego_planner_noetic_docker.sh rviz
```
