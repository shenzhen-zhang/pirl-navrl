def test_package_imports() -> None:
    import pirl_navrl
    from pirl_navrl.adapters.gym_pybullet_drones_adapter import GymPybulletDronesAdapter
    from pirl_navrl.metrics.episode_metrics import EpisodeMetricsWriter
    from pirl_navrl.risk.action_conditioned_risk import ActionConditionedRiskScorer
    from pirl_navrl.shield.risk_shield import ThresholdRiskShield

    assert pirl_navrl.__version__
    assert GymPybulletDronesAdapter
    assert EpisodeMetricsWriter
    assert ActionConditionedRiskScorer
    assert ThresholdRiskShield
