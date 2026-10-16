"""Tests for hvac_app known-input wiring (tracking residue)."""

import inspect

from hvac.hvac_app import HvacApp, advance_with_tracking_residue
from hvac.ladrc import LadrcState
from hvac.models import LadrcConfig, LadrcTuneConfig

# Locked CAP-5 thermal band (same numbers as tests/test_ladrc.py _thermal_config).
_THERMAL_B0 = 5e-4
_THERMAL_OMEGA_O = 0.03
_THERMAL_OMEGA_C = 0.01
_THERMAL_DT = 60.0


def _config() -> LadrcConfig:
    return LadrcConfig(
        b0=_THERMAL_B0,
        omega_o=_THERMAL_OMEGA_O,
        omega_c=_THERMAL_OMEGA_C,
        omega_c_min=0.02,
        omega_c_max=0.15,
        tune=LadrcTuneConfig(
            ki=0.005,
            deadband=0.2,
            min_steady_ticks=5,
            max_rate_fraction=0.05,
        ),
        dt=_THERMAL_DT,
    )


def test_control_tick_uses_tracking_residue_seam():
    """Call site must advance via seam, not absolute LadrcState.advance."""
    src = inspect.getsource(HvacApp.control_tick)
    assert "advance_with_tracking_residue" in src
    assert "self._ladrc.advance(" not in src


def test_residue_known_input_differs_behaviorally_from_absolute():
    """Residue vs absolute SWT must move the ESO differently (no private field)."""
    config = _config()
    measured = 21.0
    command = 55.0
    u_ff = 40.0

    via_residue = LadrcState()
    via_absolute = LadrcState()
    via_residue.reset(measured)
    via_absolute.reset(measured)

    advance_with_tracking_residue(via_residue, measured, command, u_ff, config)
    via_absolute.advance(measured, command, config)

    assert via_residue.z1 != via_absolute.z1


def test_advance_with_tracking_residue_uses_command_minus_uff():
    """ESO known input is post-clamp (command − u_ff), not absolute SWT."""
    state = LadrcState()
    config = _config()
    state.reset(21.0)
    command = 55.0  # absolute clamped plant write
    u_ff = 40.0

    advance_with_tracking_residue(state, 21.0, command, u_ff, config)

    assert state._last_u_applied == command - u_ff
    assert state._last_u_applied != command


def test_advance_with_tracking_residue_zero_when_command_equals_uff():
    state = LadrcState()
    config = _config()
    state.reset(21.0)
    u_ff = 40.0
    command = 40.0  # clamp at min with u_track ≈ 0

    advance_with_tracking_residue(state, 21.0, command, u_ff, config)

    assert state._last_u_applied == 0.0


def test_advance_with_tracking_residue_mid_band():
    """Residue when command sits between plant limits (not only clamp edges)."""
    state = LadrcState()
    config = _config()
    state.reset(21.0)
    u_ff = 45.0
    command = 50.0

    advance_with_tracking_residue(state, 21.0, command, u_ff, config)

    assert state._last_u_applied == 5.0


def test_advance_with_tracking_residue_negative_when_command_below_uff():
    """Post-clamp residue can be negative when command < u_ff."""
    state = LadrcState()
    config = _config()
    state.reset(21.0)
    u_ff = 50.0
    command = 40.0

    advance_with_tracking_residue(state, 21.0, command, u_ff, config)

    assert state._last_u_applied == -10.0


def test_hvac_app_config_matches_cap5_thermal_band():
    config = _config()
    assert config.b0 == _THERMAL_B0
    assert config.omega_o == _THERMAL_OMEGA_O
    assert config.omega_c == _THERMAL_OMEGA_C
    assert config.dt == _THERMAL_DT
