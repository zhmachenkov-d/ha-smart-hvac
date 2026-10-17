"""Tests for hvac_app known-input wiring (tracking residue) and blow-up guard."""

import inspect
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from hvac.hvac_app import (
    LATCH_DECAY_U_TRACK_FRACTION,
    HvacApp,
    advance_with_tracking_residue,
    format_blow_up_warning,
    guard_u_track,
    latch_after_zone_change,
    latch_decay_residue_holds,
    next_decayed_omega_c,
    should_apply_omega_c,
    sticky_blow_up_latch,
)
from hvac.ladrc import LadrcState
from hvac.ladrc_tuner import LadrcTuner
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


def test_control_tick_wires_should_warn_and_sticky_latch():
    """AI-7 / F-V3 + CAP-4: WARN before write; sticky only after successful write."""
    src = inspect.getsource(HvacApp.control_tick)
    assert "sticky_blow_up_latch(" in src
    assert "guard.latch_out" not in src
    assert "if guard.should_warn:" in src
    write_i = src.index("_write_setpoint(guard.command)")
    assert src.index("if guard.should_warn:") < write_i
    assert write_i < src.index("sticky_blow_up_latch(")


def test_control_tick_skips_commit_omega_c_when_guard_tripped():
    """AI-5 / F-R2: persist adapted ωc only via apply_proposed after write."""
    src = inspect.getsource(HvacApp.control_tick)
    write_i = src.index("_write_setpoint(guard.command)")
    # Provisional apply gate before write; post-write commit gated by apply_proposed.
    assert src.index("should_apply_omega_c") < write_i
    post_write = src[write_i:]
    assert "omega_to_commit" not in post_write
    assert "should_apply_omega_c" not in post_write
    commit_gate = "if apply_proposed:"
    assert commit_gate in post_write
    # Normal commit lives in the else of the CAP-4 decay branch.
    normal_commit = post_write.split(commit_gate, 1)[1]
    assert "_tuner.commit_omega_c(new_omega_c)" in normal_commit
    # Must not regress to persistence-only gating (guard.tripped alone).
    assert "if new_omega_c is not None and not guard.tripped:" not in src
    # CAP-4: decay branch before normal apply_proposed else.
    assert "latch_decay_residue_holds" in post_write
    assert "next_decayed_omega_c" in post_write
    assert post_write.index("next_decayed_omega_c") < post_write.index(commit_gate)


def test_control_tick_skips_maybe_adapt_when_latched_at_start():
    """CAP-6(e): latch already active at tick start → maybe_adapt not called."""
    src = inspect.getsource(HvacApp.control_tick)
    demand = src.split("if not decision.has_demand:")[1].split("return", 1)[1]
    adapt_call = "self._tuner.maybe_adapt("
    assert "latch_at_start = self._blow_up_latch" in demand
    assert demand.index("latch_at_start = self._blow_up_latch") < demand.index(
        adapt_call
    )
    assert "if latch_at_start:" in demand
    skip_block = demand.split("if latch_at_start:")[1].split("else:")[0]
    assert "new_omega_c = None" in skip_block
    assert adapt_call not in skip_block


@pytest.mark.parametrize(
    ("proposed", "current", "tripped", "command", "expected"),
    [
        (None, 0.05, False, 47.0, False),  # no proposal
        (0.06, 0.05, True, 47.0, False),  # guard tripped
        (0.06, 0.05, False, _SETPOINT_MAX, False),  # max + ωc↑
        (0.04, 0.05, False, _SETPOINT_MAX, True),  # max + ωc↓
        (0.04, 0.05, False, _SETPOINT_MIN, False),  # min + ωc↓
        (0.06, 0.05, False, _SETPOINT_MIN, True),  # min + ωc↑
        (0.06, 0.05, False, 47.0, True),  # interior
    ],
)
def test_should_apply_omega_c_matrix(
    proposed: float | None,
    current: float,
    tripped: bool,
    command: float,
    expected: bool,
) -> None:
    """CAP-6(a): directional clamp + guard trip matrix."""
    assert (
        should_apply_omega_c(
            proposed,
            current,
            guard_tripped=tripped,
            command=command,
            setpoint_min=_SETPOINT_MIN,
            setpoint_max=_SETPOINT_MAX,
        )
        is expected
    )


def test_saturated_upward_proposal_does_not_ratchet_applied_or_committed() -> None:
    """CAP-6(b): Hass-free loop — write-path applied and committed ωc never rise."""
    config = _config()
    ladrc = LadrcState()
    measured = 21.0
    reference = 22.0
    zone = "zone_one"
    ladrc.reset(measured)
    ladrc.critical_zone = zone

    committed_omega = config.omega_c
    # Positive u_track + u_ff at max → healthy command clamped at setpoint_max.
    u_ff = _SETPOINT_MAX

    for step in range(10):
        proposed = committed_omega * (1.0 + 0.05 * (step + 1))
        assert proposed > committed_omega

        proposed_cfg = config.with_omega_c(proposed)
        provisional_u = ladrc.compute_tracking(
            measured=measured,
            reference=reference,
            config=proposed_cfg,
            critical_zone=zone,
        )
        provisional = _run_guard(
            u_track=provisional_u,
            u_ff=u_ff,
            u_track_max=proposed_cfg.u_track_max,
        )
        assert provisional.command >= _SETPOINT_MAX

        apply_proposed = should_apply_omega_c(
            proposed,
            committed_omega,
            guard_tripped=provisional.tripped,
            command=provisional.command,
            setpoint_min=_SETPOINT_MIN,
            setpoint_max=_SETPOINT_MAX,
        )
        if apply_proposed:
            write_cfg = proposed_cfg
        else:
            write_cfg = config.with_omega_c(committed_omega)

        applied_omega = write_cfg.omega_c
        assert applied_omega == committed_omega
        assert applied_omega == config.omega_c

        if apply_proposed:
            committed_omega = proposed

        assert committed_omega == config.omega_c


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


# --- CAP-4 / CAP-6(e): latch decay + skip adapt ---


def _decay_config(*, omega_c: float = 0.10) -> LadrcConfig:
    """Config with headroom above omega_c_min so decay steps are observable."""
    return LadrcConfig(
        b0=_THERMAL_B0,
        omega_o=_THERMAL_OMEGA_O,
        omega_c=omega_c,
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


@pytest.mark.parametrize(
    ("u_track", "u_track_max", "expected"),
    [
        (81.0, 100.0, True),  # just above 0.8·max
        (80.0, 100.0, False),  # at band
        (50.0, 100.0, False),  # below band
        (100.0, 100.0, True),  # at trip magnitude
        (150.0, 100.0, True),  # above trip
        (float("nan"), 100.0, True),
        (float("inf"), 100.0, True),
        (float("-inf"), 100.0, True),
    ],
)
def test_latch_decay_residue_holds_matrix(
    u_track: float, u_track_max: float, expected: bool
) -> None:
    assert latch_decay_residue_holds(u_track, u_track_max) is expected


def test_latch_decay_fraction_constant() -> None:
    assert LATCH_DECAY_U_TRACK_FRACTION == 0.8


def test_next_decayed_omega_c_step_and_floor() -> None:
    assert next_decayed_omega_c(0.10, 0.05, 0.02) == pytest.approx(0.095)
    # Floor at omega_c_min.
    assert next_decayed_omega_c(0.021, 0.05, 0.02) == pytest.approx(0.02)
    assert next_decayed_omega_c(0.02, 0.05, 0.02) == pytest.approx(0.02)


@pytest.mark.parametrize(
    ("latch_in", "tripped", "u_track", "expected"),
    [
        (False, True, 150.0, True),  # trip sets
        (True, False, 90.0, True),  # hold in (0.8·max, max]
        (True, False, 100.0, True),  # hold at max (not tripped; abs==max)
        (True, False, 80.0, False),  # clear at ≤ band
        (True, False, 50.0, False),  # clear below band
        (False, False, 90.0, False),  # no latch_in, not tripped
        (True, True, 150.0, True),  # trip while already latched
        (True, False, float("nan"), True),  # non-finite holds
    ],
)
def test_sticky_blow_up_latch_matrix(
    latch_in: bool, tripped: bool, u_track: float, expected: bool
) -> None:
    """CAP-4 sticky latch: trip sets; holds in (0.8·max, max]; clears at ≤ band."""
    assert sticky_blow_up_latch(latch_in, tripped, u_track, _U_TRACK_MAX) is expected


def _mirror_decay_tick(
    *,
    tuner: LadrcTuner,
    config: LadrcConfig,
    latch: bool,
    u_track: float,
    u_ff: float = 40.0,
    write_ok: bool = True,
) -> bool:
    """Hass-free mirror of control_tick sticky+decay after a plant write attempt.

    When write_ok is False, matches fail-write early return: latch and ωc unchanged.
    """
    latch_in = latch
    guard = guard_u_track(
        u_track,
        u_ff,
        config.u_track_max,
        _SETPOINT_MIN,
        _SETPOINT_MAX,
        latch_in,
    )
    if not write_ok:
        return latch_in
    latch_out = sticky_blow_up_latch(
        latch_in, guard.tripped, u_track, config.u_track_max
    )
    if latch_out and latch_decay_residue_holds(u_track, config.u_track_max):
        tuner.commit_omega_c(
            next_decayed_omega_c(
                tuner.omega_c,
                config.tune.max_rate_fraction,
                config.omega_c_min,
            )
        )
    return latch_out


def test_multi_tick_decay_persists_until_omega_c_min(tmp_path: Path) -> None:
    """CAP-6(e): latched ticks with |u_track| above band decay persisted ωc to floor."""
    config = _decay_config(omega_c=0.10)
    state_path = tmp_path / "ladrc_tune_state.json"
    tuner = LadrcTuner(config, state_path)
    assert tuner.omega_c == pytest.approx(0.10)

    # Residue in (0.8·max, max]: not tripped, sticky holds, decay runs.
    u_track = 90.0
    latch = True
    for _ in range(200):
        latch = _mirror_decay_tick(
            tuner=tuner, config=config, latch=latch, u_track=u_track
        )
        if tuner.omega_c <= config.omega_c_min + 1e-12:
            break

    assert latch is True
    assert tuner.omega_c == pytest.approx(config.omega_c_min)
    persisted = json.loads(state_path.read_text(encoding="utf-8"))["omega_c"]
    assert persisted == pytest.approx(config.omega_c_min)
    reloaded = LadrcTuner(config, state_path)
    assert reloaded.omega_c == pytest.approx(config.omega_c_min)


def test_decay_stops_when_residue_at_or_below_band(tmp_path: Path) -> None:
    """Finite |u_track| ≤ 0.8·u_track_max clears sticky latch and skips decay."""
    config = _decay_config(omega_c=0.10)
    state_path = tmp_path / "ladrc_tune_state.json"
    tuner = LadrcTuner(config, state_path)

    latch = True
    latch = _mirror_decay_tick(tuner=tuner, config=config, latch=latch, u_track=90.0)
    assert latch is True
    after_decay = tuner.omega_c
    assert after_decay < 0.10

    latch = _mirror_decay_tick(tuner=tuner, config=config, latch=latch, u_track=80.0)
    assert latch is False
    assert tuner.omega_c == pytest.approx(after_decay)
    persisted = json.loads(state_path.read_text(encoding="utf-8"))["omega_c"]
    assert persisted == pytest.approx(after_decay)


def test_non_finite_u_track_decay_persists(tmp_path: Path) -> None:
    """CAP-6(e): latched + non-finite u_track steps ωc down via real commit_omega_c."""
    config = _decay_config(omega_c=0.10)
    state_path = tmp_path / "ladrc_tune_state.json"
    tuner = LadrcTuner(config, state_path)
    expected = next_decayed_omega_c(
        0.10, config.tune.max_rate_fraction, config.omega_c_min
    )

    latch = _mirror_decay_tick(
        tuner=tuner, config=config, latch=True, u_track=float("nan")
    )

    assert latch is True
    assert tuner.omega_c == pytest.approx(expected)
    persisted = json.loads(state_path.read_text(encoding="utf-8"))["omega_c"]
    assert persisted == pytest.approx(expected)


def test_trip_edge_decay_persists_despite_guard_trip(tmp_path: Path) -> None:
    """CAP-6(e): trip-edge latches and decay-persists; normal commit still skips."""
    config = _decay_config(omega_c=0.10)
    state_path = tmp_path / "ladrc_tune_state.json"
    tuner = LadrcTuner(config, state_path)
    current = tuner.omega_c
    u_track = 150.0
    u_ff = 40.0

    # Latch inactive at start (trip-edge); adapt may have proposed — commit blocked.
    guard = guard_u_track(
        u_track,
        u_ff,
        config.u_track_max,
        _SETPOINT_MIN,
        _SETPOINT_MAX,
        False,
    )
    assert guard.tripped is True
    assert (
        should_apply_omega_c(
            0.11,
            current,
            guard_tripped=guard.tripped,
            command=guard.command,
            setpoint_min=_SETPOINT_MIN,
            setpoint_max=_SETPOINT_MAX,
        )
        is False
    )

    expected = next_decayed_omega_c(
        current, config.tune.max_rate_fraction, config.omega_c_min
    )
    latch = _mirror_decay_tick(
        tuner=tuner, config=config, latch=False, u_track=u_track, u_ff=u_ff
    )

    assert latch is True
    assert tuner.omega_c == pytest.approx(expected)
    persisted = json.loads(state_path.read_text(encoding="utf-8"))["omega_c"]
    assert persisted == pytest.approx(expected)
    reloaded = LadrcTuner(config, state_path)
    assert reloaded.omega_c == pytest.approx(expected)


def test_single_decay_step_matches_max_rate_fraction(tmp_path: Path) -> None:
    """Acceptance: one latched high-residue tick decreases persisted ωc by one step."""
    config = _decay_config(omega_c=0.10)
    state_path = tmp_path / "ladrc_tune_state.json"
    tuner = LadrcTuner(config, state_path)
    expected = next_decayed_omega_c(
        0.10, config.tune.max_rate_fraction, config.omega_c_min
    )

    _mirror_decay_tick(tuner=tuner, config=config, latch=True, u_track=90.0)

    assert tuner.omega_c == pytest.approx(expected)
    persisted = json.loads(state_path.read_text(encoding="utf-8"))["omega_c"]
    assert persisted == pytest.approx(expected)


def test_fail_write_leaves_latch_and_omega_c_unchanged(tmp_path: Path) -> None:
    """Fail-write early return: sticky/decay must not run (sticky-after-write)."""
    config = _decay_config(omega_c=0.10)
    state_path = tmp_path / "ladrc_tune_state.json"
    tuner = LadrcTuner(config, state_path)

    # Latched + gray-band residue would decay if write succeeded.
    latch = _mirror_decay_tick(
        tuner=tuner, config=config, latch=True, u_track=90.0, write_ok=False
    )
    assert latch is True
    assert tuner.omega_c == pytest.approx(0.10)

    # Trip-edge would sticky+decay on success; fail keeps latch False.
    latch = _mirror_decay_tick(
        tuner=tuner, config=config, latch=False, u_track=150.0, write_ok=False
    )
    assert latch is False
    assert tuner.omega_c == pytest.approx(0.10)
    assert not state_path.is_file()


# --- CAP-6 (c)(d): write-on-change vs fail-closed ---

_PLANT_SETPOINT = "number.plant_setpoint"


def _write_stub(raw_state: object) -> HvacApp:
    """Minimal Hass surface for HvacApp._write_setpoint / _read_float."""
    app = object.__new__(HvacApp)
    app._config = SimpleNamespace(plant_setpoint=_PLANT_SETPOINT)
    app.get_state = MagicMock(return_value=raw_state)
    app.call_service = MagicMock()
    app.log = MagicMock()
    return app


@pytest.mark.parametrize(
    "raw_state",
    [42.0, "42.0", 42],
)
def test_write_setpoint_skips_set_value_when_entity_float_equals(raw_state):
    """CAP-6(c): identical entity float skips set_value; returns success."""
    app = _write_stub(raw_state)

    ok = HvacApp._write_setpoint(app, 42.0)

    assert ok is True
    app.call_service.assert_not_called()


def test_write_setpoint_calls_set_value_when_entity_float_differs():
    app = _write_stub(40.0)

    ok = HvacApp._write_setpoint(app, 42.0)

    assert ok is True
    app.call_service.assert_called_once_with(
        "number/set_value",
        entity_id=_PLANT_SETPOINT,
        value=42.0,
    )


@pytest.mark.parametrize(
    "raw_state",
    [None, "unavailable", "unknown", "not-a-float", object()],
)
def test_write_setpoint_fail_closed_when_entity_unreadable(raw_state):
    """CAP-6(d): unreadable/unparseable → no set_value, false (tick abort)."""
    app = _write_stub(raw_state)

    ok = HvacApp._write_setpoint(app, 42.0)

    assert ok is False
    app.call_service.assert_not_called()
