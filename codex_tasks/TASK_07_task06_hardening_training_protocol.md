# TASK_07：Task06 Hardening with NavRL-Style Forest Training Scenes

## 0. 任务定位

TASK_07 是 TASK_06 的集中修复和强化阶段。TASK_07 的目标是修复 TASK_06 中的 geometry、scene scale、forest scenario generation、validated parameter convergence、training protocol、heuristic sanity、top-down PyBullet replay 和 reporting 问题。

TASK_07 不进入 PIRL intent/risk module，不做 EGO baseline，不做正式论文实验，不报告 formal success rate，不声称复现 NavRL，不使用 NavRL checkpoint 或结果，不提交 outputs/checkpoints/GIF/MP4/wandb/TensorBoard。

## 1. 必须阅读的上下文

```text
docs/07_task07_task06_hardening.md
docs/TASK_06_COMPLETION_REPORT.md
docs/navrl_guided_training_adjustments_task06.md
codex_tasks/TASK_06_navrl_guided_multiscenario_ppo_case_replay.md
```

TASK_06 的 gate-easy 结果只能作为 diagnostic observation，不能作为 formal result。

## 2. 核心原则

TASK_07 必须多参考 NavRL，减少自由变量，但不得盲目冻结。

```text
NavRL-inspired candidate defaults
-> diagnostic validation
-> validated defaults
-> frozen defaults
-> curriculum training
-> evidence-based unfreeze if needed
```

默认场景优先实现 NavRL-style forest scenes：

```text
static_forest
dynamic_forest
latent_dynamic_forest
mixed_forest optional
```

核心场景原则：

```text
simple forest-like randomized scenes + obstacle-count curriculum + speed/density curriculum
```

核心参数原则：

```text
frozen means default-stable, not immutable
parameters may be frozen only after validation evidence is recorded
later training changes curriculum parameters first
unfreeze PPO / reward / observation / action only with documented diagnosis
```

不要做一堆复杂手工小场景，也不要在没有诊断证据时随意改 PPO / reward / observation。

## 3. Cylinder-only default training geometry

- 默认训练障碍全部为 `cylinder`；
- static_forest / dynamic_forest / latent_dynamic_forest 中所有默认 obstacle kind == `cylinder`；
- sphere / mesh / mixed-shape 只能作为 future eval variant；
- tests 必须断言所有默认训练 obstacle kind == `cylinder`。

## 4. Forest curriculum implementation

新增或更新：

```text
pirl_navrl/scenarios/forest_curriculum.py
configs/task07_forest_curriculum.json
```

配置至少包含：

```text
arena_size
training_obstacle_kind
static_obstacle_count_by_level
dynamic_obstacle_count_by_level
latent_obstacle_count_by_level
cylinder_radius_range_by_level
cylinder_height_range
dynamic_speed_range_by_level
latent_trigger_radius_range_by_level
latent_random_activation_step_range_by_level
boundary_behavior
max_episode_steps_by_level
```

## 5. Static forest

实现随机静态圆柱森林：

```text
random start / goal
random static cylinders
controlled obstacle count and density
clearance constraints
reachability check
```

不要求手工设计 path-near / gate / cluster 类型，但场景不能完全无避障意义，也不能完全堵死。

## 6. Dynamic forest

在 static forest 基础上加入 moving cylinders。

默认动态规则：

```text
random initial position
random horizontal velocity direction
speed range controlled by level
boundary behavior: bounce / wrap / respawn
```

不要求每个 moving obstacle 都精确穿越 start-goal line。

## 7. Latent dynamic forest

潜在动态障碍实现为 initially inactive dynamic cylinders。

默认 activation：

```text
if distance(robot, latent_obstacle) < trigger_radius:
    active = true
elif step >= random_activation_step:
    active = true
```

要求：

```text
distance trigger is primary
random delay trigger is secondary or fallback
after activation, obstacle uses simple sampled linear motion
future trigger label is not exposed directly to policy
reject samples where activation is completely irrelevant
```

推荐比例：

```text
70% distance-trigger latent obstacles
30% random-delay latent obstacles
```

## 8. Scene-scale validation

新增训练前 validation：

```text
validate_task07_training_scene_scale(...)
```

必须在 PPO training 前调用。失败时必须 `raise ValueError`，不得进入 PPO。

至少检查：

```text
all default obstacles are cylinders
obstacle/drone radius ratio
start/goal clearance
obstacle-obstacle spacing
free-space density is not impossible
dynamic obstacle speed ratio
cylinder height covers flight altitude
max_steps reachability
```

所有 scale 设置都要参考 NavRL，并记录具体 NavRL 文件/config。

## 9. Forest validation

新增：

```text
validate_forest_training_scene(...)
```

至少检查：

```text
start and goal valid
not inside obstacle margins
not fully blocked
coarse reachable path exists or heuristic can make progress
dynamic obstacles move in relevant arena region
latent obstacles can activate by distance or delay
activated latent motion is not completely irrelevant
rollout metrics are finite
```

## 10. Parameter convergence, validation, and evidence-based freeze policy

新增：

```text
docs/task07_parameter_freeze_matrix.md
docs/task07_parameter_change_log.md
configs/task07_default_ppo.json
configs/task07_default_reward.json
configs/task07_default_observation.json
```

`docs/task07_parameter_freeze_matrix.md` 必须包含：

```text
Parameter
Category: system / training / curriculum
Status: candidate / validated / frozen
Default value
Validation evidence
NavRL reference
Can change after freeze?
Unfreeze condition
Change log path
```

状态含义：

```text
candidate: candidate default, may be revised during Task07 validation
validated: passed diagnostic checks, but not final frozen yet
frozen: passed freeze gate; default-stable unless evidence-based unfreeze is documented
```

不得把未经验证的参数直接标记为 frozen。

冻结前必须记录验证证据：

```text
observation: finite stats, non-constant key features, usable lidar/dynamic_obstacle features
reward: finite terms, no unexpected dominance, progress and clearance terms behave reasonably
action/control: desired and actual motion are consistent enough, clipping not persistently saturated
PPO: no exploding loss, no immediate entropy collapse, 2-3 seeds do not fully collapse
```

主线 observation 应优先使用 NavRL-style dict observation：

```text
state
lidar
direction
dynamic_obstacle
```

flat observation 只能作为 debug fallback。

freeze gate：

```text
static_forest_easy shows stable learning effect
dynamic_forest_easy shows stable learning effect
latent_dynamic_forest_easy shows stable learning effect
heuristic policy clearly beats random
trained policy is not clearly worse than heuristic and should beat random
reward/obs/action diagnostics show no NaN, saturation, or scale anomaly
2-3 seeds do not fully collapse under the same default stack
top-down replay behavior is reasonable
```

解冻规则：冻结后不是永远不能改，但必须通过 failure diagnosis 和 change log 解冻。每次解冻必须记录 old value、new value、evidence、NavRL reference、expected effect、validation result。

## 11. Training protocol hardening

训练脚本必须支持：

```text
--mode full
--mode smoke
--scenario-group static_forest|dynamic_forest|latent_dynamic_forest|mixed_forest
```

要求：

- 默认 `--mode full`；
- smoke 只能显式指定；
- smoke checkpoint 不得用于 final case selection；
- 每个 run 必须写 `training_completion_status.json`；
- full 未完成时必须写 blocked report；
- gate-easy 或 smoke 结果不得冒充完整 Task 7 completion。

## 12. Random / heuristic / trained 三方对比

新增 heuristic sanity policies：

```text
goal_tracking_policy
static_clearance_heuristic_policy
dynamic_reactive_heuristic_policy
latent_reactive_heuristic_policy
```

每个 scenario group 必须评估 random / heuristic / trained。

## 13. Top-down PyBullet renderer

新增：

```text
pirl_navrl/visualization/topdown_pybullet_renderer.py
scripts/render_task07_topdown_pybullet_case.py
```

要求 top-down replay 显示 drone、start、goal、cylinder footprint、trajectory、dynamic path、latent activation state、success/collision/timeout/failure_type。Matplotlib replay 只能作为 fallback。

## 14. Diagnostics and reports

新增或更新：

```text
docs/TASK_07_TRAINING_PROTOCOL_REPORT.md
docs/TASK_07_COMPLETION_REPORT.md
docs/TASK_07_BLOCKED_REPORT.md  # only if blocked
```

Reports 必须说明：NavRL-style forest 设计、forest validation、parameter freeze matrix、默认 PPO/reward/observation 是否经过验证后冻结、是否有解冻记录、三方对比、top-down replay、blocked items。

## 15. Tests

新增或更新 tests，至少覆盖：

```text
cylinder-only default training scenes
scene-scale validation pass/fail
forest scene validation pass/fail
dynamic obstacle motion and boundary behavior
latent distance-trigger activation
latent random-delay activation
heuristic policy finite action and progress check
training mode full/smoke status schema
top-down PyBullet renderer fallback schema
parameter freeze matrix schema
parameter status candidate/validated/frozen schema
parameter change log schema
default PPO / reward / observation config exists
report templates contain required fields
```

## 16. 验收标准

TASK_07 完成时必须满足：

1. `pytest -q` 通过；
2. 三类 forest 默认训练障碍全部为 cylinder；
3. scene-scale validation 在 PPO 前执行；
4. 三类 forest 场景都通过 scene-scale / forest validation；
5. latent_dynamic_forest 支持 distance-to-drone trigger 和可选 random-delay trigger；
6. train script 支持 full / smoke / blocked；
7. 每类场景都有 random / heuristic / trained eval summary；
8. 每类都有 success 或 best_non_success case；
9. 每类都有 representative failure case；
10. 每类有 top-down PyBullet GIF/video 或明确 fallback summary；
11. parameter freeze matrix 完成，并明确 system / training / curriculum 以及 candidate / validated / frozen 状态；
12. 默认 PPO / reward / observation 配置存在，并说明 NavRL 参考和验证证据；
13. frozen 参数不能没有 validation evidence；
14. 如果发生解冻，必须有 parameter change log 和 failure diagnosis；
15. TASK_06 gate-easy 结果被明确标记为 diagnostic，不是 formal result；
16. 不提交 outputs、checkpoints、GIF、MP4、TensorBoard、wandb。

## 17. 明确不做

TASK_07 不做 PIRL intent/risk module、EGO baseline、formal paper table、multi-seed paper benchmark、NavRL reproduction claim、checkpoint/result artifact submission。