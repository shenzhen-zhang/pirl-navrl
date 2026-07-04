# TASK_05：NavRL-Informed PPO Debug Training and Visualization

## 0. 任务定位

TASK_05 是第一次训练链路验证阶段，但仍然不是正式论文实验阶段。

本任务不能直接开始写 PPO 训练脚本。必须先仔细研究 NavRL 代码，再检查 PIRL-NavRL 当前训练前置工作是否完备。有缺口先优化，最后才开始最小 PPO debug training，并提供可视化让用户看到训练前后策略效果。

本任务不是正式 baseline，不做多 seed benchmark，不报告正式 success rate，不提交训练产物。

## 1. 执行顺序

必须按下面顺序执行：

```text
1. NavRL code study
2. training readiness audit
3. readiness fix / optimization
4. randomized curriculum scenario generator
5. PPO debug training pipeline
6. eval rollout
7. visualization
```

## 2. 第一部分：NavRL code study

在开始 TASK_05 实现之前，必须先进行 NavRL code study。

请仔细阅读 `external/NavRL` 或本地 NavRL clone 中与导航训练相关的代码。

重点查看：

- repository structure；
- 场景大小；
- 环境边界；
- start / goal 采样方式；
- 静态 / 动态障碍物生成；
- obstacle 参数范围；
- observation schema；
- action schema；
- reward shaping；
- collision / success / timeout 判断；
- episode length；
- curriculum / difficulty 组织；
- PPO / RL 训练参数；
- runner / trainer / evaluator；
- checkpoint / logging / config 管理；
- visualization / debug 工具；
- ROS / deployment 边界。

允许：

- 参考 NavRL 的模块设计、参数范围、helper、schema、adapter pattern；
- 复制小段通用 helper 或参数组织方式；
- 适配到 PIRL-NavRL 自己的命名、类型、平台和测试。

禁止：

- 整包迁移 NavRL；
- 把 NavRL 当 baseline；
- 声称复现 NavRL；
- 使用 NavRL 结果；
- 复制代码但不适配、不测试、不注明来源；
- 引入许可证不清楚的代码。

必须新增：

```text
docs/navrl_code_review_for_task05.md
```

该文档必须包含：

1. NavRL repo structure summary；
2. NavRL scenario / obstacle / start-goal 设计；
3. NavRL observation / action / reward 设计；
4. NavRL training / runner / logging / checkpoint 设计；
5. 可被 PIRL-NavRL 采纳的设计；
6. 暂不采纳的设计；
7. attribution / license 注意事项；
8. TASK_05 具体采用哪些 NavRL-informed 设计。

## 3. 第二部分：training readiness audit

NavRL code study 完成后，检查当前 PIRL-NavRL 的 TASK_03 / TASK_04 是否已经具备训练条件。

必须检查：

- `Task04GymPybulletDronesRLEnv` 是否适合 SB3；
- observation 是否 fixed shape / finite；
- action 是否 normalized `Box([-1, 1], shape=(3,))`；
- reward 是否 finite 且分项可解释；
- `terminated = success or collision`；
- `truncated = timeout`；
- `platform_terminated` / `platform_truncated` 是否只作为 info；
- collision / success / timeout 语义是否稳定；
- reset 是否支持 seed；
- 是否需要 randomized scenario generator；
- 障碍物尺寸是否适合 Crazyflie；
- logs / checkpoints 是否不会提交仓库；
- eval rollout 是否能复现；
- GUI / trace replay 是否能显示训练效果。

必须新增：

```text
docs/task05_training_readiness_review.md
```

如果发现需要优化的地方，先修复，再开始训练 pipeline。

## 4. 第三部分：randomized curriculum scenario generator

采用 NavRL-informed 场景设计：

```text
固定场景大小 + seed 控制随机 start/goal/obstacles + curriculum 控制难度
```

新增：

```text
pirl_navrl/scenarios/curriculum.py
configs/task05_curriculum_levels.json
```

实现：

- `CurriculumLevelConfig`
- `ScenarioRandomizationConfig`
- `make_curriculum_scenario(level_id: str, seed: int) -> ScenarioConfig`
- `sample_start_goal(...)`
- `sample_static_obstacles(...)`
- `validate_scenario(...)`

第一版固定 arena：

```text
x: [-5, 5]
y: [-5, 5]
z: [0.3, 3.0]
```

第一版支持 3 个 level：

1. `level_0_no_obstacle_short`
2. `level_1_no_obstacle_long`
3. `level_2_static_obstacle_easy`

要求：

- 所有随机由 seed 控制；
- 同一个 seed 生成完全一致场景；
- 不同 seed 应产生可观察差异；
- start / goal 不在障碍物中；
- obstacle 不离 start / goal 过近；
- obstacles 不明显重叠；
- level 0 无障碍；
- level 2 有静态障碍。

暂不做动态障碍训练。动态障碍、sudden motion obstacle、risk-aware scenario 留给后续阶段。

## 5. 第四部分：PPO debug training pipeline

新增：

```text
pirl_navrl/training/__init__.py
pirl_navrl/training/sb3_ppo_debug.py
pirl_navrl/training/eval.py
pirl_navrl/training/callbacks.py
scripts/train_task05_ppo_debug.py
scripts/eval_task05_ppo_debug.py
scripts/plot_task05_training_curves.py
configs/task05_ppo_debug_train.json
```

训练要求：

- 使用 Stable-Baselines3 PPO；
- 使用 `Task04GymPybulletDronesRLEnv`；
- 默认 curriculum level 使用 `level_0_no_obstacle_short`；
- total_timesteps 很小，例如 10k 到 50k；
- 只做 debug training；
- 不做正式结果；
- 不做多 seed benchmark；
- 不调参追求效果；
- checkpoint / logs 写入 `outputs/task05/...`；
- `outputs/` 不提交仓库。

建议 PPO 初始参数：

```text
policy: MlpPolicy
n_steps: 512 or 1024
batch_size: 64
learning_rate: 3e-4
gamma: 0.99
gae_lambda: 0.95
ent_coef: 0.0
clip_range: 0.2
verbose: 1
```

这些参数只是 debug 初值，不是论文最终配置。

## 6. 第五部分：eval + visualization

必须实现：

1. 训练前 random / untrained policy eval；
2. 训练后 checkpoint eval；
3. 生成 JSONL rollout；
4. 可用 GUI 看到训练后策略效果；
5. 可用 trace replay 回放；
6. 可选生成训练曲线 PNG。

命令示例：

```bash
python3 scripts/train_task05_ppo_debug.py --config configs/task05_ppo_debug_train.json
python3 scripts/eval_task05_ppo_debug.py --checkpoint outputs/task05/<run_id>/checkpoints/final_model.zip --gui
python3 scripts/eval_task05_ppo_debug.py --checkpoint outputs/task05/<run_id>/checkpoints/final_model.zip --output outputs/task05/<run_id>/eval/eval_rollout.jsonl
python3 scripts/view_task03_rollout.py --trace outputs/task05/<run_id>/eval/eval_rollout.jsonl
python3 scripts/plot_task05_training_curves.py --run-dir outputs/task05/<run_id>
```

可视化至少覆盖：

- drone position；
- start / goal；
- obstacles；
- trajectory；
- action / desired velocity；
- collision / success / timeout；
- training curve：episode reward、episode length、eval final distance、termination summary。

训练曲线、checkpoint、TensorBoard、videos、large JSONL 只能保存在 `outputs/`，不得提交仓库。

## 7. 文档要求

新增：

```text
docs/05_task05_navrl_informed_ppo_debug_training.md
docs/navrl_code_review_for_task05.md
docs/task05_training_readiness_review.md
```

文档必须说明：

- TASK_05 先研究 NavRL；
- 采用了哪些 NavRL-informed 设计；
- 当前训练只是 debug training；
- 不做 baseline；
- 不报告正式 success rate；
- checkpoint/log/video/plot 不提交仓库；
- 如何可视化训练效果；
- TASK_06 如何进入 PIRL intent-risk module。

## 8. 测试要求

新增 tests：

### 8.1 `tests/test_task05_curriculum_scenarios.py`

验证：

- 同 seed 可复现；
- 不同 seed 有变化；
- start / goal 合法；
- obstacle 不与 start / goal 重叠；
- level 0 无障碍；
- level 2 有静态障碍。

### 8.2 `tests/test_task05_training_config.py`

验证：

- config 字段完整；
- `output_type = diagnostic_training`；
- outputs 路径不在 git-tracked result path。

### 8.3 `tests/test_task05_eval_schema.py`

验证：

- eval rollout JSONL 字段兼容 `RolloutJsonlWriter`；
- `policy_id` / `checkpoint_path` / `curriculum_level` 写入 metadata。

### 8.4 `tests/test_task05_navrl_review_doc_exists.py`

验证：

- `docs/navrl_code_review_for_task05.md` 存在；
- 包含 scenario / observation / action / reward / training 参数总结。

## 9. 明确不做

TASK_05 禁止：

- 不做正式 baseline；
- 不做多 seed benchmark；
- 不报告正式 success rate；
- 不接 EGO baseline；
- 不实现 PIRL risk / intent module；
- 不做动态障碍正式训练；
- 不提交 outputs、checkpoints、videos、TensorBoard、wandb。

## 10. 验收标准

完成后必须满足：

1. `pytest -q` 通过；
2. `docs/navrl_code_review_for_task05.md` 已完成；
3. `docs/task05_training_readiness_review.md` 已完成；
4. curriculum scenario generator 可用；
5. PPO debug training script 可运行；
6. eval script 可运行；
7. GUI 或 trace replay 能看到训练后策略效果；
8. 不提交 outputs、checkpoints、videos、TensorBoard、wandb；
9. README / docs 明确 TASK_05 不是正式论文实验。