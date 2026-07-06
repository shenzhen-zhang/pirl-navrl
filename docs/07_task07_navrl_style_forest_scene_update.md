# TASK_07 Update：NavRL-Style Forest Scene Design

## 1. 为什么要更新

TASK_07 原设计里对 static、dynamic、latent_dynamic 场景写得偏手工：例如要求动态障碍横穿 nominal path、潜在动态障碍按精确交互触发等。

结合 NavRL 在 Isaac Sim 中的训练方式，TASK_07 的主训练场景应更简单：

```text
forest-like randomized scenes
many simple obstacles
random start and goal
simple dynamic motion
curriculum over obstacle count, density, and speed
```

因此 TASK_07 后续实现应优先采用 NavRL-style forest 场景，而不是复杂手工场景分类。

## 2. 新的核心原则

```text
Use NavRL-style forest-like randomized training scenes rather than many hand-designed special cases.
```

中文：

```text
优先采用 NavRL 风格的随机森林式训练场景，而不是大量手工设计的小场景。
```

TASK_07 仍然保留 scene-scale validation、cylinder-only、training protocol、三方对比和 top-down replay 等要求，但场景生成方式应更接近 NavRL 的训练思路。

## 3. 三类主训练场景

TASK_07 应将默认训练场景重构为三类 forest：

```text
static_forest
dynamic_forest
latent_dynamic_forest
```

可选：

```text
mixed_forest
```

### 3.1 Static forest

Static forest 是随机圆柱森林：

```text
random start / goal
random static cylinders
controlled obstacle count
controlled density
clearance constraints
reachable path check
```

训练目的：基础几何避障和 clearance 保持。

推荐 curriculum：

```text
static_forest_easy: fewer cylinders, larger free space
static_forest_medium: more cylinders, moderate density
static_forest_hard: more cylinders, narrower free space
```

### 3.2 Dynamic forest

Dynamic forest 在 static forest 基础上加入随机移动圆柱。

动态障碍不需要复杂手工 crossing rule。默认使用简单线性运动：

```text
random initial position
random horizontal velocity direction
speed range controlled by level
boundary behavior: bounce / wrap / respawn
```

训练目的：通过大量随机移动障碍和 curriculum 学习动态避障。

推荐 curriculum：

```text
dynamic_forest_easy: few moving cylinders, slow speed
dynamic_forest_medium: more moving cylinders, medium speed
dynamic_forest_hard: more moving cylinders, faster speed
```

### 3.3 Latent dynamic forest

Latent dynamic forest 不需要复杂 intent rule。它可以被实现为：

```text
initially inactive dynamic obstacles
```

障碍物 reset 后先静止，满足 activation rule 后变成普通 moving cylinder。

默认 activation：

```text
if distance(robot, latent_obstacle) < trigger_radius:
    active = true
elif step >= random_activation_step:
    active = true
```

要求：

```text
distance trigger is the main trigger
random delay trigger is only secondary diversity / fallback
after activation, obstacle uses simple sampled linear motion
future trigger label is not exposed directly to policy
ignore or reject samples where latent motion is completely irrelevant
```

推荐比例：

```text
70% distance-trigger latent obstacles
30% random-delay latent obstacles
```

推荐 curriculum：

```text
latent_forest_easy: few latent cylinders, larger trigger radius, slow speed
latent_forest_medium: more latent cylinders, smaller trigger radius, medium speed
latent_forest_hard: more latent cylinders, shorter reaction window, faster speed
```

## 4. 场景验证应改为 forest validation

原本的 `validate_avoidance_interaction(...)` 可以保留，但 TASK_07 主线更推荐实现：

```text
validate_forest_training_scene(...)
```

至少检查：

```text
start and goal are valid
start and goal are not inside obstacle margins
scene is not fully blocked
coarse reachable path exists or heuristic can make progress
dynamic obstacles move inside relevant arena regions
latent obstacles can activate by distance or delay
activated latent motion is not completely irrelevant
random / heuristic rollouts produce finite metrics
```

不要求每个动态障碍都精确横穿 start-goal path；只要求整体随机场景有训练意义、可达、有避障压力。

## 5. 推荐配置字段

建议新增或更新：

```text
configs/task07_forest_curriculum.json
```

包含：

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

所有默认训练障碍仍然必须是 cylinder。

## 6. 对 Codex 的执行要求

Codex 执行 TASK_07 时必须同时满足：

```text
docs/07_task07_task06_hardening.md
codex_tasks/TASK_07_task06_hardening_training_protocol.md
docs/07_task07_navrl_style_forest_scene_update.md
```

如果三者冲突，以本文件的 NavRL-style forest 场景原则为准。

## 7. 仍然保留的硬性要求

本更新不取消以下要求：

```text
cylinder-only default training geometry
scene-scale validation before PPO
full / smoke / blocked training protocol
random / heuristic / trained comparison
PyBullet top-down replay or fallback
TASK_06 gate-easy is diagnostic only
no outputs/checkpoints/GIF/MP4 committed
pytest -q passes
```

## 8. 简短结论

TASK_07 的场景目标应从：

```text
many carefully hand-designed obstacle interactions
```

调整为：

```text
NavRL-style randomized forest scenes with simple obstacle rules and curriculum
```

这是更简单、更稳定、也更接近 NavRL 成功训练经验的路线。