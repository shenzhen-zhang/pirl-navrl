"""Threshold-based diagnostic action shield."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pirl_navrl.risk.action_conditioned_risk import ActionConditionedRiskScorer, RiskEstimate


@dataclass(frozen=True)
class ShieldResult:
    action: list[float]
    proposed_action: list[float]
    risk: RiskEstimate
    intervened: bool
    reason: str
    result_kind: str = "diagnostic"


class ThresholdRiskShield:
    """Apply a fallback action when diagnostic risk exceeds a threshold."""

    def __init__(
        self,
        scorer: ActionConditionedRiskScorer,
        threshold: float | None = None,
        fallback_action: list[float] | None = None,
    ) -> None:
        self.scorer = scorer
        self.threshold = scorer.config.threshold if threshold is None else threshold
        self.fallback_action = fallback_action
        self.previous_action: list[float] | None = None
        self.interventions: list[dict[str, Any]] = []

    def filter_action(self, observation: Any, proposed_action: list[float], step: int = 0) -> ShieldResult:
        risk = self.scorer.score(observation, proposed_action, self.previous_action)
        intervened = risk.score > self.threshold
        if intervened:
            action = self._fallback_for(proposed_action)
            reason = f"risk {risk.score:.3f} exceeded threshold {self.threshold:.3f}"
            self.interventions.append(
                {
                    "step": step,
                    "risk_score": risk.score,
                    "threshold": self.threshold,
                    "reason": reason,
                    "result_kind": "diagnostic",
                }
            )
        else:
            action = list(proposed_action)
            reason = "risk below threshold"

        self.previous_action = list(action)
        return ShieldResult(
            action=action,
            proposed_action=list(proposed_action),
            risk=risk,
            intervened=intervened,
            reason=reason,
        )

    def _fallback_for(self, proposed_action: list[float]) -> list[float]:
        if self.fallback_action is not None:
            return list(self.fallback_action)
        return [0.0 for _ in proposed_action]
