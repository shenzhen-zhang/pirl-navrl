# 平台决策：第一阶段

## 结论

第一阶段选择 **gym-pybullet-drones** 作为主要轻量级无人机训练平台。

NavRL 保留为长期参考，用于理解 Isaac Sim、ROS、部署链路和完整动态导航系统设计。第一阶段不把 NavRL 作为训练依赖。

## 为什么不直接用裸 PyBullet

裸 PyBullet 是物理引擎，不是完整的无人机强化学习研究平台。

如果直接从裸 PyBullet 开始，我们需要自己补齐：环境接口、任务定义、训练接入、日志、评估和图表。这会重新走回“自研平台”的路线。

## 为什么选择 gym-pybullet-drones

选择它的原因：

- 已有 PyBullet 四旋翼仿真
- 兼容 Gymnasium
- 兼容 Stable-Baselines3
- 有内置 PID 和 RL 示例
- 比 Isaac Sim 轻
- 后续可以作为迁移到 NavRL / Isaac Sim 前的轻量物理验证平台

## 为什么第一阶段不直接用 NavRL

NavRL 更贴近长期目标，但训练栈依赖 Isaac Sim 和较重 GPU 环境。当前阶段先避免重硬件依赖，优先建立可本地运行的轻量训练底座。

## Safety-Gymnasium / OmniSafe 的位置

Safety-Gymnasium 和 OmniSafe 仍然是重要的 SafeRL benchmark 参考，但第一阶段优先考虑 UAV 物理相关性，因此选择 gym-pybullet-drones。

## 第一阶段范围

第一阶段只做：

- 外部仓库 setup
- 本地环境配置
- import 检查
- 内置示例检查
- 一个围绕 gym-pybullet-drones 的简单 PIRL-NavRL adapter / risk / shield 演示

第一阶段不做论文结果。