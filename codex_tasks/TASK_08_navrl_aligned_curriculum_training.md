# TASK_08：NavRL Code-Aligned Curriculum Training and Latent Semantic Dynamic Obstacles

## 0. 任务定位

TASK_07 没有得到足够好的训练效果。TASK_08 重新明确路线：以 NavRL 训练无人机项目为主参考对象，进行代码级对齐，在 gym-pybullet-drones / PyBullet 中做尺度适配，并加入本项目新增的 latent semantic dynamic obstacles。

TASK_08 不是从零重新设计 PPO 避障系统，而是迁移 NavRL-style navigation framework：

```text
NavRL code-level source study
+ NavRL-style observation
+ NavRL-style velocity action
+ NavRL-style reward structure
+ NavRL-style PPO / policy setup
+ NavRL-style forest curriculum
+ PyBullet-compatible scale adaptation
+ latent semantic dynamic obstacle extension
```

TASK_08 不做 formal paper result，不声称复现 NavRL，不提交 checkpoints/outputs/videos。

## 1. 必须阅读的上下文

```text
docs/08_task08_navrl_aligned_curriculum_training.md
docs/07_task07_task06_hardening.md
docs/TASK_07_COMPLETION_REPORT.md 或 docs/TASK_07_BLOCKED_REPORT.md（如果存在）
docs/navrl_guided_training_adjustments_task06.md
codex_tasks/TASK_07_task06_hardening_training_protocol.md
```

如果 TASK_07 report 不存在，必须从当前代码和 Task07 文档中提取 blocked reason，并在 Task08 report 中说明。

## 2. 核心原则

除以下差异外，能严格参考 NavRL 训练项目代码的地方应尽量严格参考：

```text
simulation backend: Isaac Sim -> gym-pybullet-drones / PyBullet
scene scale: large NavRL forest -> smaller PyBullet-compatible forest
new extension: latent semantic dynamic obstacles
training budget: large parallel training -> smaller curriculum training
```

重点参考 NavRL 代码，而不是只参考论文：

```text
state / observation representation structure
static obstacle raycast / lidar-like representation
dynamic obstacle state representation
velocity-style action semantics
safe navigation reward term structure and relative role
PPO / policy network setup
random forest curriculum
training script organization and logging pattern
safety shield interface direction for later stages
```

实现前必须先读 NavRL 代码、配置、环境、reward、observation、policy、curriculum 和 training scripts。若直接复用小段实现或配置，必须记录来源、差异、license / attribution。

## 3. Stage 0：先读 NavRL 代码，再实现

写任何核心训练代码前，先新增并完成：

```text
docs/task08_navrl_source_index.md
docs/task08_navrl_alignment_table.md
docs/TASK_08_FROM_TASK_07_FAILURE_ANALYSIS.md
```

`docs/task08_navrl_source_index.md` 必须列出：

```text
NavRL repository URL or local reference path
commit / branch / version if available
file path
function / class / config name
what it controls
whether we strictly follow it
whether we adapt it
license / attribution note
```

如果某个模块找不到 NavRL 源码，写明 `not found`，不要凭论文或记忆假装代码对齐。

`docs/task08_navrl_alignment_table.md` 必须覆盖：

```text
observation/state representation
static obstacle raycast / lidar-like representation
dynamic obstacle representation
action representation
reward structure
PPO / policy setup
forest curriculum
training script and budget
safety shield placeholder
latent semantic dynamic obstacle extension
```

表格列：

```text
Module
NavRL code file / config
NavRL design from code
Strictly referenced? yes / adapted / no
PIRL-NavRL implementation
Difference from NavRL
Reason for difference
Validation evidence
Status: candidate / validated / frozen
```

`docs/TASK_08_FROM_TASK_07_FAILURE_ANALYSIS.md` 必须说明 Task07 tried what, failed how, suspected causes, Task08 changes, and what not to repeat.

## 4. 启动前 design contracts

进入 full training 前必须完成：

```text
configs/task08_navrl_style_observation.json
docs/task08_observation_contract.md
configs/task08_navrl_aligned_reward.json
docs/task08_reward_alignment_report.md
configs/task08_navrl_forest_curriculum.json
configs/task08_training_budget.json
docs/task08_promotion_block_criteria.md
```

这些 contracts 不完成，只能 smoke，不能 full training。

## 5. Observation：实现 NavRL-style dict observation

新增：

```text
pirl_navrl/observation/navrl_style_observation.py
```

主线 schema：

```text
{
  "state": ...,
  "direction": ...,
  "lidar": ...,
  "dynamic_obstacle": ...,
  "latent_obstacle": ...
}
```

`docs/task08_observation_contract.md` 必须写明每个 field 的 shape、unit、coordinate frame、normalization、clip range、padding、mask、flatten order、NavRL source reference。

第一版建议：

```text
NavRL-style dict schema for documentation and validation
flattened vector for SB3 PPO MlpPolicy implementation
```

若使用 MultiInputPolicy 或 custom feature extractor，必须写清 NavRL 代码依据和每个分支 shape。

### 5.1 lidar / raycast

第一版建议：

```text
2D horizontal raycast
360-degree FOV unless NavRL code shows otherwise and can be adapted
static cylinders included in lidar
dynamic / latent obstacles represented in dynamic_obstacle / latent_obstacle channels
ray distance normalized to [0, 1]
missing hit = 1.0
```

### 5.2 dynamic_obstacle

至少包含：

```text
relative position
relative velocity
distance
radius or safety size
valid mask
```

必须固定 K、sorting rule、normalization、padding value、mask convention。

### 5.3 latent semantic obstacle

这是本项目相对 NavRL 的扩展。不得给 policy 未来随机触发信息。

允许：

```text
relative position
current velocity if active
is_active
semantic type or risk class
distance-to-risk-region if observable
valid mask
```

不得包含：

```text
future_activation_step
will_activate_in_n_steps
future trajectory unavailable to a real policy
```

第一版语义类别固定为：

```text
static_like_latent
crossing_latent
sudden_latent
```

每类定义 trigger_radius_range、activation_delay_range、speed_range、motion_direction_rule、risk role。

## 6. Action

Action 主线保持 velocity-style：

```text
policy outputs normalized desired velocity
adapter clips by max_speed
gym-pybullet-drones executes velocity command
```

必须记录 raw_action、clipped_action、desired_velocity、actual_velocity、tracking_error、action_clipping_fraction、altitude behavior。若 action/control tracking 不稳定，先修 action/control，不先调 reward。

## 7. Reward

新增或更新：

```text
configs/task08_navrl_aligned_reward.json
docs/task08_reward_alignment_report.md
```

Reward 结构严格参考 NavRL 代码中的 safe navigation reward：

```text
reward = progress
       + goal_success
       - collision_penalty
       - clearance_or_static_risk_penalty
       - dynamic_obstacle_risk_penalty
       - action_or_smoothness_penalty
       - timeout_penalty
       - latent_semantic_risk_penalty
```

报告必须说明 NavRL reward code term 到本项目 term 的映射、初始系数来源、哪些严格参考、哪些因 PyBullet 尺度调整、reward_terms_stats、每次系数变化原因。

只允许 evidence-based one-time scaling adaptation；如果一次调整后仍无 learning signal，写 blocked 或回到诊断模块，不继续盲调。

## 8. Forest curriculum

新增或更新：

```text
pirl_navrl/scenarios/task08_navrl_forest_curriculum.py
configs/task08_navrl_forest_curriculum.json
```

默认 levels：

```text
static_forest_easy / medium / hard
dynamic_forest_easy / medium / hard
latent_semantic_forest_easy / medium / hard
mixed_forest_target
```

`configs/task08_navrl_forest_curriculum.json` 必须给出具体数值，包括 arena size、static/dynamic/latent obstacle count、density、radius、speed、trigger/risk radius、semantic class distribution、goal distance、episode horizon。

`mixed_forest_target` 是 NavRL-style high-density target / stress test，不作为第一训练入口。

## 9. Training scripts and budget

新增：

```text
configs/task08_training_budget.json
scripts/train_task08_navrl_aligned_curriculum.py
scripts/eval_task08_navrl_aligned_policy.py
scripts/render_task08_topdown_cases.py
```

支持 `--mode smoke|train|eval|blocked` 和 `--curriculum-level ...`。

`configs/task08_training_budget.json` 必须明确 smoke_steps、debug_train_steps、full_train_steps、num_envs、num_seeds、promotion criteria、blocked criteria。

## 10. Promotion / blocked criteria

新增：

```text
docs/task08_promotion_block_criteria.md
```

最小晋级标准：

```text
heuristic mean final_distance < random mean final_distance
trained mean final_distance < random mean final_distance
trained collision rate <= random collision rate + documented tolerance
trained timeout rate not materially worse than random
reward curve is not collapsed
action clipping fraction below documented threshold
obs/lidar/dynamic/latent stats finite and non-degenerate
```

不满足时，不能进入更难 level，必须写 blocked reason 或修复对应模块。

## 11. Evaluation and replay

每个关键 level 评估 random / heuristic / trained。固定 eval seeds 和 level configs 必须写入报告。

Top-down replay 至少展示 drone trajectory、start/goal、static footprints、dynamic paths、latent semantic activation/active state、success/collision/timeout/failure type。不要提交 GIF / MP4 / outputs。

## 12. Camera and safety boundary

Task08 不做真实 RGB-D perception stack。使用 PyBullet/scenario raycast 模拟 NavRL policy 输入前的结构化中间表示。

Task08 不使用 raw RGB / RGB-D policy input，不做 CNN vision encoder。Camera 只能 diagnostic / visualization。

Task08 只保留 safety shield placeholder / identity interface：

```text
policy_output -> identity_safety_filter -> action_adapter
```

正式 NavRL-style safety shield adaptation 放到 TASK_09。

## 13. Diagnostics and reports

必须输出到 ignored `outputs/`：obs_stats、lidar_stats、dynamic_obstacle_stats、latent_obstacle_stats、reward_terms_stats、action_control_tracking、training_completion_status、eval_summary_random_heuristic_trained。

新增：

```text
docs/TASK_08_TRAINING_PROTOCOL_REPORT.md
docs/TASK_08_COMPLETION_REPORT.md
```

如果未完成：

```text
docs/TASK_08_BLOCKED_REPORT.md
```

Report 必须说明 studied NavRL code files/configs、strictly aligned items、PyBullet adaptations、latent semantic extension、Task07 failure analysis、observation stats、reward alignment, curriculum numeric levels, fixed eval seeds, random/heuristic/trained comparison, diagnostics, replay cases, whether Task09 can start.

## 14. 验收标准

TASK_08 完成时必须满足：

1. `pytest -q` 通过；
2. `docs/task08_navrl_source_index.md` 完成；
3. `docs/task08_navrl_alignment_table.md` 完成；
4. `docs/TASK_08_FROM_TASK_07_FAILURE_ANALYSIS.md` 完成；
5. `docs/task08_observation_contract.md` 完成；
6. 主线 observation 使用 NavRL-style dict：`state / direction / lidar / dynamic_obstacle`，并明确 latent extension；
7. lidar/raycast observation 有具体配置、归一化、统计诊断；
8. dynamic_obstacle features 有 K、排序、padding、mask、归一化；
9. latent semantic dynamic obstacle features 不泄露未来 trigger label；
10. semantic classes 有明确定义；
11. action 为 velocity-style，并有 tracking diagnostics；
12. reward structure 对齐 NavRL code-style safe navigation reward，并记录系数来源和调整证据；
13. forest curriculum 有具体 numeric config；
14. training budget 有具体 steps / seeds / envs / promotion / blocked criteria；
15. 不直接从 target forest 起训；
16. fixed eval seeds 和 fixed level configs 已记录；
17. random / heuristic / trained 对比完成；
18. 至少 easy static / dynamic / latent semantic levels 显示 learning signal，或写清 blocked reason；
19. 有 top-down replay 或 fallback summary；
20. 没有达到预期效果时写 blocked report，而不是继续盲调；
21. 不提交 outputs、checkpoints、GIF、MP4、TensorBoard、wandb。

## 15. 明确不做

TASK_08 不做 formal paper success-rate table、full sim-to-real experiment、real RGB-D perception stack、EGO baseline、PIRL final risk module、NavRL reproduction claim、formal NavRL benchmark reproduction。

TASK_08 完成后，如果 NavRL-aligned curriculum 能稳定学习，进入 TASK_09 safety shield、TASK_10 latent semantic risk / PIRL module、TASK_11 formal evaluation。
