# TASK_07：Task06 Hardening for Paper-Ready Multi-Scenario Training

## 0. 任务定位

TASK_07 是 TASK_06 的集中修复和强化阶段。

TASK_06 已完成 multi-scenario PPO diagnostic prototype，但审查发现它还不能直接作为后续论文级训练基础。TASK_07 的目标是修复 TASK_06 中的 geometry、scene scale、scenario interaction、training protocol、heuristic sanity、top-down PyBullet replay 和 reporting 问题。

TASK_07 不进入 PIRL intent/risk module，不做 EGO baseline，不做正式论文实验，不报告 formal success rate，不声称复现 NavRL，不使用 NavRL checkpoint 或结果，不提交 outputs/checkpoints/GIF/MP4/wandb/TensorBoard。

## 1. 必须阅读的上下文

执行前请先阅读：

```text
docs/07_task07_task06_hardening.md
docs/TASK_06_COMPLETION_REPORT.md
docs/navrl_guided_training_adjustments_task06.md
codex_tasks/TASK_06_navrl_guided_multiscenario_ppo_case_replay.md
```

TASK_06 的 gate-easy 结果只能作为 diagnostic observation，不能作为 formal result。

## 2. Cylinder-only default training geometry

必须修复 TASK_06 默认训练 geometry。

要求：

- 修改 `pirl_navrl/scenarios/dynamic_curriculum.py`；
- static / dynamic / latent_dynamic 默认训练障碍全部为 `cylinder`；
- sphere / mesh / mixed-shape 只能作为 future eval variant；
- 不允许默认训练场景继续使用 sphere；
- 更新 tests，断言所有默认训练 obstacle kind == `cylinder`。

## 3. Scene-scale validation

新增训练前 scene-scale validation：

```text
validate_task07_training_scene_scale(...)
```

可以兼容提供：

```text
validate_task06_training_scene_scale(...)
```

必须在 PPO training 前调用。失败时必须 `raise ValueError`，不得进入 PPO。

至少检查：

```text
obstacle/drone radius ratio
start/goal clearance
obstacle-obstacle spacing
corridor passability
dynamic obstacle speed ratio
cylinder height covers flight altitude
max_steps reachability
```

更新 `configs/task06_multiscenario_curriculum.json` 或新增 `configs/task07_multiscenario_curriculum.json`，包含明确 scene-scale fields：

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

所有 scale 设置都要参考 NavRL，并记录具体 NavRL 文件/config 到 `docs/navrl_guided_training_adjustments_task06.md` 或新增 `docs/navrl_guided_training_adjustments_task07.md`。

## 4. Interaction-driven scenario design

场景必须体现避障交互，而不是只是存在障碍物。

新增：

```text
validate_avoidance_interaction(...)
```

### Static

要求：

- cylinder near nominal start-goal corridor；
- straight-line / goal-tracking policy has low-clearance or collision risk；
- still passable by a clearance-aware policy；
- obstacle 不允许离路径太远以至于不影响导航。

### Dynamic

要求：

- moving cylinder crosses the nominal drone corridor；
- crossing time overlaps expected drone arrival time；
- straight-line policy has near-miss or collision risk；
- reactive heuristic can improve clearance or avoid collision。

### Latent dynamic

潜在动态默认采用距离触发：

```text
trigger_mode = distance_to_drone
trigger_radius configurable
fallback_trigger_step optional
```

要求：

- obstacle initially stationary or low-risk；
- when drone enters trigger_radius, obstacle begins crossing the corridor；
- future trigger label must not be exposed directly to the policy；
- eval can classify latent_trigger_failure。

## 5. Training protocol hardening

新增或修复训练脚本，使其支持：

```text
--mode full
--mode smoke
--scenario-group static|dynamic|latent_dynamic|mixed_static_dynamic
```

要求：

- 默认 `--mode full`；
- smoke 只能显式指定；
- smoke checkpoint 不得用于 final case selection；
- 每个 run 必须写 `training_completion_status.json`；
- full 未完成时必须写 blocked report；
- gate-easy 或 smoke 结果不得冒充完整 Task 7 completion。

可以新增：

```text
configs/task07_training_budget.json
scripts/train_task07_hardened_multiscenario.py
```

也可以扩展现有 TASK_06 训练脚本，但必须保持 TASK_06 历史结果可解释。

## 6. Random / heuristic / trained 三方对比

新增 heuristic sanity policies：

```text
goal_tracking_policy
static_clearance_heuristic_policy
dynamic_reactive_heuristic_policy
latent_reactive_heuristic_policy
```

每个 scenario group 必须评估：

```text
random policy
heuristic sanity policy
trained PPO policy
```

解释规则：

```text
heuristic fails -> suspect scene / control / reward / observation
heuristic succeeds but PPO fails -> suspect PPO / reward / observation / training config
trained beats heuristic -> policy may be learning useful behavior
```

heuristic 不是 formal baseline，不得作为论文 baseline 报告。

## 7. Top-down PyBullet renderer

当前 Matplotlib JSONL replay 可保留为 fallback，但 TASK_07 必须新增真正 PyBullet top-down renderer。

新增：

```text
pirl_navrl/visualization/topdown_pybullet_renderer.py
scripts/render_task07_topdown_pybullet_case.py
```

要求：

- camera fixed above arena and points downward；
- show drone, start, goal, cylinder footprint, trajectory；
- show dynamic obstacle path；
- show latent trigger state when relevant；
- show success/collision/timeout/failure_type；
- output GIF or MP4 under ignored outputs；
- if rendering fails, write fallback summary JSON with reason。

## 8. Diagnostics and reports

新增或更新：

```text
docs/TASK_07_TRAINING_PROTOCOL_REPORT.md
docs/TASK_07_COMPLETION_REPORT.md
```

如果 full training 未完成，新增：

```text
docs/TASK_07_BLOCKED_REPORT.md
```

Reports 必须说明：

- TASK_06 gate-easy result 是 diagnostic，不是 formal result；
- cylinder-only 是否完成；
- scene-scale validation 是否在 PPO 前执行；
- interaction validation 是否证明三类场景确实体现避障；
- 每类场景 random / heuristic / trained 对比；
- top-down PyBullet replay 是否生成；
- 哪些内容仍 blocked。

本地 diagnostics 建议输出到 ignored `outputs/`：

```text
obs_stats.json
reward_terms_stats.json
action_stats.json
control_tracking_error.json
distance_curve.json
reachability_report.json
interaction_validation_report.json
```

## 9. Tests

新增或更新 tests，至少覆盖：

```text
cylinder-only default training scenes
non-cylinder default scene rejected
scene-scale validation pass/fail
corridor passability validation
dynamic crossing interaction validation
latent distance-trigger activation
straight-line policy risky check
heuristic policy finite action and safer-than-straight check
training mode full/smoke status schema
top-down PyBullet renderer fallback schema
report templates contain required fields
```

## 10. 验收标准

TASK_07 完成时必须满足：

1. `pytest -q` 通过；
2. static / dynamic / latent_dynamic 默认训练障碍全部为 cylinder；
3. scene-scale validation 在 PPO 前执行；
4. static / dynamic / latent_dynamic 都通过 scene-scale validation；
5. static / dynamic / latent_dynamic 都通过 avoidance interaction validation；
6. latent_dynamic 默认采用 distance-to-drone trigger，fixed step trigger 只能作为 fallback；
7. train script 支持 full / smoke / blocked 状态；
8. smoke 不会被标记为 completed；
9. 每类场景都有 random / heuristic / trained eval summary；
10. 每类都有 success 或 best_non_success case；
11. 每类都有 representative failure case；
12. 每类有 top-down PyBullet GIF/video 或明确 fallback summary；
13. TASK_06 gate-easy 结果被明确标记为 diagnostic，不是 formal result；
14. 不提交 outputs、checkpoints、GIF、MP4、TensorBoard、wandb。

## 11. 明确不做

TASK_07 不做：

```text
PIRL intent/risk module
EGO baseline
formal paper success-rate table
multi-seed paper benchmark
NavRL reproduction claim
checkpoint/result artifact submission
```

TASK_07 完成后，再决定是否进入 PIRL/risk/intention module prototype 或 frozen evaluation protocol。