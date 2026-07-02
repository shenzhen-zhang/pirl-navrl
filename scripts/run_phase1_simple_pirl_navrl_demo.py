#!/usr/bin/env python3
"""Run a small diagnostic PIRL-NavRL shield demo on gym-pybullet-drones."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pirl_navrl.adapters.gym_pybullet_drones_adapter import GymPybulletDronesAdapter
from pirl_navrl.metrics.episode_metrics import EpisodeMetricsWriter
from pirl_navrl.risk.action_conditioned_risk import ActionConditionedRiskScorer, RiskConfig
from pirl_navrl.shield.risk_shield import ThresholdRiskShield


DEFAULT_CONFIG = ROOT / "configs" / "phase1_simple_demo.json"


INSTALL_HINT = """
Install the phase 1 backend before running the real demo:
  bash scripts/setup_external_repos.sh
  pip install -e external/gym-pybullet-drones
  pip install -e .
"""


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def make_env(gui: bool = False) -> Any:
    try:
        import gymnasium as gym
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"gymnasium import failed: {exc}") from exc

    try:
        from gym_pybullet_drones.utils.enums import ActionType, ObservationType
    except Exception:
        ActionType = None
        ObservationType = None

    kwargs: dict[str, Any] = {"gui": gui}
    if ObservationType is not None:
        kwargs["obs"] = ObservationType.KIN
    if ActionType is not None:
        kwargs["act"] = ActionType.RPM

    candidates = ["hover-aviary-v0", "HoverAviary-v0"]
    errors = []
    for env_id in candidates:
        try:
            return gym.make(env_id, **kwargs)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{env_id}: {exc}")

    try:
        from gym_pybullet_drones.envs.HoverAviary import HoverAviary

        return HoverAviary(**kwargs)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"HoverAviary direct import: {exc}")
        raise RuntimeError("Could not create a gym-pybullet-drones HoverAviary env.\n" + "\n".join(errors)) from exc


def reset_env(env: Any, seed: int) -> Any:
    try:
        result = env.reset(seed=seed)
    except TypeError:
        result = env.reset()
    return result[0] if isinstance(result, tuple) else result


def step_env(env: Any, action: Any) -> tuple[Any, float, bool, dict[str, Any]]:
    result = env.step(action)
    if len(result) == 5:
        observation, reward, terminated, truncated, info = result
        return observation, float(reward), bool(terminated or truncated), dict(info)
    observation, reward, done, info = result
    return observation, float(reward), bool(done), dict(info)


def sample_action(env: Any, adapter: GymPybulletDronesAdapter) -> list[float]:
    if hasattr(env.action_space, "sample"):
        return adapter.action_to_env(env.action_space.sample())
    return adapter.action_to_env([0.0] * adapter.action_dim)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--steps", type=int)
    parser.add_argument("--gui", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    steps = args.steps or int(config["demo"]["steps"])
    output = args.output or ROOT / config["demo"]["output_path"]

    try:
        env = make_env(gui=args.gui)
    except RuntimeError as exc:
        print(str(exc))
        print(INSTALL_HINT.strip())
        return 1

    if hasattr(env.action_space, "seed"):
        env.action_space.seed(int(config["seed"]))

    adapter = GymPybulletDronesAdapter(action_space=env.action_space)
    risk_cfg = RiskConfig(**config["risk"])
    scorer = ActionConditionedRiskScorer(config=risk_cfg, adapter=adapter)
    shield = ThresholdRiskShield(scorer=scorer)

    metadata = {
        "task_id": config["task_id"],
        "platform_id": config["platform_id"],
        "algorithm_id": config["algorithm_id"],
        "environment_id": config["environment_id"],
        "seed": config["seed"],
        "config_path": str(args.config.relative_to(ROOT) if args.config.is_relative_to(ROOT) else args.config),
        "metric_source": "scripts/run_phase1_simple_pirl_navrl_demo.py",
    }

    observation = reset_env(env, int(config["seed"]))
    total_reward = 0.0
    try:
        with EpisodeMetricsWriter(output, metadata) as writer:
            for step in range(steps):
                proposed_action = sample_action(env, adapter)
                shield_result = shield.filter_action(observation, proposed_action, step=step)
                env_action = adapter.format_action_for_env(shield_result.action)
                observation, reward, done, info = step_env(env, env_action)
                total_reward += reward
                writer.write(
                    {
                        "event": "step",
                        "step": step,
                        "reward": reward,
                        "total_reward": total_reward,
                        "risk_score": shield_result.risk.score,
                        "risk_components": shield_result.risk.components,
                        "intervened": shield_result.intervened,
                        "shield_reason": shield_result.reason,
                        "info_keys": sorted(info.keys()),
                    }
                )
                if done:
                    break
    finally:
        env.close()

    print(f"Wrote diagnostic metrics to {output}")
    print(f"Interventions: {len(shield.interventions)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
