# TASK_02 完成报告

## 结论

TASK_02 当前统一为：EGO-Planner 官方 Docker/ROS sidecar diagnostic。

当前主路线在 Docker Noetic 中运行官方 EGO-Planner 节点，并使用
`ego_custom_map_sidecar.launch` 把我们自己构建的 PyBullet-style 场景点云
注入 `/grid_map/cloud`。PyBullet 只作为我们侧的可视化和 trace 诊断辅助，
不再使用 mock EGO-like waypoint planner 观察 planner 行为。

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
- `pirl_navrl/bridges/ego_planner_bridge/ego_custom_map_sidecar.launch`

Docker image: `osrf/ros:noetic-desktop-full`

已完成的诊断链路检查：

- `catkin_make -DCMAKE_BUILD_TYPE=Release` completed in the Noetic Docker
  environment.
- `ego_custom_map_sidecar.launch` 可启动官方 planner/controller/simulator 节点。
- `/move_base_simple/goal` 发布后可收到 `/planning/pos_cmd`。
- PyBullet mirror 可显示 official odom、command、目标点和自定义动态障碍物。

## 场景 suite

场景定义：

```text
pirl_navrl/scenarios/ego_official_diagnostic_scenarios.py
```

包含：

- `ego_static_obstacle_v0`
  - 目标：观察 official EGO 在我们自定义静态柱状障碍物附近的轨迹反应。
  - Behavior observation：短测 trace 中 odom 横向偏移约 `1.21 m`。
- `ego_dynamic_obstacle_v0`
  - 目标：观察 official EGO 对连续横向运动障碍物的反应。
  - Behavior observation：短测 trace 中移动障碍从 `y≈-1.99` 到 `y≈2.83`，
    odom 横向偏移约 `0.99 m`。
- `ego_sudden_motion_obstacle_v0`
  - 目标：观察 official EGO 对“先静止、后横向运动”障碍物的反应。
  - Behavior observation：短测 trace 中运动前障碍 y 固定为 `-1.7`，
    运动后到 `y≈5.09`，odom 横向偏移约 `1.26 m`。

这些横向偏移、最终距离、command/map 接收状态只作为 diagnostic behavior
observation，用于说明 trace 中观测到的现象；它们不是性能结论，不构成
success rate、collision-free rate 或正式 baseline metric。

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
- `source_launch: pirl_navrl/bridges/ego_planner_bridge/ego_custom_map_sidecar.launch`
- `scenario_id`
- `obstacle_mode`
- `goal`
- `record_type`
- `timestamp`
- `elapsed` where applicable
- `odom_position` where available
- `ego_command_position` where available
- `obstacle_positions` where available
- `distance_to_goal` where available

`map_received` 的语义是 recorder 观察到了 custom cloud topic 上的
`PointCloud2` 消息。它说明我们的 pointcloud publisher 和 trace recorder
链路可见，但不等价于严格证明 official EGO 内部 grid map 已完整消费该
cloud。后续如果要作为 baseline，需要用 `rqt_graph`、`rosnode info`、
`rostopic info/echo/hz` 等工具进一步确认 remap、订阅关系和 EGO 内部地图消费。

## 删除/降级的历史内容

以下内容不再作为 TASK_02 当前主路线：

- early EGO-like waypoint experiment
- early smoke-test script
- old EGO-like static scene module
- early interface experiment 的 `final_distance_to_goal` / `min_clearance` 数值报告
- synthetic waypoint 参数调优

历史原因：它们只能说明早期接口形状和 schema 能跑，不能代表官方
EGO-Planner 行为。当前 TASK_02 只围绕 official Docker/ROS sidecar。

## 当前限制

- PyBullet mirror 是 official EGO ROS loop 的可视化/诊断镜像，不是控制后端。
- 自定义动态点云已接入 official EGO 的 `/grid_map/cloud`，但当前仍是小场景
  diagnostic，不是论文 baseline，也不是 gym-pybullet-drones 正式控制后端。
- 当前不定义统一 collision/success 标准，不做多 seed 评估，不生成正式
  baseline metrics。

## 验证命令

```bash
python3 -m pytest -q
python3 -m py_compile scripts/mirror_official_ego_ros_trace.py scripts/view_official_ego_pybullet_mirror.py
```

本报告对应的代码仍保持 diagnostic 性质。
