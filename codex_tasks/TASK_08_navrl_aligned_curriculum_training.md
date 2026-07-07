# TASK_08：NavRL-Aligned Curriculum Training and Latent Semantic Dynamic Obstacles

## 0. 任务定位

TASK_07 没有得到足够好的训练效果。TASK_08 重新明确路线：严格对齐 NavRL 的训练体系，在 gym-pybullet-drones / PyBullet 中做尺度适配，并加入本项目新增的 latent semantic dynamic obstacles。

TASK_08 不是从零重新设计 PPO 避障系统，而是迁移 NavRL-style navigation framework：

```text
NavRL-style observation
+ NavRL-style velocity action
+ NavRL-style reward structure
+ NavRL-style forest curriculum
+ PyBullet-compatible scale adaptation
+ latent semantic dynamic obstacle extension
```

TASK_08 不做 formal paper result，不声称复现 NavRL，不提交 checkpoints/outputs/videos。

## 1. 必须阅读的上下文

执行前必须阅读：

```text
docs/08_task08_navrl_aligned_curriculum_training.md
docs/07_task07_task06_hardening.md
docs/TASK_07_COMPLETION_REPORT.md 或 docs/TASK_07_BLOCKED_REPORT.md（如果存在）
docs/navrl_guided_training_adjustments_task06.md
codex_tasks/TASK_07_task06_hardening_training_protocol.md
```

如果 TASK_07 report 不存在，必须从当前代码和 Task07 文档中提取 blocked reason，并在 Task08 report 中说明。

## 2. 核心原则

### 2.1 严格参考 NavRL

除以下差异外，能严格参考 NavRL 的地方应尽量严格参考：

```text
simulation backend: Isaac Sim -> gym-pybullet-drones / PyBullet
scene scale: large NavRL forest -> smaller PyBullet-compatible forest
new extension: latent semantic dynamic obstacles
training budget: large parallel training -> smaller curriculum training
```

重点严格参考：

```text
state representation structure
static obstacle raycast / lidar-like representation
dynamic obstacle state representation
velocity-style action semantics
safe navigation reward structure
random forest curriculum
PPO training loop
safety shield direction for later stages
```

### 2.2 不再盲调

不要继续无边界调 reward/PPO。TASK_08 的调整必须围绕 NavRL 对齐表和诊断证据。

```text
strict NavRL reference
-> PyBullet scale adaptation
-> easy curriculum diagnostic
-> evidence-based one-time adjustment
-> freeze or blocked
```

### 2.3 不迷信训练步数

不得假设训练步数足够多就一定会好。增加训练步数只有在 observation、reward、action/control、scene distribution 和 curriculum level 都合理时才有意义。

## 3. 必须新增 NavRL 对齐表

新增：

```text
docs/task08_navrl_alignment_table.md
```

表格至少包含：

```text
Module
NavRL design
Strictly referenced? yes / adapted / no
PIRL-NavRL implementation
Difference from NavRL
Reason for difference
Validation evidence
Status: candidate / validated / frozen
```

必须覆盖：

```text
observation/state representation
static obstacle raycast / lidar-like representation
dynamic obstacle representation
action representation
reward structure
forest curriculum
PPO training setup
safety shield placeholder
latent semantic dynamic obstacle extension
```

不得只写“参考 NavRL”。必须写清楚具体参考点和适配点。

## 4. Observation：实现 NavRL-style dict observation

当前 nearest-obstacle flat observation 不能作为 Task08 主线。必须新增 NavRL-style observation adapter：

```text
pirl_navrl/observation/navrl_style_observation.py
configs/task08_navrl_style_observation.json
```

主线 observation schema：

```text
{
  "state": ...,
  "direction": ...,
  "lidar": ...,
  "dynamic_obstacle": ...,
  "latent_obstacle": ...   # optional PIRL-NavRL extension or merged into dynamic_obstacle
}
```

### 4.1 state

至少包含：

```text
velocity or normalized velocity
height or z error if relevant
previous action if available
basic motion state needed by PPO
```

### 4.2 direction

至少包含：

```text
normalized direction to goal
distance to goal or clipped distance-to-goal
```

### 4.3 lidar / raycast

实现 PyBullet-compatible raycast / lidar-like static obstacle observation。

配置必须包含：

```text
num_rays
field_of_view or angular distribution
max_range
height plane or 3D ray policy
normalization rule
missing-hit value
```

允许当前用 PyBullet raycast 或 scenario geometry raycast。不要直接实现 RGB-D camera perception stack。

### 4.4 dynamic_obstacle

实现最近 K 个动态障碍结构化输入。

每个 obstacle 至少包含：

```text
relative position
relative velocity
distance
radius or safety size
valid mask
```

配置必须包含：

```text
max_dynamic_obstacles_k
sorting rule: nearest / time-to-collision / risk score
normalization rule
padding rule
```

### 4.5 latent semantic obstacle

这是本项目扩展点。可以单独输出 `latent_obstacle`，也可并入 `dynamic_obstacle`。

不得直接泄露未来 trigger label。允许输入：

```text
relative position
current velocity if active
is_active
semantic type or risk class
distance-to-risk-region if observable
valid mask
```

## 5. Action：保持 NavRL-style velocity semantics

Action 主线保持 velocity-style：

```text
policy outputs normalized desired velocity
adapter clips by max_speed
gym-pybullet-drones executes velocity command
```

必须记录：

```text
raw_action
clipped_action
desired_velocity
actual_velocity
tracking_error
action_clipping_fraction
altitude behavior
```

如果 action/control tracking 不稳定，先修 action/control，不要先调 reward。

## 6. Reward：严格参考 NavRL structure，按 PyBullet 尺度适配

新增或更新：

```text
configs/task08_navrl_aligned_reward.json
docs/task08_reward_alignment_report.md
```

Reward 结构：

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

要求：

```text
map each NavRL reward term to PIRL-NavRL term
record initial coefficient source or rationale
write reward_terms_stats.json
explain every coefficient change
allow only evidence-based one-time scaling adaptation before freeze/block
```

禁止无限调 reward。

## 7. Forest curriculum：NavRL-style random forest

实现或更新：

```text
pirl_navrl/scenarios/task08_navrl_forest_curriculum.py
configs/task08_navrl_forest_curriculum.json
```

默认 curriculum levels：

```text
static_forest_easy
static_forest_medium
static_forest_hard

dynamic_forest_easy
dynamic_forest_medium
dynamic_forest_hard

latent_semantic_forest_easy
latent_semantic_forest_medium
latent_semantic_forest_hard

mixed_forest_target
```

课程参数：

```text
arena size
static obstacle count
static obstacle density
obstacle radius range
dynamic obstacle count
dynamic obstacle speed range
latent obstacle count
latent trigger radius or risk radius
semantic class distribution
goal distance
episode horizon
```

`mixed_forest_target` 是 NavRL-style high-density target / stress test，不得作为第一训练入口。

训练路线：

```text
static_forest_easy -> static_forest_medium -> static_forest_hard
then dynamic_forest_easy -> dynamic_forest_medium -> dynamic_forest_hard
then latent_semantic_forest_easy -> latent_semantic_forest_medium -> latent_semantic_forest_hard
then mixed_forest_target
```

## 8. Training scripts

新增：

```text
configs/task08_training_budget.json
scripts/train_task08_navrl_aligned_curriculum.py
scripts/eval_task08_navrl_aligned_policy.py
scripts/render_task08_topdown_cases.py
```

支持模式：

```text
--mode smoke
--mode train
--mode eval
--mode blocked
--curriculum-level static_forest_easy|dynamic_forest_easy|latent_semantic_forest_easy|mixed_forest_target|...
```

要求：

```text
smoke only checks dependencies and interfaces
train writes training_completion_status.json
eval uses fixed seeds and fixed level configs
blocked writes docs/TASK_08_BLOCKED_REPORT.md
no outputs/checkpoints/videos/tensorboard/wandb committed
```

## 9. Evaluation

每个关键 level 至少评估：

```text
random policy
heuristic policy
trained PPO policy
```

判断逻辑：

```text
heuristic beats random -> scene/action/observation likely feasible
trained beats random -> learning signal exists
trained approaches heuristic on easy -> training stack is usable
heuristic fails -> suspect scene/action/observation/control
heuristic succeeds but trained fails -> suspect reward/PPO/observation scaling
```

固定 eval seeds 和 level configs 必须写入报告。

## 10. Top-down replay

必须生成 PyBullet top-down replay 或 fallback summary。

Replay 至少展示：

```text
drone trajectory
start / goal
static obstacle footprints
dynamic obstacle paths
latent semantic obstacle activation / active state
success / collision / timeout / failure type
```

不要提交 GIF / MP4 / outputs。

## 11. Diagnostics

必须输出到 ignored `outputs/`：

```text
obs_stats.json
lidar_stats.json
dynamic_obstacle_stats.json
latent_obstacle_stats.json
reward_terms_stats.json
action_control_tracking.json
training_completion_status.json
eval_summary_random_heuristic_trained.json
```

报告中必须摘录关键统计，不提交原始大文件。

## 12. Reports

新增：

```text
docs/TASK_08_TRAINING_PROTOCOL_REPORT.md
docs/TASK_08_COMPLETION_REPORT.md
```

如果未完成：

```text
docs/TASK_08_BLOCKED_REPORT.md
```

Report 必须说明：

```text
what is strictly aligned with NavRL
what is adapted for PyBullet scale
how latent semantic obstacles extend NavRL
observation schema and stats
reward alignment and final coefficients
curriculum levels and fixed eval seeds
random / heuristic / trained comparison
training diagnostics
top-down replay cases
whether Task09 can start
```

## 13. 验收标准

TASK_08 完成时必须满足：

1. `pytest -q` 通过；
2. `docs/task08_navrl_alignment_table.md` 完成；
3. 主线 observation 使用 NavRL-style dict：`state / direction / lidar / dynamic_obstacle`，并明确 latent extension；
4. lidar/raycast observation 有配置、归一化、统计诊断；
5. dynamic_obstacle features 有 K、排序、padding、mask、归一化；
6. latent semantic dynamic obstacle features 不泄露未来 trigger label；
7. action 仍为 velocity-style，并有 tracking diagnostics；
8. reward structure 对齐 NavRL-style safe navigation reward，并记录系数来源和调整证据；
9. forest curriculum 包含 static / dynamic / latent semantic / mixed target；
10. 不直接从 target forest 起训；
11. fixed eval seeds 和 fixed level configs 已记录；
12. random / heuristic / trained 对比完成；
13. 至少 easy static / dynamic / latent semantic levels 显示 learning signal；
14. 训练结果有 top-down replay 或 fallback summary；
15. 如果没有达到预期效果，必须写 blocked report，而不是继续盲调；
16. 不提交 outputs、checkpoints、GIF、MP4、TensorBoard、wandb。

## 14. 明确不做

TASK_08 不做：

```text
formal paper success-rate table
full sim-to-real experiment
real RGB-D perception stack
EGO baseline
PIRL final risk module
NavRL reproduction claim
```

TASK_08 完成后，如果 NavRL-aligned curriculum 能稳定学习，进入：

```text
TASK_09: NavRL-style safety shield adaptation
TASK_10: latent semantic risk / PIRL module
TASK_11: formal evaluation protocol
```
