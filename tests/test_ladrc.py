"""Tests for discrete LADRC."""

import math

from hvac.ladrc import LadrcState
from hvac.models import LadrcConfig, LadrcTuneConfig


def _default_config() -> LadrcConfig:
    return LadrcConfig(
        b0=2.8,
        omega_o=19.49,
        omega_c=0.053,
        omega_c_min=0.02,
        omega_c_max=0.15,
        tune=LadrcTuneConfig(
            ki=0.005,
            deadband=0.2,
            min_steady_ticks=5,
            max_rate_fraction=0.05,
        ),
        dt=60.0,
    )


def test_compute_tracking_returns_finite_u_track():
    state = LadrcState()
    u = state.compute_tracking(
        measured=18.0,
        reference=20.0,
        config=_default_config(),
        critical_zone="living_room",
    )
    assert math.isfinite(u)


def test_critical_zone_change_resets_observer():
    config = _default_config()
    state = LadrcState()
    state.compute_tracking(18.0, 20.0, config, "living_room")
    state.compute_tracking(19.0, 21.0, config, "bedroom")
    assert state.z1 == 19.0
    assert state.z2 == 0.0


def test_clear_resets_state():
    state = LadrcState()
    config = _default_config()
    state.compute_tracking(18.0, 20.0, config, "living_room")
    state.clear()
    assert state.z1 == 0.0
    assert state.z2 == 0.0
    assert state.critical_zone is None


def test_eso_bounded_with_60s_dt():
    config = _default_config()
    state = LadrcState(z1=18.0, z2=0.0)
    z1_prev = state.z1
    state.advance(20.0, 0.0, config)
    assert abs(state.z1 - z1_prev) < 50


def test_compute_tracking_does_not_advance_eso():
    config = _default_config()
    state = LadrcState(z1=18.0, z2=0.5)
    state.compute_tracking(18.0, 20.0, config, "living_room")
    z1_after_1 = state.z1
    z2_after_1 = state.z2
    state.compute_tracking(18.5, 20.0, config, "living_room")
    assert state.z1 == z1_after_1
    assert state.z2 == z2_after_1


def test_advance_uses_u_applied():
    config = _default_config()
    state = LadrcState(z1=18.0, z2=0.0)
    state.advance(18.0, 0.0, config)
    z1_zero = state.z1
    state = LadrcState(z1=18.0, z2=0.0)
    state.advance(18.0, 40.0, config)
    assert state.z1 != z1_zero
