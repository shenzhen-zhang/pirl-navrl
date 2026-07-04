"""Skeleton adapters for future gym-pybullet-drones integration."""

from pirl_navrl.platforms.gym_pybullet_drones.action_adapter import (
    adapt_desired_velocity,
    clip_desired_velocity,
    desired_velocity_to_action,
    normalize_desired_velocity,
)
from pirl_navrl.platforms.gym_pybullet_drones.rl_env import Task04GymPybulletDronesRLEnv
from pirl_navrl.platforms.gym_pybullet_drones.simple_adapter import GymPybulletDronesSimpleAdapter

__all__ = [
    "GymPybulletDronesSimpleAdapter",
    "Task04GymPybulletDronesRLEnv",
    "adapt_desired_velocity",
    "clip_desired_velocity",
    "desired_velocity_to_action",
    "normalize_desired_velocity",
]
