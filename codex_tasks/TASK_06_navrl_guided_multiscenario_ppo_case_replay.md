# TASK_06：NavRL-Guided Multi-Scenario PPO Training with Case Replay

## 0. 任务定位

TASK_06 是参考 NavRL 的多场景 PPO 稳定化训练与成功/失败案例回放阶段。

TASK_05 已经完成 NavRL-informed PPO debug training pipeline，但简单训练效果较差。TASK_06 不应只在无障碍最简单任务上调通，而应在静态、动态、潜在动态三类诊断场景上都观察到相对 random / untrained policy 的 debug-level learning effect。

本任务仍然不是正式论文实验，不做 baseline，不接 EGO，不实现完整 PIRL，不报告正式 success rate，不提交训练产物。

## 1. 总体目标

目标是在 TASK_05 的基础上完成：

```text
NavRL-guided scenario expansion
  -> reward / observation / PPO stabilization
  -> static PPO training/eval
  -> dynamic PPO training/eval
  -> latent-dynamic PPO training/eval
  -> case selection
  -> GIF / trace replay visualization
  -> random vs trained summary metrics
```

每类场景训练后必须输出：

- random policy eval summary；
- trained checkpoint eval summary；
- success case 或 best_non_success case；
- representative failure case；
- JSONL trace；
- GIF 或 fallback summary；
- failure analysis。

## 2. NavRL-guided 调整文档

必须新增：

```text
docs/navrl_guided_training_adjustments_task06.md
```

该文档必须维护一张持续更新的表：

```text
NavRL reference
Observed setting
PIRL-NavRL adaptation
Reason
Result / observation
Next change
```

每次调整以下内容都必须记录 NavRL 参考依据：

- scenario size / obstacle distribution；
- static obstacle parameters；
- dynamic obstacle motion pattern；
- latent / sudden-motion trigger design；
- observation features；
- reward terms and weights；
- PPO / VecNormalize / env runner settings；
- eval / logging / checkpoint / visualization design。

禁止：

- 整包迁移 NavRL；
- 把 NavRL 当 baseline；
- 声称复现 NavRL；
- 使用 NavRL checkpoint 或结果；
- 复制许可证不清楚的代码。

## 3. 场景扩展

至少支持以下 scenario groups：

```text
static
dynamic
latent_dynamic
mixed_static_dynamic
```

推荐 levels：

```text
static_obstacle_easy
static_obstacle_medium
dynamic_crossing_easy
latent_dynamic_easy
mixed_static_dynamic_easy
```

新增或更新：

```text
pirl_navrl/scenarios/dynamic_curriculum.py
configs/task06_multiscenario_curriculum.json
```

### 3.1 static

要求：

- 固定 arena；
- seed-controlled start / goal；
- 1-5 个静态 sphere / cylinder；
- obstacle 不贴 start / goal；
- 部分 obstacle 接近 start-goal 直线路径；
- 支持 easy / medium 难度。

### 3.2 dynamic

要求：

- 至少 1 个动态 obstacle；
- motion pattern 优先实现 `linear_crossing`；
- 可配置速度范围、起止点、active time window；
- observation 暴露当前动态障碍位置/相对位置/相对速度相关特征；
- 不做复杂 intent prediction。

### 3.3 latent_dynamic

要求：

- obstacle 初期静止或低风险；
- 到达 `trigger_step` 或 drone 距离小于 `trigger_radius` 后突然开始横穿；
- 不直接向 policy 泄露未来 trigger label；
- 可以给当前 obstacle state、当前速度和历史差分；
- eval 必须能识别 `latent_trigger_failure`。

## 4. Observation / reward / training 稳定化

根据 NavRL 和 TASK_05 训练问题，补齐以下模块：

```text
pirl_navrl/platforms/gym_pybullet_drones/feature_scaling.py
pirl_navrl/evaluation/reward_profiles.py
pirl_navrl/analysis/rollout_metrics.py
pirl_navrl/training/vec_env.py
```

### 4.1 feature scaling

支持 normalized observation 或 feature scaling，至少覆盖：

- position / arena size；
- velocity / max_speed；
- relative_goal / arena size；
- distance_to_goal / max_distance；
- obstacle relative position / arena size；
- obstacle relative velocity / max_dynamic_speed；
- clearance / arena size；
- step_fraction。

### 4.2 reward profiles

至少支持：

```text
goal_only
static_avoidance
dynamic_avoidance
latent_risk
```

`static_avoidance` 应包含 progress、distance、clearance、collision、action/smoothness、success、timeout。`dynamic_avoidance` 应加入 relative velocity risk / time-to-collision style penalty。`latent_risk` 应鼓励保持 clearance、避免 late evasive behavior，但不能泄露未来 trigger label。

### 4.3 training stabilization

支持：

- DummyVecEnv；
- VecNormalize；
- separate eval env；
- EvalCallback 或等价 eval loop；
- checkpoint save / load；
- normalization stats save / load；
- random vs trained eval。

## 5. 训练步数和停止条件

训练步数可以根据效果调整，不设置过小硬上限。必须保留工程安全阀和 progress checkpoints。

配置中建议支持：

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

## 6. 训练脚本和配置

新增：

```text
pirl_navrl/training/task06_multiscenario.py
scripts/train_task06_multiscenario_ppo.py
scripts/eval_task06_multiscenario.py
scripts/analyze_task06_rollout.py
scripts/plot_task06_multiscenario_summary.py
configs/task06_static_ppo.json
configs/task06_dynamic_ppo.json
configs/task06_latent_dynamic_ppo.json
configs/task06_case_selection.json
```

训练建议分阶段：

```text
Stage A: static obstacle PPO
Stage B: dynamic obstacle PPO
Stage C: latent dynamic PPO
Stage D: mixed scenario eval or smoke training
```

不要只训练一个 mixed policy 后再判断全部场景。

## 7. Eval / case selection

新增：

```text
pirl_navrl/evaluation/case_selector.py
scripts/select_task06_cases.py
```

每个 scenario group 训练后必须选择：

```text
success_case 或 best_non_success_case
representative failure_case
```

输出位置：

```text
outputs/task06/<run_id>/cases/<scenario_group>/
```

### 7.1 success case 规则

优先选择：

1. `success == true`；
2. `collision == false`；
3. `final_distance_to_goal` 最小；
4. `path_length` 不异常；
5. `min_clearance` 合理。

如果没有 success，选择 best non-success case，并明确写：

```json
{
  "case_type": "best_non_success_case",
  "reason": "no_success_found"
}
```

不允许伪造 success。

### 7.2 failure case 规则

失败案例必须分类，至少支持：

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

## 8. GIF / 可视化

新增：

```text
pirl_navrl/visualization/gif_renderer.py
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

GIF 必须输出到 `outputs/task06/...`，不得提交仓库。如果缺少 matplotlib / pillow / imageio 等依赖，必须生成 fallback summary JSON，并清楚说明没有生成 GIF 的原因。

## 9. Summary metrics

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

## 10. 文档

新增：

```text
docs/06_task06_navrl_guided_multiscenario_ppo_case_replay.md
docs/navrl_guided_training_adjustments_task06.md
```

文档必须说明：

- TASK_06 为什么不只做 level_0；
- 三类场景定义；
- NavRL 如何指导调整；
- success / failure case 如何选择；
- GIF 如何生成；
- 训练步数如何根据效果调整；
- 哪些产物不能提交；
- 如果没有成功案例，如何标记 best_non_success_case。

## 11. 测试

新增 tests：

```text
tests/test_task06_dynamic_curriculum.py
tests/test_task06_rollout_metrics.py
tests/test_task06_case_selector.py
tests/test_task06_gif_renderer_schema.py
tests/test_task06_config_schema.py
tests/test_task06_navrl_adjustment_doc.py
```

测试要求：

- static / dynamic / latent_dynamic scenario 都能生成；
- dynamic obstacle position 随时间变化；
- latent dynamic obstacle 在 trigger 前后状态不同；
- rollout metrics 能计算 final_distance、path_length、min_clearance、action_norm；
- case selector 能正确选择 success / best_non_success / failure；
- GIF renderer 在缺依赖时能写 fallback summary；
- configs 字段完整且 outputs 路径安全；
- NavRL adjustment 文档存在并包含具体 reference 表。

## 12. 验收标准

完成后必须满足：

1. `pytest -q` 通过；
2. `docs/navrl_guided_training_adjustments_task06.md` 完成并包含具体 NavRL reference 表；
3. static / dynamic / latent_dynamic 三类场景都可生成；
4. static / dynamic / latent_dynamic 三类都可训练或至少可运行训练 smoke；
5. 每类都能执行 random policy eval 和 trained checkpoint eval；
6. 每类都生成 success 或 best_non_success case；
7. 每类都生成 representative failure case；
8. 每类 case 都可渲染 GIF 或在缺依赖时生成明确 fallback summary；
9. 每类都有 random vs trained summary metrics；
10. 如果某类没有改善，必须在 docs 中解释失败类型和下一步修正；
11. 不提交 outputs、checkpoints、GIF、videos、TensorBoard、wandb。

## 13. 明确不做

TASK_06 不做：

- 不做正式论文 baseline；
- 不做 EGO baseline；
- 不声称复现 NavRL；
- 不使用 NavRL checkpoint 或结果；
- 不实现完整 PIRL intent-risk 方法；
- 不报告正式 success rate；
- 不提交训练产物。

## 14. 提交前检查

提交前请确认：

```bash
python3 -m pytest -q
```

并确认：

```text
outputs/
results/
runs/
wandb/
*.zip
*.gif
*.mp4
```

没有被提交。