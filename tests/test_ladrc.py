"""Tests for discrete LADRC."""

import math

from hvac.ladrc import LadrcState
from hvac.models import LadrcConfig


def _default_config() -> LadrcConfig:
    return LadrcConfig(b0=2.8, kp=0.053, beta1=15, beta2=380, dt=60.0)


def test_step_returns_finite_u_track():
    state = LadrcState()
    u = state.step(
        measured=18.0,
        reference=20.0,
        config=_default_config(),
        critical_zone="living_room",
    )
    assert math.isfinite(u)


def test_critical_zone_change_resets_observer():
    config = _default_config()
    state = LadrcState()
    state.step(18.0, 20.0, config, "living_room")
    state.step(19.0, 21.0, config, "bedroom")
    assert state.z1 == 19.0
    assert state.z2 == 0.0


def test_clear_resets_state():
    state = LadrcState()
    config = _default_config()
    state.step(18.0, 20.0, config, "living_room")
    state.clear()
    assert state.z1 == 0.0
    assert state.z2 == 0.0
    assert state.critical_zone is None
