"""Tests for continuous-form LADRC (CAP-5 ESO discretization)."""

import math

from hvac.ladrc import LadrcState
from hvac.models import LadrcConfig, LadrcTuneConfig

# Locked CAP-5 thermal+C scenario (not example YAML).
_Y = 21.0
_T_R = 21.2
_U_FF = 40.0
_CLAMP_MIN = 40.0
_CLAMP_MAX = 55.0
_N_TICKS = 80
_ZONE = "living_room"


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


def _thermal_config() -> LadrcConfig:
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


def _example_aligned_config() -> LadrcConfig:
    """CAP-3(b) / AI-1 package A: same b0/ωo/ωc/u_track_max as apps.yaml.example."""
    return LadrcConfig(
        b0=5e-4,
        omega_o=0.03,
        omega_c=0.03,
        omega_c_min=0.02,
        omega_c_max=0.15,
        tune=LadrcTuneConfig(
            ki=0.005,
            deadband=0.2,
            min_steady_ticks=5,
            max_rate_fraction=0.05,
        ),
        dt=60.0,
        u_track_max=250.0,
    )


def _advance_exp_map(
    state: LadrcState,
    measured: float,
    u_applied: float,
    config: LadrcConfig,
) -> None:
    """Frozen pre-change α-map body; mutates the same LadrcState as compute_tracking."""
    dt = config.dt
    error = measured - state.z1
    omega_o = math.sqrt(config.beta2)
    alpha = 1.0 - math.exp(-omega_o * dt)
    g1 = 2.0 * alpha
    g2 = alpha * alpha

    state.z1 = state.z1 + dt * (state.z2 + config.b0 * u_applied) + g1 * error
    state.z2 = state.z2 + g2 * error
    state._last_u_applied = u_applied


def _run_thermal_c_ticks(
    state: LadrcState,
    config: LadrcConfig,
    *,
    use_exp_map: bool,
) -> list[float]:
    """Plant write clamp(u_ff+u_track); ESO known input (command−u_ff)."""
    u_tracks: list[float] = []
    for _ in range(_N_TICKS):
        u_track = state.compute_tracking(_Y, _T_R, config, _ZONE)
        u_tracks.append(u_track)
        command = min(_CLAMP_MAX, max(_CLAMP_MIN, _U_FF + u_track))
        u = command - _U_FF
        if use_exp_map:
            _advance_exp_map(state, _Y, u, config)
        else:
            state.advance(_Y, u, config)
    return u_tracks


def _run_huang_absolute_exp_map_ticks(
    state: LadrcState, config: LadrcConfig
) -> list[float]:
    """Pre-fix path: Huang gains + absolute SWT into frozen exp_map."""
    u_tracks: list[float] = []
    for _ in range(_N_TICKS):
        u_track = state.compute_tracking(_Y, _T_R, config, _ZONE)
        u_tracks.append(u_track)
        command = min(_CLAMP_MAX, max(_CLAMP_MIN, _U_FF + u_track))
        _advance_exp_map(state, _Y, command, config)
    return u_tracks


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
    """One-step thermal continuous-form: nonzero modest |Δz1| at dt=60."""
    config = _thermal_config()
    state = LadrcState(z1=18.0, z2=0.0)
    z1_prev = state.z1
    state.advance(20.0, 0.0, config)
    delta = abs(state.z1 - z1_prev)
    assert math.isfinite(state.z1)
    assert math.isfinite(state.z2)
    # Lower bound rules out vacuous z1=y / u=0 (Δz1≡0); upper tightened vs 5.0.
    assert 1.0 < delta < 3.0


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


def test_cap5_exp_map_thermal_c_diverges():
    """Frozen exp_map + thermal+C: track blows (non-finite or |u_track|≥1e6)."""
    config = _thermal_config()
    state = LadrcState()
    u_tracks = _run_thermal_c_ticks(state, config, use_exp_map=True)
    assert any((not math.isfinite(u)) or abs(u) >= 1e6 for u in u_tracks)


def test_cap3a_huang_absolute_exp_map_diverges():
    """CAP-3a Huang half: frozen exp_map + Huang + absolute SWT diverges."""
    config = _default_config()
    state = LadrcState()
    u_tracks = _run_huang_absolute_exp_map_ticks(state, config)
    assert any((not math.isfinite(u)) or abs(u) >= 1e6 for u in u_tracks)


def test_cap5_continuous_thermal_c_bounded():
    """Production continuous-form + thermal+C: |u_track|<100 every tick for N=80."""
    config = _thermal_config()
    state = LadrcState()
    u_tracks = _run_thermal_c_ticks(state, config, use_exp_map=False)
    assert all(math.isfinite(u) for u in u_tracks)
    assert math.isfinite(state.z1)
    assert math.isfinite(state.z2)
    assert all(abs(u) < 100.0 for u in u_tracks)


def test_cap3b_example_aligned_continuous_c_bounded():
    """CAP-3(b): example gains + continuous + C stay under u_track_max."""
    config = _example_aligned_config()
    state = LadrcState()
    u_tracks = _run_thermal_c_ticks(state, config, use_exp_map=False)
    assert all(math.isfinite(u) for u in u_tracks)
    assert math.isfinite(state.z1)
    assert math.isfinite(state.z2)
    assert all(abs(u) < config.u_track_max for u in u_tracks)


def test_ai1_example_cold_start_e2_no_trip():
    """Package A (тепло): after zone reset, |e|=2 → |u_track| under u_track_max."""
    config = _example_aligned_config()
    state = LadrcState()
    measured, reference = 19.0, 21.0  # |e|=2
    u_track = state.compute_tracking(measured, reference, config, _ZONE)
    assert math.isfinite(u_track)
    assert abs(u_track) < config.u_track_max
    assert abs(abs(u_track) - config.omega_c * 2.0 / config.b0) < 1e-9


def test_ai1_example_cold_start_e5_may_trip():
    """Package A: |e|=5 → |u_track| exceeds u_track_max (guard may trip)."""
    config = _example_aligned_config()
    state = LadrcState()
    measured, reference = 16.0, 21.0  # |e|=5
    u_track = state.compute_tracking(measured, reference, config, _ZONE)
    assert math.isfinite(u_track)
    assert abs(u_track) > config.u_track_max
