"""Heuristic action-conditioned risk scoring for phase 1 diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pirl_navrl.adapters.gym_pybullet_drones_adapter import (
    DroneObservation,
    GymPybulletDronesAdapter,
)


def _clip01(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def _mean_abs(values: list[float]) -> float:
    return sum(abs(v) for v in values) / len(values) if values else 0.0


@dataclass(frozen=True)
class RiskConfig:
    threshold: float = 0.55
    min_altitude_m: float = 0.15
    max_speed_mps: float = 2.5
    max_abs_action: float = 1.0
    action_weight: float = 0.35
    state_weight: float = 0.65
    action_delta_weight: float = 0.15


@dataclass(frozen=True)
class RiskEstimate:
    score: float
    components: dict[str, float]
    result_kind: str = "diagnostic"


class ActionConditionedRiskScorer:
    """Compute a bounded diagnostic risk score from state and proposed action."""

    def __init__(
        self,
        config: RiskConfig | None = None,
        adapter: GymPybulletDronesAdapter | None = None,
    ) -> None:
        self.config = config or RiskConfig()
        self.adapter = adapter or GymPybulletDronesAdapter()

    def score(
        self,
        observation: Any | DroneObservation,
        action: list[float],
        previous_action: list[float] | None = None,
    ) -> RiskEstimate:
        summary = (
            observation
            if isinstance(observation, DroneObservation)
            else self.adapter.summarize_observation(observation)
        )

        cfg = self.config
        altitude_risk = _clip01((cfg.min_altitude_m - summary.altitude_m) / cfg.min_altitude_m)
        speed_risk = _clip01(summary.speed_mps / cfg.max_speed_mps)
        action_risk = _clip01(_mean_abs(action) / cfg.max_abs_action)

        delta_risk = 0.0
        if previous_action:
            deltas = [a - previous_action[i] for i, a in enumerate(action[: len(previous_action)])]
            delta_risk = _clip01(_mean_abs(deltas) / cfg.max_abs_action)

        state_risk = max(altitude_risk, speed_risk)
        action_term = (1.0 - cfg.action_delta_weight) * action_risk + cfg.action_delta_weight * delta_risk
        score = _clip01(cfg.state_weight * state_risk + cfg.action_weight * action_term)

        return RiskEstimate(
            score=score,
            components={
                "altitude_risk": altitude_risk,
                "speed_risk": speed_risk,
                "action_risk": action_risk,
                "action_delta_risk": delta_risk,
                "state_risk": state_risk,
            },
        )
