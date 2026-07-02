# Third-Party Notices

This repository references external open-source projects. Phase 1 does not vendor their code.

## gym-pybullet-drones

- Repository: <https://github.com/learnsyslab/gym-pybullet-drones>
- Role: primary lightweight UAV PyBullet training backbone for Phase 1
- Notes: Gymnasium and Stable-Baselines3 compatible quadrotor simulation platform.

## NavRL

- Repository: <https://github.com/Zhefan-Xu/NavRL>
- Role: long-term reference for UAV dynamic navigation, Isaac Sim training, and ROS deployment architecture
- Phase 1 status: reference only; not a training dependency

## Stable-Baselines3

- Repository: <https://github.com/DLR-RM/stable-baselines3>
- Role: RL training baseline/integration path used by gym-pybullet-drones examples

## PyBullet / Bullet

- Repository: <https://github.com/bulletphysics/bullet3>
- Role: physics backend for gym-pybullet-drones

## Prior repository

The previous `pirl-nav-research` repository is not a third-party dependency and is not an active code source for this repository.
