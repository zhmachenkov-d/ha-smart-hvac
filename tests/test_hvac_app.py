"""Tests for hvac_app known-input wiring (tracking residue)."""

from hvac.hvac_app import advance_with_tracking_residue
from hvac.ladrc import LadrcState
from hvac.models import LadrcConfig, LadrcTuneConfig


def _config() -> LadrcConfig:
    return LadrcConfig(
        b0=5e-4,
        omega_o=0.03,
        omega_c=0.01,
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
