"""Tests for hvac_app known-input wiring (tracking residue) and blow-up guard."""

import inspect

from hvac.hvac_app import (
    HvacApp,
    advance_with_tracking_residue,
    format_blow_up_warning,
    guard_u_track,
    latch_after_zone_change,
)
from hvac.ladrc import LadrcState
from hvac.models import LadrcConfig, LadrcTuneConfig

# Locked CAP-5 thermal band (same numbers as tests/test_ladrc.py _thermal_config).
_THERMAL_B0 = 5e-4
_THERMAL_OMEGA_O = 0.03
_THERMAL_OMEGA_C = 0.01
_THERMAL_DT = 60.0

_SETPOINT_MIN = 40.0
_SETPOINT_MAX = 55.0
_U_TRACK_MAX = 100.0


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
        u_track_max=_U_TRACK_MAX,
    )


def _run_guard(
    *,
    u_track: float,
    u_ff: float = 40.0,
    latch_in: bool = False,
    u_track_max: float = _U_TRACK_MAX,
):
    return guard_u_track(
        u_track,
        u_ff,
        u_track_max,
        _SETPOINT_MIN,
        _SETPOINT_MAX,
        latch_in,
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


# --- CAP-3(c): blow-up guard seam (Hass-free) ---


def test_guard_healthy_clamps_sum_no_trip():
    u_ff = 42.0
    u_track = 5.0

    result = _run_guard(u_track=u_track, u_ff=u_ff)

    assert result.command == u_ff + u_track
    assert result.tripped is False
    assert result.should_warn is False
    assert result.latch_out is False
    assert result.reason is None


def test_guard_magnitude_trip_ff_only_no_eso_mutate():
    """Seam returns ff-only; does not reset ESO (AI-6: reset after write)."""
    ladrc = LadrcState()
    ladrc.reset(21.0)
    ladrc.z2 = 1.0
    u_ff = 42.0
    u_track = 150.0

    result = _run_guard(u_track=u_track, u_ff=u_ff)

    assert result.tripped is True
    assert result.should_warn is True
    assert result.latch_out is True
    assert result.reason == "magnitude"
    assert result.command == u_ff
    assert ladrc.z1 == 21.0
    assert ladrc.z2 == 1.0


def test_guard_trip_clamps_out_of_band_uff():
    """AI-7 / F-V2: trip command is clamp(u_ff), not raw u_ff."""
    low = _run_guard(u_track=200.0, u_ff=30.0)  # below setpoint_min
    assert low.tripped is True
    assert low.command == _SETPOINT_MIN

    high = _run_guard(u_track=200.0, u_ff=70.0)  # above setpoint_max
    assert high.tripped is True
    assert high.command == _SETPOINT_MAX


def test_guard_non_finite_trip():
    for bad in (float("nan"), float("inf"), float("-inf")):
        result = _run_guard(u_track=bad, u_ff=45.0)
        assert result.tripped is True
        assert result.should_warn is True
        assert result.latch_out is True
        assert result.reason == "non-finite"
        assert result.command == 45.0


def test_guard_consecutive_trips_warn_only_first():
    latch = False
    warns = []
    for _ in range(3):
        result = _run_guard(u_track=200.0, latch_in=latch)
        warns.append(result.should_warn)
        latch = result.latch_out
        assert result.tripped is True
        assert result.command == 40.0

    assert warns == [True, False, False]


def test_guard_latch_clears_on_healthy_then_warns_again():
    trip1 = _run_guard(u_track=200.0, latch_in=False)
    assert trip1.should_warn is True

    healthy = _run_guard(u_track=1.0, latch_in=trip1.latch_out)
    assert healthy.tripped is False
    assert healthy.latch_out is False
    assert healthy.should_warn is False

    trip2 = _run_guard(u_track=200.0, latch_in=healthy.latch_out)
    assert trip2.should_warn is True


def test_guard_poisoned_z2_via_compute_tracking():
    """CAP-3(c)+AI-6: trip → ff-only; reset then advance (post-write order)."""
    config = _config()
    ladrc = LadrcState()
    measured = 21.0
    ladrc.reset(measured)
    ladrc.critical_zone = "zone_one"
    ladrc.z2 = 1e12

    u_track = ladrc.compute_tracking(
        measured=measured,
        reference=22.0,
        config=config,
        critical_zone="zone_one",
    )
    assert abs(u_track) > config.u_track_max

    u_ff = 40.0
    result = _run_guard(
        u_track=u_track,
        u_ff=u_ff,
        u_track_max=config.u_track_max,
    )

    assert result.tripped is True
    assert result.command == u_ff
    assert ladrc.z2 == 1e12  # seam does not reset

    ladrc.reset(measured)
    assert ladrc.z2 == 0.0
    advance_with_tracking_residue(ladrc, measured, result.command, u_ff, config)
    assert ladrc._last_u_applied == 0.0


def test_format_blow_up_warning_floor_fields():
    mag = format_blow_up_warning("magnitude", 150.0, 100.0, "zone_one")
    assert "magnitude" in mag
    assert "150" in mag
    assert "100" in mag
    assert "zone_one" in mag

    for value, token in (
        (float("nan"), "nan"),
        (float("inf"), "inf"),
        (float("-inf"), "-inf"),
    ):
        msg = format_blow_up_warning("non-finite", value, 100.0, "zone_two")
        assert "non-finite" in msg
        assert token in msg
        assert "100" in msg
        assert "zone_two" in msg


def test_control_tick_calls_guard_after_compute_tracking():
    src = inspect.getsource(HvacApp.control_tick)
    assert src.index("compute_tracking") < src.index("guard_u_track")
    assert "format_blow_up_warning" in src
    assert "self._ladrc.guard" not in src


def test_control_tick_warns_before_write_on_demand_path():
    """Demand path: format_blow_up_warning before _write_setpoint(guard.command)."""
    src = inspect.getsource(HvacApp.control_tick)
    demand = src.split("if not decision.has_demand:")[1].split("return", 1)[1]
    assert demand.index("format_blow_up_warning") < demand.index(
        "_write_setpoint(guard.command)"
    )


def test_latch_after_zone_change_matrix():
    assert latch_after_zone_change("A", "B", True) is False
    assert latch_after_zone_change("A", "A", True) is True
    assert latch_after_zone_change(None, "B", True) is True
    assert latch_after_zone_change("A", "B", False) is False
    assert latch_after_zone_change("A", "A", False) is False
    assert latch_after_zone_change(None, "B", False) is False


def test_control_tick_latch_helper_before_compute_tracking():
    src = inspect.getsource(HvacApp.control_tick)
    assert src.index("latch_after_zone_change") < src.index("compute_tracking")


def test_idle_paths_clear_blow_up_latch():
    hands = inspect.getsource(HvacApp._hands_off)
    idle = inspect.getsource(HvacApp._go_idle)
    tick = inspect.getsource(HvacApp.control_tick)
    assert "_blow_up_latch = False" in hands
    assert "_blow_up_latch = False" in idle
    # no-demand path clears latch with clear()
    no_demand = tick.split("if not decision.has_demand:")[1].split("return")[0]
    assert "_blow_up_latch = False" in no_demand


def test_control_tick_trip_info_uses_guarded_marker():
    src = inspect.getsource(HvacApp.control_tick)
    assert "guarded" in src
    # Log trip branch is the last `if guard.tripped:` (after AI-6 reset).
    log_trip = src.rsplit("if guard.tripped:", 1)[1]
    trip_branch = log_trip.split("else:")[0]
    assert "guarded" in trip_branch
    assert "u_track={u_track:.2f}" not in trip_branch
    healthy_branch = log_trip.split("else:")[1]
    assert "u_track={u_track:.2f}" in healthy_branch


def test_control_tick_wires_should_warn_and_latch_out():
    """AI-7 / F-V3: once-per-episode Floor is wired at the control_tick call site."""
    src = inspect.getsource(HvacApp.control_tick)
    assert "self._blow_up_latch = guard.latch_out" in src
    assert "if guard.should_warn:" in src
    assert src.index("self._blow_up_latch = guard.latch_out") < src.index(
        "if guard.should_warn:"
    )
    assert src.index("if guard.should_warn:") < src.index(
        "_write_setpoint(guard.command)"
    )


def test_control_tick_skips_commit_omega_c_when_guard_tripped():
    """AI-5 / F-R2: persist adapted ωc only on healthy post-write ticks."""
    src = inspect.getsource(HvacApp.control_tick)
    assert "if new_omega_c is not None and not guard.tripped:" in src
    assert src.index("_write_setpoint(guard.command)") < src.index("commit_omega_c")


def test_control_tick_resets_eso_after_successful_write_on_trip():
    """AI-6 / F-R4: ESO reset only after plant write succeeds, before advance."""
    src = inspect.getsource(HvacApp.control_tick)
    write_i = src.index("_write_setpoint(guard.command)")
    # Trip reset lives in the post-write block (not inside guard_u_track).
    post_write = src[write_i:]
    assert "self._ladrc.reset(decision.measured)" in post_write
    assert post_write.index("self._ladrc.reset(decision.measured)") < post_write.index(
        "advance_with_tracking_residue"
    )
    assert "ladrc.reset" not in inspect.getsource(guard_u_track)
