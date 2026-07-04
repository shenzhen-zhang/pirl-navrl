# TASK_06：NavRL-Guided Multi-Scenario PPO Training with Top-Down Case Replay

## 0. 任务定位

TASK_06 是多场景 PPO 稳定化训练与案例回放阶段。它在 TASK_05 基础上继续推进，但不能停留在 very short smoke run。目标是建设接近论文实验前置质量的训练系统：场景设计、训练预算、评估、失败分类、案例筛选和俯视角可视化都必须严格执行。

TASK_06 仍不是正式论文结果阶段：不发布正式 success-rate 结论，不接 EGO baseline，不声称复现 NavRL，不使用 NavRL checkpoint 或结果，不提交训练产物。所有训练输出保存在 `outputs/`。

## 1. 执行状态：smoke 不等于完成

2k / 4k / 10k step 以内只能算 smoke。Smoke 只用于依赖和脚本连通性检查，不能算 TASK_06 完成。

有效状态只有：

```text
completed_full_training
blocked
smoke_only_not_complete
```

硬性要求：

- smoke checkpoint 不能作为 final trained checkpoint；
- smoke run 不能用于最终 success/failure case selection；
- 只完成 smoke 时，必须写 `docs/TASK_06_SMOKE_ONLY_REPORT.md`；
- full training 无法完成时，必须写 `docs/TASK_06_BLOCKED_TRAINING_REPORT.md`；
- 每个 scenario group 必须写 `training_completion_status.json`。

## 2. 训练预算

必须创建：

```text
configs/task06_training_budget.json
```

最低字段：

```json
{
  "smoke_timesteps": 4096,
  "smoke_is_completion": false,
  "scenario_budgets": {
    "static": {
      "min_timesteps_required": 100000,
      "initial_budget_timesteps": 300000,
      "max_timesteps_safety_cap": 1000000,
      "eval_freq": 10000,
      "patience_evals": 10
    },
    "dynamic": {
      "min_timesteps_required": 150000,
      "initial_budget_timesteps": 500000,
      "max_timesteps_safety_cap": 1500000,
      "eval_freq": 10000,
      "patience_evals": 12
    },
    "latent_dynamic": {
      "min_timesteps_required": 150000,
      "initial_budget_timesteps": 500000,
      "max_timesteps_safety_cap": 1500000,
      "eval_freq": 10000,
      "patience_evals": 12
    }
  }
}
```

这些是 TASK_06 下限，不是最终论文超参数。训练可以更长，但必须记录原因和中间 eval。

## 3. 训练脚本

`scripts/train_task06_multiscenario_ppo.py` 必须支持：

```text
--mode full
--mode smoke
--scenario-group static|dynamic|latent_dynamic|mixed_static_dynamic
```

默认必须是 `--mode full`。只有显式传 `--mode smoke` 才能短跑。`full` 模式必须读取 training budget；没达到 `min_timesteps_required` 时不能标记 completed。

## 4. NavRL 参考要求

必须维护：

```text
docs/navrl_guided_training_adjustments_task06.md
```

每次修改 scenario、observation、reward、PPO config、runner、action constraint、curriculum、evaluation 或 visualization，都必须记录具体 NavRL 文件/module/config/script：

```text
NavRL reference
Observed setting
PIRL-NavRL adaptation
Reason
Result / observation
Next change
```

训练效果差时，Codex 必须先重新查看 NavRL，再调整本项目。不能只盲调 PPO 参数。可以密切参考 NavRL 的训练思路、结构、参数、runner、observation、reward、curriculum、动态障碍组织和可视化流程；禁止整包迁移或声称复现 NavRL。

## 5. 场景组

至少支持：

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

要求：

- static：seeded start/goal，1-5 个静态障碍，障碍靠近但不堵死 start-goal corridor；
- dynamic：至少一个 moving obstacle，优先 linear crossing，observation 包含相对位置和相对速度；
- latent_dynamic：障碍初期静止或低风险，trigger_step 或 trigger_radius 后开始运动；不能向 policy 泄露未来 trigger label。

## 6. 场景比例校准与默认圆柱体训练几何

这一节是强制要求。PPO full training 前必须通过场景比例校准。

默认训练几何必须统一使用 cylinder：

```text
static obstacle kind = cylinder
dynamic obstacle kind = cylinder
latent dynamic obstacle kind = cylinder
```

Sphere / mesh / mixed geometry 只能作为后续 eval variant，不能作为 TASK_06 默认训练场景。

训练前必须查看 NavRL 的 map scale、robot radius / safety radius、obstacle radius、obstacle spacing、obstacle count、start-goal distance、dynamic obstacle speed、robot max speed、episode length，并把具体 NavRL 路径记录到 `docs/navrl_guided_training_adjustments_task06.md`。

必须更新 `configs/task06_multiscenario_curriculum.json`，包含：

```text
training_obstacle_kind
drone_collision_radius
safety_margin
cylinder_radius_range_by_group
cylinder_height_range
obstacle_drone_radius_ratio_range
min_start_goal_clearance
min_obstacle_obstacle_clearance
min_corridor_width
dynamic_obstacle_speed_range
dynamic_to_drone_speed_ratio_range
max_episode_steps_by_group
```

建议初始比例，需在 NavRL review 后确认或调整：

```text
drone_collision_radius: 0.18 to 0.22
safety_margin: 0.15 to 0.25
static easy cylinder radius: 0.18 to 0.28
static medium cylinder radius: 0.25 to 0.40
dynamic cylinder radius: 0.20 to 0.35
latent dynamic cylinder radius: 0.20 to 0.35
cylinder height: 1.2 to 2.0
obstacle/drone radius ratio easy: 0.8 to 1.5
obstacle/drone radius ratio medium: 1.0 to 2.0
```

必须实现 `validate_task06_training_scene_scale(...)`，并在 PPO 前调用。它必须检查：

- 默认训练障碍全是 cylinder；
- radius / height 在配置范围内；
- obstacle radius 与 drone collision radius 的比例在配置范围内；
- start/goal clearance 合法；
- obstacle-obstacle spacing 合法；
- start-goal corridor 不被完全堵死；
- dynamic obstacle speed 相对 drone max speed 合理；
- episode length 足够覆盖 start-goal distance。

校验失败必须 raise `ValueError`，不得进入 PPO。

## 7. 稳定化模块

新增或更新：

```text
pirl_navrl/platforms/gym_pybullet_drones/feature_scaling.py
pirl_navrl/evaluation/reward_profiles.py
pirl_navrl/analysis/rollout_metrics.py
pirl_navrl/training/vec_env.py
pirl_navrl/training/task06_multiscenario.py
```

Reward profiles 至少包含：

```text
goal_only
static_avoidance
dynamic_avoidance
latent_risk
```

训练必须支持 DummyVecEnv、VecNormalize、separate eval env、checkpoint save/load、normalization stats save/load、random-vs-trained evaluation、NaN/divergence detection。

## 8. 俯视角 gym-pybullet GIF/video

案例可视化优先生成 top-down gym-pybullet / PyBullet video 或 GIF。

新增或更新：

```text
pirl_navrl/visualization/gif_renderer.py
scripts/render_task06_case_gif.py
```

必须显示：start、goal、drone、trajectory、cylinder footprint、dynamic obstacle path、latent trigger state、step、distance_to_goal、min_clearance、success/collision/timeout、failure_type。产物保存在 `outputs/task06/...`，不得提交。

## 9. Case selection

每个 scenario group 在 full training 后必须选择：

```text
success_case 或 best_non_success_case
representative failure_case
```

没有 true success 时必须输出：

```json
{
  "case_type": "best_non_success_case",
  "reason": "no_success_found"
}
```

Failure taxonomy 至少包含：

```text
collision_failure
timeout_failure
near_miss_failure
control_instability_failure
dynamic_late_reaction_failure
latent_trigger_failure
```

每个 failure summary 必须包含 suspected cause、NavRL reference consulted、next suggested fix。

## 10. Required scripts / configs / reports

新增或更新：

```text
scripts/train_task06_multiscenario_ppo.py
scripts/eval_task06_multiscenario.py
scripts/select_task06_cases.py
scripts/render_task06_case_gif.py
scripts/analyze_task06_rollout.py
scripts/plot_task06_multiscenario_summary.py
configs/task06_static_ppo.json
configs/task06_dynamic_ppo.json
configs/task06_latent_dynamic_ppo.json
configs/task06_case_selection.json
configs/task06_training_budget.json
configs/task06_multiscenario_curriculum.json
docs/TASK_06_TRAINING_EXECUTION_REPORT.md
```

如果 full training 未完成，新增：

```text
docs/TASK_06_BLOCKED_TRAINING_REPORT.md
```

如果只完成 smoke，新增：

```text
docs/TASK_06_SMOKE_ONLY_REPORT.md
```

## 11. Tests

新增 tests，覆盖：

```text
static/dynamic/latent scenario generation
dynamic obstacle motion over time
latent trigger before/after behavior
rollout metrics
case selector
training budget parsing and smoke_is_completion=false
scene scale validation and cylinder-only geometry
top-down renderer schema and fallback behavior
config output path safety
NavRL adjustment document coverage
```

场景比例测试必须覆盖：

```text
cylinder-only default scene passes
non-cylinder default scene fails
oversized cylinder fails
bad obstacle/drone ratio fails
clearance violation fails
corridor width violation fails
moving obstacle speed violation fails
top-down renderer schema includes scale data
```

## 12. Completion criteria

TASK_06 只有满足以下条件才算完成：

1. `pytest -q` 通过；
2. static / dynamic / latent_dynamic 三类场景可生成；
3. 默认训练几何是 cylinder-only；
4. scene-scale validation 在 PPO 前运行且默认训练场景通过；
5. 三类场景均已 full training，或对未完成项写明 blocked；
6. 任一 2k/4k/10k smoke run 不得标记为完成；
7. 每类都有 random policy eval 和 trained checkpoint eval；
8. 每类都有 success 或 best_non_success case；
9. 每类都有 representative failure case；
10. 每类 case 都有 top-down gym-pybullet GIF/video 或明确 fallback summary；
11. 每类都有 random-vs-trained summary metrics；
12. 效果差时必须写 failure taxonomy、NavRL reference 和下一步修正；
13. 不提交 outputs、checkpoints、GIF、videos、TensorBoard、wandb。

## 13. Out of scope

TASK_06 不发布正式论文结论，不接 EGO baseline，不声称复现 NavRL，不使用 NavRL checkpoint 或结果。TASK_06 要完成论文级实现前置工作：长步数训练协议、多场景训练、场景比例校准、俯视角案例回放、失败分类和 NavRL-guided iteration。