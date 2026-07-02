from pirl_navrl.adapters.gym_pybullet_drones_adapter import GymPybulletDronesAdapter
from pirl_navrl.risk.action_conditioned_risk import ActionConditionedRiskScorer, RiskConfig
from pirl_navrl.shield.risk_shield import ThresholdRiskShield


def test_shield_intervenes_when_risk_exceeds_threshold() -> None:
    adapter = GymPybulletDronesAdapter(action_dim=4)
    scorer = ActionConditionedRiskScorer(
        RiskConfig(threshold=0.5, min_altitude_m=0.2, max_abs_action=1.0),
        adapter=adapter,
    )
    shield = ThresholdRiskShield(scorer, fallback_action=[0.0, 0.0, 0.0, 0.0])

    # x, y, z plus padding to velocity indices. z is below min altitude.
    observation = [0.0, 0.0, 0.01, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.0, 0.0, 0.0]
    result = shield.filter_action(observation, [1.0, 1.0, 1.0, 1.0], step=7)

    assert result.intervened is True
    assert result.action == [0.0, 0.0, 0.0, 0.0]
    assert result.risk.result_kind == "diagnostic"
    assert shield.interventions[0]["step"] == 7


def test_shield_passes_low_risk_action() -> None:
    scorer = ActionConditionedRiskScorer(RiskConfig(threshold=0.9))
    shield = ThresholdRiskShield(scorer)

    observation = [0.0, 0.0, 1.0] + [0.0] * 10
    action = [0.05, 0.05, 0.05, 0.05]
    result = shield.filter_action(observation, action, step=0)

    assert result.intervened is False
    assert result.action == action
    assert shield.interventions == []
