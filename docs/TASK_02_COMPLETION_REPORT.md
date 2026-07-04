# TASK_02 完成报告

## 结论

TASK_02 当前统一为：EGO-Planner 官方 Docker/ROS sidecar diagnostic。

当前主路线只使用 Docker Noetic 中运行的官方 EGO-Planner
`ego_planner/run_in_sim.launch`。PyBullet 只作为我们侧的可视化和 trace
诊断辅助，不再使用 mock EGO-like waypoint planner 观察效果。

本阶段仍是 diagnostic，不是正式 baseline，不进入论文结果。

## 主运行入口

```bash
bash scripts/run_official_ego_diagnostic_scene.sh --scenario ego_static_obstacle_v0
bash scripts/run_official_ego_diagnostic_scene.sh --scenario ego_dynamic_obstacle_v0
bash scripts/run_official_ego_diagnostic_scene.sh --scenario ego_sudden_motion_obstacle_v0
```

兼容入口：

```bash
bash scripts/run_official_ego_pybullet_mirror.sh
```

兼容入口等价于运行 `ego_static_obstacle_v0`。

## 保留的 official EGO 路线

- `scripts/run_ego_planner_noetic_docker.sh`
- `scripts/run_official_ego_diagnostic_scene.sh`
- `scripts/run_official_ego_pybullet_mirror.sh`
- `scripts/mirror_official_ego_ros_trace.py`
- `scripts/view_official_ego_pybullet_mirror.py`

Docker image: `osrf/ros:noetic-desktop-full`

已验证：

- `catkin_make -DCMAKE_BUILD_TYPE=Release` 通过。
- `roslaunch ego_planner run_in_sim.launch` 可启动官方节点。
- `/move_base_simple/goal` 发布后可收到 `/planning/pos_cmd`。
- PyBullet mirror 可显示 official odom、command、global cloud voxel map。

## 场景 suite

场景定义：

```text
pirl_navrl/scenarios/ego_official_diagnostic_scenarios.py
```

包含：

- `ego_static_obstacle_v0`
  - 目标：观察官方 EGO 在 upstream `mockamap_node` 静态点云中的行为。
  - 当前可运行并记录 official EGO trace。
- `ego_dynamic_obstacle_v0`
  - 目标：为连续运动障碍物记录 config 和 trace hook。
  - 当前官方 `run_in_sim.launch` 未接入动态点云注入，不声称已验证动态避障。
- `ego_sudden_motion_obstacle_v0`
  - 目标：为“先静止、后突然横向运动”障碍物记录 config 和 trace hook。
  - 当前官方 `run_in_sim.launch` 未接入突然运动点云注入，不声称已验证。

## Trace Schema

输出位置：

```text
results/official_ego_diagnostic/<scenario_id>/trace.jsonl
results/official_ego_diagnostic/<scenario_id>/official_ego_ros.log
```

JSONL 是 official EGO diagnostic trace schema，不是统一 baseline metrics。

每条记录包含或继承：

- `task_id: TASK_02`
- `output_type: diagnostic`
- `route: official_ego_docker_sidecar`
- `source_launch: ego_planner/run_in_sim.launch`
- `scenario_id`
- `obstacle_mode`
- `goal`
- `record_type`
- `timestamp`
- `elapsed` where applicable
- `odom_position` where available
- `ego_command_position` where available
- `distance_to_goal` where available

## 删除/降级的历史内容

以下内容不再作为 TASK_02 当前主路线：

- early EGO-like waypoint experiment
- early smoke-test script
- old EGO-like static scene module
- early interface experiment 的 `final_distance_to_goal` / `min_clearance` 效果报告
- synthetic waypoint 参数调优

历史原因：它们只能说明早期接口形状和 schema 能跑，不能代表官方
EGO-Planner 行为。当前 TASK_02 只围绕 official Docker/ROS sidecar。

## 当前限制

- PyBullet mirror 是 official EGO ROS loop 的可视化/诊断镜像，不是控制后端。
- 动态和突然运动障碍物目前是 scenario config / trace hook，尚未注入 official EGO。
- 若后续要观察真正动态障碍反应，需要新增 ROS pointcloud updater 或替换/扩展
  upstream map generator，但仍归入 TASK_02，不新建 TASK_03。

## 验证命令

```bash
python3 -m pytest -q
python3 -m py_compile scripts/mirror_official_ego_ros_trace.py scripts/view_official_ego_pybullet_mirror.py
```

本报告对应的代码仍保持 diagnostic 性质。
