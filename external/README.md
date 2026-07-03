# 外部仓库

本目录用于本地克隆外部仓库。

推荐本地结构：

```bash
external/gym-pybullet-drones/
external/NavRL/
external/ego-planner/
```

这些目录默认被 `.gitignore` 忽略，不应直接提交。除非后续任务明确决定使用 submodule 或 vendored snapshot，否则只保留本地克隆和说明文档。

## 克隆命令

```bash
git clone https://github.com/learnsyslab/gym-pybullet-drones.git external/gym-pybullet-drones
git clone https://github.com/Zhefan-Xu/NavRL.git external/NavRL
git clone https://github.com/ZJU-FAST-Lab/ego-planner.git external/ego-planner
```

## 角色说明

### gym-pybullet-drones

`gym-pybullet-drones` 是第一阶段和早期 PIRL-NavRL 方法验证的轻量级无人机 PyBullet 底座。

### NavRL

`NavRL` 只作为长期参考架构，不作为 baseline。

参考内容包括：

- 训练链路组织
- simulator-to-policy 接口
- perception / safety / navigation 模块拆分
- deployment / ROS / Isaac Sim 路径
- 动态导航场景设计
- 参数组织和实验记录方式

禁止将 NavRL 作为当前阶段的 baseline、训练依赖或 PyBullet baseline 迁移目标。

### EGO-Planner

`ego-planner` 在第二阶段用于 official sidecar bridge spike。

第二阶段只验证：

- EGO 官方项目能否作为外部 ROS sidecar 启动
- PyBullet state / obstacle / goal 能否桥接到 EGO-Planner
- EGO 输出的 trajectory / command 能否转换为 gym-pybullet-drones 可执行的 desired velocity / action
- EGO-like PyBullet 简单静态障碍场景中是否能完成最小闭环诊断

第二阶段不声称 EGO-Planner 论文结果复现，也不直接将其作为论文级 baseline。