# PIRL-NavRL

PIRL-NavRL 是一个新的、干净的研究仓库，用于推进 **基于预测意图-风险的无人机局部导航强化学习**。

本仓库取代旧的 `pirl-nav-research` 作为后续主线。旧仓库里的轻量仿真器、手写策略、合成训练器和审查产物不再作为本仓库的有效实现代码。

## 当前平台决策

第一阶段使用 **gym-pybullet-drones** 作为轻量级无人机 PyBullet 训练底座。

- 第一阶段主底座：<https://github.com/learnsyslab/gym-pybullet-drones>
- 长期参考仓库：<https://github.com/Zhefan-Xu/NavRL>
- 当前训练依赖：gym-pybullet-drones + Stable-Baselines3 + PyBullet
- 当前不引入：Isaac Sim、ROS1/ROS2、NavRL 训练栈

## 第一阶段目标

第一阶段是环境配置和集成验证阶段，不是论文结果阶段。

目标：

1. 拉取并记录 NavRL 和 gym-pybullet-drones。
2. 配置可复现的本地 gym-pybullet-drones 环境。
3. 验证 gym-pybullet-drones 自带示例。
4. 在 gym-pybullet-drones 集成层上实现一个简单的 PIRL-NavRL adapter / risk / shield 演示。
5. 先建立项目管理、产物管理和实验管理规则，再进入正式实验。

## 第一阶段边界

允许：

- 在 `external/` 下本地克隆外部仓库
- 围绕 gym-pybullet-drones 写 adapter / wrapper
- 生成小型 JSON/JSONL 诊断结果
- 写导入检查、smoke test 和简单演示脚本
- 把 NavRL 作为长期参考架构记录下来

禁止：

- 复制旧 `pirl-nav-research` 的有效实现代码
- 从零写新的仿真器
- 使用 Isaac Sim 训练
- 尝试 ROS 部署
- 提交 checkpoint、视频、GIF、TensorBoard、wandb 或其他大产物
- 声称论文级结果

## 项目结构原则

仓库结构保持简单：

```text
pirl-navrl/
  README.md
  THIRD_PARTY_NOTICES.md
  docs/
  external/
  codex_tasks/
```

第一阶段只放文档和任务文件。源码、脚本、配置和测试由 `TASK_01` 执行时再按需创建，避免提前堆目录。

## 项目管理

项目管理规则见 [`docs/PROJECT_MANAGEMENT.md`](docs/PROJECT_MANAGEMENT.md)。

第一阶段任务见 [`codex_tasks/TASK_01_gym_pybullet_drones_phase1_setup_and_demo.md`](codex_tasks/TASK_01_gym_pybullet_drones_phase1_setup_and_demo.md)。
