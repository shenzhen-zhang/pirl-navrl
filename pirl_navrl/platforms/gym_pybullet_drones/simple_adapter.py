"""TASK_04 gym-pybullet-drones velocity adapter."""

from __future__ import annotations

from typing import Any

import numpy as np
import pybullet as p

from pirl_navrl.platforms.gym_pybullet_drones.action_adapter import adapt_desired_velocity
from pirl_navrl.platforms.gym_pybullet_drones.observation_adapter import build_observation_dict
from pirl_navrl.scenarios.core import ObstacleConfig, ScenarioConfig


class GymPybulletDronesSimpleAdapter:
    platform_id = "gym_pybullet_drones_velocity_adapter_debug"

    def __init__(
        self,
        *,
        max_speed: float = 1.0,
        gui: bool = False,
        pyb_freq: int = 240,
        ctrl_freq: int = 48,
    ) -> None:
        self.max_speed = max_speed
        self.gui = gui
        self.pyb_freq = pyb_freq
        self.ctrl_freq = ctrl_freq
        self.env = None
        self.scenario: ScenarioConfig | None = None
        self.step_count = 0
        self.elapsed = 0.0
        self.last_platform_observation = None
        self.last_observation: dict[str, Any] | None = None
        self.pybullet_client: int | None = None
        self.drone_body_id: int | None = None
        self.obstacle_body_ids: dict[str, int] = {}
        try:
            from gym_pybullet_drones.envs.VelocityAviary import VelocityAviary
            from gym_pybullet_drones.utils.enums import DroneModel, Physics
        except ImportError as exc:
            raise RuntimeError(
                "gym-pybullet-drones is not available. Install the external "
                "dependency before using this adapter; no diagnostic fallback "
                "is provided here."
            ) from exc
        self._velocity_aviary_cls = VelocityAviary
        self._drone_model = DroneModel
        self._physics = Physics

    def reset(self, scenario: ScenarioConfig) -> dict[str, Any]:
        self.close()
        self.scenario = scenario
        self.step_count = 0
        self.elapsed = 0.0
        self.env = self._velocity_aviary_cls(
            drone_model=self._drone_model.CF2X,
            num_drones=1,
            initial_xyzs=np.asarray([scenario.start], dtype=np.float32),
            physics=self._physics.PYB,
            pyb_freq=self.pyb_freq,
            ctrl_freq=self.ctrl_freq,
            gui=self.gui,
            record=False,
            obstacles=False,
            user_debug_gui=False,
            output_folder="/tmp/pirl_navrl_task04",
        )
        platform_obs, _info = self.env.reset(seed=scenario.seed)
        self.pybullet_client = int(self.env.getPyBulletClient())
        self.drone_body_id = int(self.env.getDroneIds()[0])
        self._create_obstacle_bodies()
        self.last_platform_observation = platform_obs
        self.last_observation = build_observation_dict(
            platform_observation=platform_obs,
            scenario=scenario,
            step_count=self.step_count,
            elapsed=self.elapsed,
        )
        return self.last_observation

    def step(self, desired_velocity) -> tuple[dict[str, Any], float, bool, bool, dict[str, Any]]:
        if self.env is None or self.scenario is None:
            raise RuntimeError("reset(scenario) must be called before step()")
        action_result = adapt_desired_velocity(
            desired_velocity,
            "normalized_velocity",
            max_speed=self.max_speed,
        )
        env_action = np.asarray([action_result.velocity_aviary_action], dtype=np.float32)
        platform_obs, platform_reward, platform_terminated, platform_truncated, platform_info = self.env.step(env_action)
        self.step_count += 1
        self.elapsed += 1.0 / float(self.ctrl_freq)
        observation = build_observation_dict(
            platform_observation=platform_obs,
            scenario=self.scenario,
            step_count=self.step_count,
            elapsed=self.elapsed,
        )
        self.last_platform_observation = platform_obs
        self.last_observation = observation
        self._update_obstacle_bodies()
        safety_collision = bool(observation["min_clearance"] <= self.scenario.collision_radius)
        physical_collision = self._physical_obstacle_contact()
        collision = bool(safety_collision or physical_collision)
        success = bool(observation["distance_to_goal"] <= self.scenario.success_radius)
        timeout = bool(self.step_count >= self.scenario.max_steps and not collision and not success)
        terminated = bool(success or collision or platform_terminated)
        truncated = bool(timeout or platform_truncated)
        info = {
            "platform_id": self.platform_id,
            "scenario_id": self.scenario.scenario_id,
            "seed": self.scenario.seed,
            "step": self.step_count,
            "position": tuple(float(v) for v in observation["position"]),
            "velocity": tuple(float(v) for v in observation["velocity"]),
            "goal": self.scenario.goal,
            "distance_to_goal": float(observation["distance_to_goal"]),
            "min_clearance": float(observation["min_clearance"]),
            "collision": collision,
            "safety_collision": safety_collision,
            "physical_collision": physical_collision,
            "success": success,
            "timeout": timeout,
            "custom_obstacles_physical": True,
            "obstacle_body_ids": dict(self.obstacle_body_ids),
            "raw_desired_velocity": action_result.raw_desired_velocity,
            "clipped_desired_velocity": action_result.clipped_desired_velocity,
            "applied_action": action_result.applied_action,
            "velocity_aviary_action": action_result.velocity_aviary_action,
            "platform_reward": float(platform_reward),
            "platform_info": platform_info,
        }
        return observation, float(platform_reward), terminated, truncated, info

    def get_observation(self) -> dict[str, Any]:
        if self.last_observation is None:
            raise RuntimeError("reset(scenario) must be called before get_observation()")
        return self.last_observation

    def close(self) -> None:
        if self.env is None:
            return
        self.env.close()
        self.env = None
        self.pybullet_client = None
        self.drone_body_id = None
        self.obstacle_body_ids = {}

    def _create_obstacle_bodies(self) -> None:
        if self.scenario is None or self.pybullet_client is None:
            return
        self.obstacle_body_ids = {}
        for obstacle in self.scenario.all_obstacles():
            body_id = self._create_obstacle_body(obstacle, elapsed=0.0)
            self.obstacle_body_ids[obstacle.obstacle_id] = body_id

    def _create_obstacle_body(self, obstacle: ObstacleConfig, *, elapsed: float) -> int:
        if self.pybullet_client is None:
            raise RuntimeError("PyBullet client is not available")
        position = obstacle.position_at(elapsed)
        if obstacle.kind == "sphere":
            collision = p.createCollisionShape(
                p.GEOM_SPHERE,
                radius=obstacle.radius,
                physicsClientId=self.pybullet_client,
            )
            visual = p.createVisualShape(
                p.GEOM_SPHERE,
                radius=obstacle.radius,
                rgbaColor=[0.86, 0.12, 0.06, 0.88],
                physicsClientId=self.pybullet_client,
            )
        else:
            height = float(obstacle.height or obstacle.radius * 2.0)
            collision = p.createCollisionShape(
                p.GEOM_CYLINDER,
                radius=obstacle.radius,
                height=height,
                physicsClientId=self.pybullet_client,
            )
            visual = p.createVisualShape(
                p.GEOM_CYLINDER,
                radius=obstacle.radius,
                length=height,
                rgbaColor=[0.86, 0.12, 0.06, 0.88],
                physicsClientId=self.pybullet_client,
            )
        return int(
            p.createMultiBody(
                baseMass=0.0,
                baseCollisionShapeIndex=collision,
                baseVisualShapeIndex=visual,
                basePosition=position,
                physicsClientId=self.pybullet_client,
            )
        )

    def _update_obstacle_bodies(self) -> None:
        if self.scenario is None or self.pybullet_client is None:
            return
        for obstacle in self.scenario.all_obstacles():
            body_id = self.obstacle_body_ids.get(obstacle.obstacle_id)
            if body_id is None:
                continue
            p.resetBasePositionAndOrientation(
                body_id,
                obstacle.position_at(self.elapsed),
                [0.0, 0.0, 0.0, 1.0],
                physicsClientId=self.pybullet_client,
            )

    def _physical_obstacle_contact(self) -> bool:
        if self.pybullet_client is None or self.drone_body_id is None:
            return False
        for body_id in self.obstacle_body_ids.values():
            contacts = p.getContactPoints(
                bodyA=self.drone_body_id,
                bodyB=body_id,
                physicsClientId=self.pybullet_client,
            )
            if contacts:
                return True
        return False
