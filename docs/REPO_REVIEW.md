# 仓库审查记录

## 审查结论

当前仓库总体方向清晰：

1. 第一阶段以 gym-pybullet-drones 为轻量 UAV PyBullet 底座。
2. 第二阶段以 EGO-Planner official ROS sidecar bridge spike 为工程可行性验证。
3. NavRL 只作为长期参考架构，不作为 baseline。
4. 当前所有输出仍为 diagnostic，不进入论文结果。

本次审查重点是消除外部项目角色混淆、更新第二阶段任务边界、补齐 ignore 规则和第三方说明。

## 已优化内容

### 1. README

- 增加 NavRL 参考边界文档链接。
- 保留 Phase 1 / Phase 2 的分阶段说明。
- 明确 Phase 2 不是正式 baseline 对比，也不是论文结果阶段。

### 2. 项目管理规则

- 允许提前整理下一阶段任务文档，但必须标注为计划中，并说明执行前置条件。
- 明确 EGO-Planner 是 official sidecar bridge 可行性验证对象。
- 明确 NavRL 不作为 baseline，不进入 baseline matrix。

### 3. 第三方项目说明

- 增加 EGO-Planner 的角色说明。
- 重写 NavRL 的角色边界：只参考链路、结构、模块、部署和参数组织。
- 明确不 vendor 第三方源码。

### 4. 外部仓库与 ignore 规则

- `.gitignore` 增加 `external/ego-planner/`。
- 增加 ROS / sidecar 相关本地产物 ignore：`build/`、`devel/`、`install/`、`log/`、`.bag`、`.db3`、`.pcd`。

### 5. setup 脚本

- `scripts/setup_external_repos.sh` 默认只处理 Phase 1 依赖。
- 增加 `--include-ego`，用于 Phase 2 EGO-Planner sidecar 准备。
- 输出外部仓库 commit，便于完成报告记录。

### 6. Task 01

- 更新仓库地址。
- 删除容易混淆的外部技能要求。
- 增加 NavRL 不作为 baseline、不迁移为 PyBullet baseline 的边界。

### 7. NavRL 参考范围

新增 `docs/navrl_reference_scope.md`，专门说明 NavRL 可参考内容和禁止使用方式。

## 当前风险与建议

### 风险 1：Phase 2 可能引入 ROS 复杂度

第二阶段虽然允许 EGO-Planner official sidecar bridge，但它仍然是 diagnostic spike。实现时不得把 ROS 依赖扩散到 Phase 1 的主 Python 包和基础测试中。

建议：EGO bridge 代码放在 `pirl_navrl/bridges/ego_planner_bridge/`，并让基础 import 测试不依赖 ROS。

### 风险 2：EGO official bridge 可能跑不通

EGO-Planner 原生是 ROS/catkin/C++ 项目。当前 TASK_02 统一使用 Docker
Noetic 运行 official sidecar；不要再把早期接口实验作为主路线或效果证据。

建议：TASK_02 输出必须明确区分 official EGO trace、PyBullet mirror 和 future
gym-pybullet-drones baseline hook。

### 风险 3：Phase 1 diagnostic demo 不能被误读为算法结果

当前 risk / shield demo 是启发式诊断实现，只用于验证 adapter、risk scoring、shield 和 JSONL 日志链路。

建议：所有输出继续使用 `result_kind=diagnostic`，不要生成论文表格或结果图。

### 风险 4：NavRL 角色容易再次混淆

NavRL 与本项目主题接近，容易被误写成 baseline。

建议：任何后续任务如涉及 NavRL，必须引用 `docs/navrl_reference_scope.md`，并再次确认“不训练、不对比、不迁移为 PyBullet baseline”。

## 下一步建议

1. 先完成并审查 `TASK_01`。
2. 再执行 `TASK_02` 的 EGO-Planner sidecar bridge spike。
3. TASK_02 完成后做一次决策：继续 official EGO sidecar，还是回退 EGO-style Python baseline。
4. 只有在 Phase 1 / Phase 2 诊断链路清晰后，再规划正式 train/eval protocol、baseline matrix 和 ablation matrix。
