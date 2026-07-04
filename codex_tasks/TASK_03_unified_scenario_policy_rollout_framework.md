# TASK_03：Unified Gym-PyBullet-Drones Scenario / Policy / Rollout Framework

## 0. 任务定位

TASK_02 已收口为 official EGO-Planner Docker/ROS sidecar diagnostic。EGO 暂时冻结，不继续扩展。

TASK_03 开始准备 PIRL-NavRL 自己的主线实现：统一场景、统一 policy 接口、统一 rollout recorder、最小可运行 diagnostic pipeline，并提供可视化。

本任务不是正式实验，不训练模型，不生成论文结果，不做 baseline matrix。

## 1. NavRL / 开源项目参考规则

NavRL 不只是链路参考。可以仔细阅读 NavRL 详细代码，包括模块方法、参数组织、训练流程、环境接口、动态障碍处理、日志、可视化、部署边界等。

允许：

- 仔细检查 NavRL 各模块代码；
- 参考 NavRL 的 module boundary、API design、config pattern、parameter ranges；
- 复制小段通用 helper、schema、adapter pattern 或参数组织方式；
- 对复制或借鉴内容进行重命名、改写、类型适配和测试适配；
- 在必要处补充 attribution / license note；
- 参考其他 gym-pybullet / Gymnasium / SB3 开源项目的 env wrapper、runner、evaluator、visualization 设计。

禁止：

- 整包迁移 NavRL 训练栈；
- 直接把 NavRL 当作本项目实现主体；
- 训练或复现 NavRL；
- 把 NavRL 作为 baseline；
- 声称使用了 NavRL 结果；
- 复制代码后不适配、不测试、不说明来源；
- 引入许可证不清楚或归属不清楚的代码。

## 2. 总体目标

实现最小但可扩展的主线框架：

```text
ScenarioConfig
  -> diagnostic kinematic env / future gym-pybullet-drones adapter
  -> PolicyLike
  -> RolloutJsonlWriter
  -> PyBullet visualization
  -> diagnostic summary
```

## 3. 必须新增或更新的文件

### 3.1 ScenarioConfig

新增：

```text
pirl_navrl/scenarios/core.py
```

定义：

- `Vector3 = tuple[float, float, float]`
- `Bounds3D`
- `ObstacleConfig`
- `ScenarioConfig`

`ScenarioConfig` 至少包含：

- `scenario_id`
- `seed`
- `start`
- `goal`
- `bounds`
- `static_obstacles`
- `dynamic_obstacles`
- `max_steps`
- `dt`
- `success_radius`
- `collision_radius`

提供：

```python
make_task03_static_nav_v0(seed: int = 0) -> ScenarioConfig
```

推荐场景：

- start: `(-4.0, 0.0, 1.0)`
- goal: `(4.0, 0.0, 1.0)`
- bounds: `x=[-5, 5], y=[-5, 5], z=[0, 3]`
- 2-3 个静态障碍物
- `max_steps` 约 100
- `dt` 约 0.1 或 0.2

### 3.2 Policy interface

新增：

```text
pirl_navrl/interfaces/policy.py
pirl_navrl/interfaces/__init__.py
```

定义 `PolicyLike` Protocol：

```python
reset(self, scenario: ScenarioConfig) -> None
act(self, observation: Mapping[str, Any]) -> Any
```

### 3.3 Simple diagnostic policies

新增：

```text
pirl_navrl/policies/__init__.py
pirl_navrl/policies/simple_policies.py
```

实现：

- `RandomVelocityPolicy`
- `GoalSeekingVelocityPolicy`

要求：

- 不依赖 ROS / EGO；
- 固定 seed 可复现；
- 输出 desired velocity 或 action-like vector；
- action norm 不超过 max_speed；
- `policy_id` 必须带 debug / diagnostic 语义；
- 不声称 baseline 性能。

### 3.4 Diagnostic kinematic env

新增：

```text
pirl_navrl/platforms/diagnostic_kinematic_env.py
pirl_navrl/platforms/__init__.py
```

功能：

- `reset(scenario)`；
- `step(action)`；
- `get_observation()`；
- `position += clipped_velocity * dt`；
- bounds clamp；
- static obstacle clearance；
- collision / success / timeout 判断。

必须明确：

```text
diagnostic_kinematic_env is only a diagnostic fallback, not the final paper environment.
```

### 3.5 gym-pybullet-drones adapter skeleton

新增：

```text
pirl_navrl/platforms/gym_pybullet_drones/__init__.py
pirl_navrl/platforms/gym_pybullet_drones/simple_adapter.py
```

目标：

- 为 TASK_04 接入真实 gym-pybullet-drones 预留接口；
- 当前可以 skeleton；
- 依赖不可用时显式报错；
- 不要静默 fallback；
- 不要把 diagnostic env 冒充成 gym-pybullet-drones。

### 3.6 Rollout recorder

新增：

```text
pirl_navrl/evaluation/rollout_recorder.py
```

定义：

- `RolloutStepRecord`
- `RolloutSummary`
- `RolloutJsonlWriter`

每步字段至少包括：

- `task_id`
- `output_type`
- `platform_id`
- `scenario_id`
- `seed`
- `policy_id`
- `step`
- `position`
- `velocity`
- `goal`
- `action`
- `distance_to_goal`
- `min_clearance`
- `collision`
- `success`
- `timeout`

`output_type` 固定为 `diagnostic`。

### 3.7 Visualization

TASK_03 必须有可视化。

新增：

```text
scripts/view_task03_rollout.py
```

也可以在 rollout 脚本中支持 `--gui`。

可视化要求：

- PyBullet GUI 显示 start、goal、bounds、障碍物、当前位置、历史轨迹；
- 显示 desired velocity / action 方向线；
- 显示 collision / success / timeout 状态；
- 支持 `--direct` headless 模式；
- 能读取 JSONL trace 复现轨迹；
- 不生成视频或大产物。

### 3.8 Rollout script

新增：

```text
scripts/run_task03_gym_pybullet_rollout.py
```

默认运行：

- scenario: `task03_static_nav_v0`
- policy: `goal_seeking_velocity_debug`
- platform: `diagnostic_kinematic_env`
- output: `results/task03_static_nav_rollout.jsonl`

支持：

```bash
python3 scripts/run_task03_gym_pybullet_rollout.py
python3 scripts/run_task03_gym_pybullet_rollout.py --gui
python3 scripts/view_task03_rollout.py --trace results/task03_static_nav_rollout.jsonl
```

打印 diagnostic summary：

- `steps`
- `final_distance_to_goal`
- `min_clearance`
- `collision`
- `success`
- `timeout`
- `platform_id`
- `policy_id`

不要报告 success rate。

### 3.9 Config

新增：

```text
configs/task03_static_nav_debug.json
```

内容：

```json
{
  "task_id": "TASK_03",
  "output_type": "diagnostic",
  "scenario_id": "task03_static_nav_v0",
  "seed": 0,
  "policy_id": "goal_seeking_velocity_debug",
  "platform_id": "diagnostic_kinematic_env",
  "output_path": "results/task03_static_nav_rollout.jsonl",
  "visualize": false
}
```

### 3.10 Documentation

新增或更新：

```text
docs/03_task03_unified_rollout_framework.md
README.md
docs/navrl_reference_scope.md
```

文档必须说明：

- TASK_03 是 diagnostic framework；
- 可以细看、参考和适配 NavRL 代码；
- 复制代码必须适配、测试并处理 attribution / license；
- 当前不训练、不做 baseline、不生成论文结果；
- 可视化是 diagnostic，不是论文图。

## 4. 测试要求

新增测试：

1. `tests/test_task03_scenario_config.py`
   - ScenarioConfig 可构建；
   - start / goal / bounds / obstacles 正确；
   - seed 可控。

2. `tests/test_simple_policies.py`
   - GoalSeekingVelocityPolicy 输出朝向目标；
   - velocity norm 不超过 max_speed；
   - RandomVelocityPolicy 固定 seed 可复现。

3. `tests/test_diagnostic_kinematic_env.py`
   - reset 后位置等于 start；
   - step 后位置变化；
   - 靠近障碍物 collision=True；
   - 接近目标 success=True。

4. `tests/test_rollout_recorder.py`
   - JSONL writer 写入必需字段；
   - summary 可构建；
   - output_type 必须是 diagnostic。

5. `tests/test_task03_visualization_trace_schema.py`
   - viewer 所需字段存在；
   - headless/direct 路径不依赖 GUI；
   - 不生成视频或大文件。

## 5. 明确不做

- 不训练 PPO。
- 不训练 PIRL。
- 不接 EGO baseline。
- 不做多 seed benchmark。
- 不生成论文表格。
- 不报告 success rate。
- 不提交 results、videos、checkpoints、大日志。
- 不把 diagnostic kinematic env 当正式环境。
- 不把 NavRL 作为 baseline。
- 不声称复现 NavRL。

## 6. 验收标准

完成后必须满足：

1. `pytest -q` 通过。
2. `python3 scripts/run_task03_gym_pybullet_rollout.py` 能生成 JSONL。
3. `python3 scripts/run_task03_gym_pybullet_rollout.py --gui` 或 `python3 scripts/view_task03_rollout.py --trace ...` 能显示轨迹、障碍物和目标。
4. 所有新增代码不依赖 ROS / EGO。
5. 文档明确 TASK_03 是 diagnostic framework，不是正式实验。
6. NavRL 参考边界已更新为：可以详细参考和适配代码，但必须测试、适配、注明来源并遵守许可证。