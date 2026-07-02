# 第三方项目说明

本仓库会引用若干外部开源项目。第一阶段不直接 vendor 它们的代码。

## gym-pybullet-drones

- 仓库：<https://github.com/learnsyslab/gym-pybullet-drones>
- 角色：第一阶段主要轻量级无人机 PyBullet 训练底座
- 说明：兼容 Gymnasium 和 Stable-Baselines3 的四旋翼仿真平台

## NavRL

- 仓库：<https://github.com/Zhefan-Xu/NavRL>
- 角色：长期参考，用于无人机动态导航、Isaac Sim 训练和 ROS 部署架构
- 第一阶段状态：仅参考，不作为训练依赖

## Stable-Baselines3

- 仓库：<https://github.com/DLR-RM/stable-baselines3>
- 角色：gym-pybullet-drones 示例中使用的强化学习训练基线/接口

## PyBullet / Bullet

- 仓库：<https://github.com/bulletphysics/bullet3>
- 角色：gym-pybullet-drones 的物理后端

## 旧仓库

旧 `pirl-nav-research` 不是第三方依赖，也不是本仓库的有效代码来源。