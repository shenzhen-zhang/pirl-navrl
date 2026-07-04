# TASK_06 设计：NavRL-Guided Multi-Scenario PPO Training with Case Replay

## 1. 阶段定位

TASK_06 是参考 NavRL 的多场景 PPO 稳定化训练与案例回放阶段。

TASK_05 已经搭建了 NavRL-informed curriculum、SB3 PPO debug training、eval rollout 和基础可视化链路，但简单训练效果较差。TASK_06 不应只在无障碍最简单任务上调通，而应在 NavRL 成功案例的启发下，扩展到三类核心诊断场景并观察 PPO 是否出现 debug-level learning effect：

1. 静态障碍场景；
2. 动态障碍场景；
3. 潜在动态 / sudden-motion / hidden-risk 场景。

本阶段仍然不是正式论文实验，不做 baseline，不接 EGO，不实现完整 PIRL，不报告正式 success rate。它的目标是形成可训练、可诊断、可回放、可解释的多场景 PPO 调试训练流程。

## 2. NavRL-guided 调整要求

TASK_06 的场景、observation、reward、PPO config 和 eval/case selection 调整必须密切参考 NavRL。

必须新增：

```text
docs/navrl_guided_training_adjustments_task06.md
```

该文档必须维护一张持续更新的审查/调整表，至少包含：

```text
NavRL reference
Observed setting
PIRL-NavRL adaptation
Reason
Result / observation
Next change
```

每次修改以下内容都必须记录：

- scenario size / obstacle distribution；
- static obstacle parameters；
- dynamic obstacle motion pattern；
- latent / sudden-motion trigger design；
- observation features；
- reward terms and weights；
- PPO / VecNormalize / env runner settings；
- eval / logging / checkpoint / visualization design。

允许参考 NavRL 的模块组织、参数范围、helper、schema、adapter pattern 和训练流程。禁止整包迁移 NavRL、把 NavRL 当 baseline、声称复现 NavRL、使用 NavRL 结果或复制许可证不清楚的代码。

## 3. 三类场景要求

TASK_06 至少支持以下 scenario groups：

```text
static
dynamic
latent_dynamic
mixed_static_dynamic
```

推荐具体 levels：

```text
static_obstacle_easy
static_obstacle_medium
dynamic_crossing_easy
latent_dynamic_easy
mixed_static_dynamic_easy
```

### 3.1 静态障碍

目标：训练策略在静态障碍场景中相对 random / untrained policy 有更好的接近目标与避障行为。

第一版要求：

- 固定 arena；
- seed-controlled start / goal；
- 1-5 个静态 sphere / cylinder；
- 障碍物不贴 start / goal；
- 部分障碍物应接近 start-goal 直线路径；
- 支持 easy / medium 难度。

### 3.2 动态障碍

目标：训练策略能对可观测 moving obstacle 做出反应。

第一版要求：

- 至少 1 个动态障碍；
- motion pattern 优先使用 `linear_crossing`；
- 可配置速度范围、起止点、active time window；
- observation 需要暴露当前动态障碍位置/相对位置/相对速度相关特征；
- 不要求复杂 intent prediction。

### 3.3 潜在动态 / sudden-motion

目标：构造与 PIRL intent-risk 主题更接近的诊断场景。

第一版要求：

- 障碍物初期静止或低风险；
- 到达 `trigger_step` 或 drone 距离小于 `trigger_radius` 后突然开始横穿；
- 不直接向 policy 泄露未来 trigger label；
- 可以给当前 obstacle state、当前速度和历史差分；
- eval 要能显示是否出现 late reaction / near miss / latent trigger failure。

## 4. 训练策略

TASK_06 可以根据训练表现调整 timesteps，不设置过小硬上限。建议保留工程安全阀和 early stopping：

```text
min_timesteps
max_timesteps
eval_freq
patience_evals
target_success_rate_debug
target_final_distance
early_stop_on_plateau
```

默认可以从 50k 到 300k 起步；必要时允许扩展到 1M 或更高，但必须记录 reason 和 intermediate eval。不要把训练产物提交到仓库。

训练建议分阶段执行：

```text
Stage A: static obstacle PPO
Stage B: dynamic obstacle PPO
Stage C: latent dynamic PPO
Stage D: mixed scenario eval or smoke training
```

不要一开始只训练 mixed policy，否则失败时无法定位问题来源。

## 5. 成功案例 / 失败案例输出

每个 scenario group 训练后必须输出案例包。案例包保存在：

```text
outputs/task06/<run_id>/cases/<scenario_group>/
```

每类场景至少输出：

```text
success_case.jsonl
success_case.gif
success_case_summary.json
failure_case.jsonl
failure_case.gif
failure_case_summary.json
```

如果没有真正 success case，不允许伪造成成功。必须输出：

```text
best_non_success_case.jsonl
best_non_success_case.gif
best_non_success_case_summary.json
```

并在 summary 中写明：

```text
case_type: best_non_success_case
reason: no_success_found
```

### 5.1 成功案例选择规则

自动 selector 优先选择：

1. `success == true`；
2. `collision == false`；
3. `final_distance_to_goal` 最小；
4. `path_length` 不异常；
5. `min_clearance` 合理。

如果没有 success，则选择 non-success 中最接近目标且无碰撞优先的 best case。

### 5.2 失败案例选择规则

失败案例应是 representative failure，不一定是最差 episode。至少分类：

```text
collision_failure
timeout_failure
near_miss_failure
control_instability_failure
dynamic_late_reaction_failure
latent_trigger_failure
```

每个 failure summary 必须说明：

- failure_type；
- failure_step；
- final_distance_to_goal；
- min_clearance；
- collision / timeout；
- suspected cause；
- next suggested fix。

## 6. GIF / 可视化要求

GIF 可以生成，但必须保存在 `outputs/`，不得提交仓库。

新增建议脚本：

```text
scripts/render_task06_case_gif.py
```

GIF 至少显示：

- drone trajectory；
- start / goal；
- static obstacles；
- dynamic obstacle positions over time；
- latent trigger marker / state；
- current step；
- distance_to_goal；
- min_clearance；
- success / collision / timeout。

优先使用 JSONL trace replay 渲染 GIF。不要依赖提交视频或大图片文件。

## 7. 指标摘要

每个 scenario group 必须生成：

```text
random_policy_summary.json
trained_policy_summary.json
case_selection_summary.json
```

建议字段：

```json
{
  "scenario_group": "static",
  "checkpoint": "outputs/task06/.../final_model.zip",
  "num_eval_episodes": 20,
  "success_count": 0,
  "collision_count": 0,
  "timeout_count": 0,
  "mean_final_distance": 0.0,
  "mean_min_clearance": 0.0,
  "mean_path_length": 0.0,
  "mean_action_norm": 0.0,
  "best_case_trace": "...",
  "failure_case_trace": "...",
  "best_case_gif": "...",
  "failure_case_gif": "...",
  "debug_learning_effect": "improved_or_not_observed",
  "notes": ""
}
```

这些不是正式 benchmark 指标，只用于 debug learning effect 判断。

## 8. 建议新增文件

文档：

```text
docs/06_task06_navrl_guided_multiscenario_ppo_case_replay.md
docs/navrl_guided_training_adjustments_task06.md
codex_tasks/TASK_06_navrl_guided_multiscenario_ppo_case_replay.md
```

模块：

```text
pirl_navrl/scenarios/dynamic_curriculum.py
pirl_navrl/training/task06_multiscenario.py
pirl_navrl/evaluation/case_selector.py
pirl_navrl/visualization/gif_renderer.py
pirl_navrl/analysis/rollout_metrics.py
pirl_navrl/evaluation/reward_profiles.py
pirl_navrl/platforms/gym_pybullet_drones/feature_scaling.py
pirl_navrl/training/vec_env.py
```

脚本：

```text
scripts/train_task06_multiscenario_ppo.py
scripts/eval_task06_multiscenario.py
scripts/select_task06_cases.py
scripts/render_task06_case_gif.py
scripts/plot_task06_multiscenario_summary.py
scripts/analyze_task06_rollout.py
```

配置：

```text
configs/task06_static_ppo.json
configs/task06_dynamic_ppo.json
configs/task06_latent_dynamic_ppo.json
configs/task06_case_selection.json
configs/task06_multiscenario_curriculum.json
```

测试：

```text
tests/test_task06_dynamic_curriculum.py
tests/test_task06_rollout_metrics.py
tests/test_task06_case_selector.py
tests/test_task06_gif_renderer_schema.py
tests/test_task06_config_schema.py
tests/test_task06_navrl_adjustment_doc.py
```

## 9. 验收标准

TASK_06 完成后必须满足：

1. `pytest -q` 通过；
2. `docs/navrl_guided_training_adjustments_task06.md` 完成并包含具体 NavRL reference 表；
3. static / dynamic / latent_dynamic 三类场景都可生成；
4. static / dynamic / latent_dynamic 三类都可训练或至少可运行训练 smoke；
5. 每类都能执行 random policy eval 和 trained checkpoint eval；
6. 每类都生成 success 或 best_non_success case；
7. 每类都生成 representative failure case；
8. 每类 case 都可渲染 GIF 或在缺依赖时生成明确的 fallback summary；
9. 每类都有 random vs trained summary metrics；
10. 如果某类没有改善，必须在 docs 中解释失败类型和下一步修正；
11. 不提交 outputs、checkpoints、GIF、videos、TensorBoard、wandb。

## 10. 明确不做

TASK_06 不做：

- 不做正式论文 baseline；
- 不做 EGO baseline；
- 不声称复现 NavRL；
- 不使用 NavRL checkpoint 或结果；
- 不实现完整 PIRL intent-risk 方法；
- 不报告正式 success rate；
- 不提交训练产物。

## 11. TASK_07 前置条件

只有当 TASK_06 证明三类场景至少有 debug-level learning effect，或者清楚记录每类失败原因和下一步修正后，才进入 TASK_07。

TASK_07 可以进入 PIRL risk / intent module prototype，但前提是 TASK_06 已经提供静态、动态、潜在动态三类可回放案例。