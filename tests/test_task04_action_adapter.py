import numpy as np
import pytest

from pirl_navrl.platforms.gym_pybullet_drones.action_adapter import (
    adapt_desired_velocity,
    clip_desired_velocity,
    desired_velocity_to_action,
    normalize_desired_velocity,
)


def test_clip_desired_velocity_limits_norm_and_shape() -> None:
    clipped = clip_desired_velocity((3.0, 4.0, 0.0), max_speed=2.0)

    assert clipped.shape == (3,)
    assert np.linalg.norm(clipped) <= 2.0 + 1e-6


def test_normalize_desired_velocity_is_bounded() -> None:
    normalized = normalize_desired_velocity((3.0, 0.0, 0.0), max_speed=1.5)

    assert normalized.shape == (3,)
    assert np.all(normalized <= 1.0)
    assert np.all(normalized >= -1.0)


def test_desired_velocity_to_action_tracks_raw_clipped_and_applied() -> None:
    action = desired_velocity_to_action((2.0, 0.0, 0.0), max_speed=1.0)
    result = adapt_desired_velocity((2.0, 0.0, 0.0), max_speed=1.0)

    assert action.shape == (3,)
    assert np.all(action <= 1.0)
    assert np.all(action >= -1.0)
    assert result.raw_desired_velocity == (2.0, 0.0, 0.0)
    assert result.clipped_desired_velocity == (1.0, 0.0, 0.0)
    assert result.applied_action == (1.0, 0.0, 0.0)
    assert len(result.velocity_aviary_action) == 4


def test_action_adapter_rejects_non_positive_max_speed() -> None:
    with pytest.raises(ValueError):
        clip_desired_velocity((1.0, 0.0, 0.0), max_speed=0.0)
