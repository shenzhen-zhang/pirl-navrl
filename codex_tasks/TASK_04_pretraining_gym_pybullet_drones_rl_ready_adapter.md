# TASK_04：Pre-Training Gym-PyBullet-Drones RL-Ready Adapter

## 0. 任务定位

TASK_04 是训练前置准备阶段，不开始训练。

目标是把 TASK_03 的 unified scenario / policy / rollout framework 接到真实 `gym-pybullet-drones` 平台，并补齐下一阶段 SB3/PPO 训练前必须稳定的 observation、action、reward、termination、env-check 和 rollout smoke test。

本任务只做 RL-ready environment preparation。所有输出仍为 diagnostic，不做 baseline，不报告 success rate。

## 1. 背景

TASK_03 已完成：

- `ScenarioConfig`
- `PolicyLike`
- diagnostic kinematic env
- simple debug policies
- `RolloutJsonlWriter`
- PyBullet rollout viewer

TASK_04 必须保留这些接口，不要重写框架，而是实现真实 `gym-pybullet-drones` adapter 和 RL-ready env preparation。

## 2. 参考要求

可以仔细参考以下开源项目和文档。

### gym-pybullet-drones

重点参考：

- `examples/pid.py`
- `examples/pid_velocity.py`
- `examples/learn.py`
- `BaseAviary`
- `CtrlAviary`
- `VelocityAviary`
- `BaseRLAviary`

优先理解 velocity / PID / target-position 相关接口。不要在本阶段直接做 RPM policy。

### Stable-Baselines3

重点参考：

- `check_env`
- `Monitor`
- `EvalCallback`
- `VecNormalize`
- PPO example

TASK_04 不训练 PPO，但要为 TASK_05 训练做准备。

### Gymnasium

重点参考：

- reset / step API；
- observation_space / action_space；
- terminated / truncated 语义。

### NavRL

可以参考：

- env wrapper；
- observation design；
- reward shaping；
- runner / config / logging / visualization pattern；
- collision / clearance metrics。

允许复制小段通用 helper、schema、adapter pattern 或参数组织方式，但必须：

- 适配到 PIRL-NavRL 命名和类型；
- 添加测试；
- 保留必要 attribution / license note；
- 不整包迁移；
- 不声称复现 NavRL。

## 3. 总体目标

实现下面链路：

```text
ScenarioConfig
  -> GymPyBulletDronesAdapter
  -> PolicyLike desired_velocity
  -> ActionAdapter
  -> env.step()
  -> ObservationAdapter
  -> RolloutJsonlWriter
  -> Viewer / diagnostic summary
```

## 4. 必须新增或更新的文件

### 4.1 更新 real adapter

更新：

```text
pirl_navrl/platforms/gym_pybullet_drones/simple_adapter.py
```

实现：

- `class GymPybulletDronesSimpleAdapter`
- `reset(scenario: ScenarioConfig)`
- `step(desired_velocity)`
- `get_observation()`
- `close()`

要求：

- 优先使用 `gym-pybullet-drones` 的 velocity / PID / target-position 相关接口；
- 不直接做 RPM policy；
- 如果底层 env 不支持自定义障碍物物理碰撞，必须明确写 `diagnostic obstacle metrics only`；
- 不能静默 fallback 到 `diagnostic_kinematic_env`；
- 依赖缺失时显式报错；
- `platform_id = gym_pybullet_drones_velocity_adapter_debug`。

### 4.2 新增 action adapter

新增：

```text
pirl_navrl/platforms/gym_pybullet_drones/action_adapter.py
```

实现：

- `clip_desired_velocity(desired_velocity, max_speed)`
- `normalize_desired_velocity(desired_velocity, max_speed)`
- `desired_velocity_to_action(desired_velocity, action_mode)`

要求：

- 输出 shape 为 `(3,)`；
- normalized action 在 `[-1, 1]`；
- `max_speed <= 0` 必须报错；
- 输出或 info 中可追踪 raw desired velocity、clipped desired velocity、applied action；
- 不实现 RPM 训练 policy。

### 4.3 新增 observation adapter

新增：

```text
pirl_navrl/platforms/gym_pybullet_drones/observation_adapter.py
```

实现统一 observation dict：

- `position`
- `velocity`
- `goal`
- `relative_goal`
- `distance_to_goal`
- `nearest_obstacle_relative_position`
- `nearest_obstacle_distance`
- `min_clearance`
- `step_fraction`

同时提供：

- `flatten_observation(obs_dict) -> np.ndarray`
- `observation_space_for_scenario(scenario) -> gymnasium.spaces.Box`

要求：

- shape 固定；
- 数值 finite；
- 适合下一阶段 PPO；
- 不把 dict schema 和 flattened schema 混淆。

### 4.4 新增 reward module

新增：

```text
pirl_navrl/evaluation/reward.py
```

实现：

```text
compute_task04_reward(previous_obs, current_obs, action, event_flags, config)
```

初版 reward：

- progress_to_goal reward；
- distance penalty；
- action norm penalty；
- clearance penalty；
- collision penalty；
- success bonus；
- timeout penalty。

要求：

- reward 必须 finite；
- reward terms 写入 `info["reward_terms"]`；
- 不调参追求训练效果，只保证可解释和可运行。

### 4.5 新增 Gymnasium RL env wrapper

新增：

```text
pirl_navrl/platforms/gym_pybullet_drones/rl_env.py
```

实现：

- `class Task04GymPybulletDronesRLEnv(gymnasium.Env)`
- `observation_space`
- `action_space`
- `reset(seed=None, options=None)`
- `step(action)`
- `render` optional
- `close`

要求：

- `reset` 返回 `(observation, info)`；
- `step` 返回 `(observation, reward, terminated, truncated, info)`；
- `terminated = success or collision`；
- `truncated = timeout only`；
- `action_space = Box(low=-1, high=1, shape=(3,))`；
- observation 可以先用 flattened observation vector；
- info 包含 diagnostic metrics：position、velocity、distance_to_goal、min_clearance、collision、success、timeout、reward_terms、platform_id、scenario_id、seed。

### 4.6 新增 env checker

新增：

```text
scripts/check_task04_rl_ready_env.py
```

功能：

- 创建 `Task04GymPybulletDronesRLEnv`；
- reset；
- random action step 若干步；
- 检查 observation shape 固定；
- 检查 reward finite；
- 检查 terminated / truncated 类型正确；
- 检查 info 包含 metrics；
- 若 `stable_baselines3` 可用，运行 `check_env`；
- 如果 `gym-pybullet-drones` 不可用，明确报错或 skip integration，不要伪装通过。

### 4.7 新增 rollout smoke test

新增：

```text
scripts/run_task04_gym_pybullet_drones_rollout.py
configs/task04_gym_pybullet_static_nav_debug.json
```

默认配置：

```json
{
  "task_id": "TASK_04",
  "output_type": "diagnostic",
  "scenario_id": "task03_static_nav_v0",
  "seed": 0,
  "policy_id": "goal_seeking_velocity_debug",
  "platform_id": "gym_pybullet_drones_velocity_adapter_debug",
  "output_path": "results/task04_gym_pybullet_static_nav_rollout.jsonl",
  "max_speed": 1.0,
  "visualize": false
}
```

脚本要求：

- 使用 `goal_seeking_velocity_debug` policy；
- 使用真实 `gym_pybullet_drones_velocity_adapter_debug`；
- 写统一 JSONL；
- 打印 diagnostic summary；
- 支持 `--gui`；
- 不训练、不报告 success rate、不生成视频、不提交 results。

### 4.8 文档

新增或更新：

```text
docs/04_task04_gym_pybullet_drones_adapter.md
README.md
```

说明：

- TASK_04 是训练前置准备；
- 不训练；
- 为什么优先 desired_velocity 而不是 RPM；
- observation / action / reward / termination 设计；
- 哪些参考了 gym-pybullet-drones / SB3 / Gymnasium / NavRL；
- 当前限制；
- TASK_05 如何开始 PPO debug training。

## 5. 测试要求

新增测试：

### 5.1 `tests/test_task04_action_adapter.py`

验证：

- velocity clipping 正确；
- normalized action 在 `[-1, 1]`；
- `max_speed <= 0` 报错；
- 输出 shape 为 `(3,)`。

### 5.2 `tests/test_task04_observation_adapter.py`

验证：

- observation dict 字段完整；
- `flatten_observation` shape 固定；
- `observation_space.contains(flattened_obs)`；
- 数值 finite。

### 5.3 `tests/test_task04_reward.py`

验证：

- progress reward 方向正确；
- collision penalty 生效；
- success bonus 生效；
- reward finite；
- reward_terms 包含各项。

### 5.4 `tests/test_task04_rl_env_contract.py`

验证：

- 如果 `gym-pybullet-drones` 不可用，integration test skip；
- 如果可用，reset 返回 `(obs, info)`；
- step 返回 5 元组；
- terminated / truncated 语义正确；
- action_space / observation_space 存在。

### 5.5 `tests/test_task04_config_schema.py`

验证：

- config 字段完整；
- `output_type = diagnostic`；
- platform_id 正确。

## 6. 明确不做

TASK_04 禁止：

- 不训练 PPO；
- 不训练 PIRL；
- 不接 EGO baseline；
- 不做多 seed benchmark；
- 不做正式 baseline；
- 不报告 success rate；
- 不调参追求效果；
- 不提交 results、videos、checkpoints、TensorBoard、wandb。

## 7. 验收标准

完成后必须满足：

1. `pytest -q` 通过。
2. `python3 scripts/check_task04_rl_ready_env.py` 可运行，依赖缺失时明确说明。
3. `python3 scripts/run_task04_gym_pybullet_drones_rollout.py` 可运行，或在依赖缺失时明确报错。
4. 文档明确 TASK_04 不训练、不做 baseline。
5. action / observation / reward / termination 已稳定到可以进入 TASK_05 PPO debug training。
6. 不提交 results、videos、checkpoints、TensorBoard、wandb。