# TASK_04 设计：Pre-Training Gym-PyBullet-Drones RL-Ready Adapter

## 1. 阶段定位

TASK_04 是训练前置准备阶段，不开始训练。

TASK_03 已完成统一 `ScenarioConfig`、`PolicyLike`、diagnostic env、rollout recorder 和可视化。TASK_04 的目标是把这套统一框架接到真实 `gym-pybullet-drones` 平台，并补齐下一阶段 SB3 / PPO debug training 之前必须稳定的 action、observation、reward、termination、env checker 和 rollout smoke test。

本阶段仍然只生成 diagnostic JSONL，不生成论文指标，不做 baseline，不报告 success rate。

## 2. 开源项目调研参考范围

TASK_04 可以仔细参考以下项目和文档：

### gym-pybullet-drones

重点参考：

- `examples/pid.py`
- `examples/pid_velocity.py`
- `examples/learn.py`
- `BaseAviary`
- `CtrlAviary`
- `VelocityAviary`
- `BaseRLAviary`

重点理解：

- reset / step / render / close 调用方式；
- drone state 读取方式；
- PID / velocity reference / target-position 控制方式；
- observation/action shape；
- 和 SB3 训练示例的接口边界。

### Stable-Baselines3

重点参考：

- `check_env`
- `Monitor`
- `EvalCallback`
- `VecNormalize`
- PPO example

TASK_04 不训练 PPO，但要让 env 具备下一阶段接 SB3 的条件。

### Gymnasium

重点参考：

- `reset(seed=None, options=None) -> (obs, info)`；
- `step(action) -> (obs, reward, terminated, truncated, info)`；
- `observation_space` / `action_space`；
- `terminated` 与 `truncated` 分离。

### NavRL

NavRL 可以作为详细实现参考，尤其是：

- env wrapper；
- observation design；
- reward shaping；
- runner / config / logging；
- visualization organization；
- collision / clearance metrics。

允许复制小段通用 helper、schema、adapter pattern 或参数组织方式，但必须适配到 PIRL-NavRL 自己的命名、类型、平台和测试，并处理 attribution / license。不得整包迁移 NavRL 训练栈，不得声称复现 NavRL。

## 3. 核心设计原则

### 3.1 优先 desired_velocity，不直接做 RPM policy

PIRL、PPO debug policy、EGO sidecar 和后续 shield 都更自然地产生 high-level desired velocity。因此 TASK_04 优先实现：

```text
PolicyLike desired_velocity
  -> action adapter
  -> gym-pybullet-drones velocity / PID / target-position control layer
```

不要在本阶段直接训练 RPM-level policy。RPM 会把低层控制和导航学习混在一起，增加调试成本。

### 3.2 保持 TASK_03 接口不变

TASK_04 不重写 TASK_03 框架，只替换 platform adapter：

```text
ScenarioConfig
  -> GymPyBulletDronesAdapter
  -> PolicyLike desired_velocity
  -> RolloutJsonlWriter
```

`RolloutStepRecord` 和 JSONL schema 应尽量兼容 TASK_03。

### 3.3 不静默 fallback

如果 `gym-pybullet-drones` 不可用，真实 adapter 和脚本必须明确报错或显式 skip integration test。不要静默退回 `diagnostic_kinematic_env`，避免用户误以为真实平台已接入。

## 4. 必须补齐的模块

### 4.1 Real adapter

更新：

```text
pirl_navrl/platforms/gym_pybullet_drones/simple_adapter.py
```

实现：

- `GymPybulletDronesSimpleAdapter`
- `reset(scenario)`
- `step(desired_velocity)`
- `get_observation()`
- `close()`

`platform_id` 使用：

```text
gym_pybullet_drones_velocity_adapter_debug
```

如果底层 env 暂不支持我们自定义障碍物碰撞，必须明确写成 diagnostic obstacle metrics only，不要声称障碍物已进入真实物理碰撞。

### 4.2 Action adapter

新增：

```text
pirl_navrl/platforms/gym_pybullet_drones/action_adapter.py
```

实现：

- `clip_desired_velocity(desired_velocity, max_speed)`
- `normalize_desired_velocity(desired_velocity, max_speed)`
- `desired_velocity_to_action(desired_velocity, action_mode)`

要求：

- action shape 固定为 `(3,)`；
- normalized action 在 `[-1, 1]`；
- `max_speed <= 0` 必须报错；
- 输出或 info 中保留 raw desired velocity、clipped desired velocity、applied action。

### 4.3 Observation adapter

新增：

```text
pirl_navrl/platforms/gym_pybullet_drones/observation_adapter.py
```

统一 observation dict 至少包括：

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

要求 shape 固定、数值 finite，方便 TASK_05 直接接 PPO。

### 4.4 Reward

新增：

```text
pirl_navrl/evaluation/reward.py
```

实现：

```text
compute_task04_reward(previous_obs, current_obs, action, event_flags, config)
```

初版 reward terms：

- progress_to_goal reward；
- distance penalty；
- action norm penalty；
- clearance penalty；
- collision penalty；
- success bonus；
- timeout penalty。

要求：

- reward finite；
- `info["reward_terms"]` 包含分项；
- 不调参追求训练效果，只保证可解释、可运行、可检查。

### 4.5 Gymnasium RL env wrapper

新增：

```text
pirl_navrl/platforms/gym_pybullet_drones/rl_env.py
```

实现：

- `Task04GymPybulletDronesRLEnv(gymnasium.Env)`
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
- info 包含 position、velocity、distance_to_goal、min_clearance、collision、success、timeout、reward_terms、platform_id、scenario_id、seed。

### 4.6 Env checker

新增：

```text
scripts/check_task04_rl_ready_env.py
```

检查：

- reset 正常；
- random action step 若干步；
- observation shape 固定；
- reward finite；
- terminated / truncated 类型正确；
- info 包含 diagnostic metrics；
- 若 stable_baselines3 可用，运行 `check_env`；
- 若 gym-pybullet-drones 不可用，明确报错或 skip integration，不要伪装通过。

### 4.7 Rollout smoke test

新增：

```text
scripts/run_task04_gym_pybullet_drones_rollout.py
configs/task04_gym_pybullet_static_nav_debug.json
```

默认运行：

```text
scenario_id: task03_static_nav_v0
policy_id: goal_seeking_velocity_debug
platform_id: gym_pybullet_drones_velocity_adapter_debug
output_path: results/task04_gym_pybullet_static_nav_rollout.jsonl
```

要求：

- 不训练；
- 不报告 success rate；
- 不生成视频；
- 不提交 results。

### 4.8 Visualization

TASK_04 可以复用 TASK_03 viewer，或新增 `scripts/view_task04_rollout.py`。

可视化至少显示：

- drone position；
- goal；
- obstacles；
- desired velocity；
- applied action；
- trajectory；
- collision / success / timeout。

可视化仍然是 diagnostic，不是论文图。

## 5. 明确不做

TASK_04 不做：

- 不训练 PPO；
- 不训练 PIRL；
- 不接 EGO baseline；
- 不做多 seed benchmark；
- 不做正式 baseline；
- 不报告 success rate；
- 不调参追求效果；
- 不提交 results、videos、checkpoints、TensorBoard、wandb。

## 6. TASK_04 完成后的标准表述

完成后可以说：

```text
We prepared an RL-ready gym-pybullet-drones adapter and diagnostic rollout path that can be checked before SB3/PPO training.
```

不能说：

```text
We trained an effective policy.
We completed a baseline.
We completed the PIRL method.
```

## 7. 进入 TASK_05 的条件

TASK_04 完成后，进入 TASK_05 前应满足：

1. RL env 能 reset/step/close。
2. observation_space / action_space 固定。
3. reward finite 且分项可解释。
4. terminated/truncated 语义正确。
5. diagnostic rollout 能写统一 JSONL。
6. `check_task04_rl_ready_env.py` 能运行。
7. 文档明确当前还未训练。

满足这些条件后，TASK_05 才开始 SB3 / PPO debug training。