"""Tests for online LADRC omega_c adaptation."""

import json
from pathlib import Path

import pytest
from hvac.config import ConfigError, parse_config
from hvac.ladrc_tuner import LadrcTuner
from hvac.models import LadrcConfig, LadrcTuneConfig


def _default_tune() -> LadrcTuneConfig:
    return LadrcTuneConfig(
        ki=0.005,
        deadband=0.2,
        min_steady_ticks=5,
        max_rate_fraction=0.05,
    )


def _default_config() -> LadrcConfig:
    return LadrcConfig(
        b0=2.8,
        omega_o=19.49,
        omega_c=0.053,
        omega_c_min=0.02,
        omega_c_max=0.15,
        tune=_default_tune(),
        dt=60.0,
    )


def _tuner(tmp_path: Path, config: LadrcConfig | None = None) -> LadrcTuner:
    return LadrcTuner(config or _default_config(), tmp_path / "ladrc_tune_state.json")


def _steady_adapt(
    tuner: LadrcTuner,
    *,
    zone: str = "living_room",
    error: float = 1.0,
    ticks: int = 5,
) -> float | None:
    result: float | None = None
    for _ in range(ticks):
        result = tuner.maybe_adapt(error, zone, has_demand=True)
    return result


def test_deadband_blocks_adaptation(tmp_path: Path) -> None:
    tuner = _tuner(tmp_path)
    assert _steady_adapt(tuner, error=0.1) is None
    assert tuner.omega_c == pytest.approx(0.053)


def test_steady_tick_gate(tmp_path: Path) -> None:
    tuner = _tuner(tmp_path)
    for _ in range(4):
        assert tuner.maybe_adapt(1.0, "living_room", has_demand=True) is None
    assert tuner.omega_c == pytest.approx(0.053)


def test_adapts_after_steady_ticks(tmp_path: Path) -> None:
    tuner = _tuner(tmp_path)
    new_omega_c = _steady_adapt(tuner, error=1.0)
    assert new_omega_c is not None
    assert new_omega_c > 0.053


def test_rate_limit_clamps_per_tick_change(tmp_path: Path) -> None:
    tuner = _tuner(tmp_path)
    new_omega_c = _steady_adapt(tuner, error=100.0)
    assert new_omega_c is not None
    max_delta = 0.05 * 0.053
    assert new_omega_c <= 0.053 + max_delta + 1e-12


def test_bounds_clamp_high(tmp_path: Path) -> None:
    config = LadrcConfig(
        b0=2.8,
        omega_o=19.49,
        omega_c=0.14,
        omega_c_min=0.02,
        omega_c_max=0.15,
        tune=LadrcTuneConfig(
            ki=1.0,
            deadband=0.0,
            min_steady_ticks=1,
            max_rate_fraction=1.0,
        ),
        dt=60.0,
    )
    tuner = _tuner(tmp_path, config)
    new_omega_c = tuner.maybe_adapt(10.0, "living_room", has_demand=True)
    assert new_omega_c == pytest.approx(0.15)


def test_bounds_clamp_low(tmp_path: Path) -> None:
    config = LadrcConfig(
        b0=2.8,
        omega_o=19.49,
        omega_c=0.03,
        omega_c_min=0.02,
        omega_c_max=0.15,
        tune=LadrcTuneConfig(
            ki=1.0,
            deadband=0.0,
            min_steady_ticks=1,
            max_rate_fraction=1.0,
        ),
        dt=60.0,
    )
    tuner = _tuner(tmp_path, config)
    new_omega_c = tuner.maybe_adapt(-10.0, "living_room", has_demand=True)
    assert new_omega_c == pytest.approx(0.02)


def test_zone_switch_freezes_adaptation(tmp_path: Path) -> None:
    tuner = _tuner(tmp_path)
    for _ in range(4):
        tuner.maybe_adapt(1.0, "living_room", has_demand=True)
    assert tuner.maybe_adapt(1.0, "bedroom", has_demand=True) is None
    assert tuner.omega_c == pytest.approx(0.053)


def test_no_demand_resets_steady_counter(tmp_path: Path) -> None:
    tuner = _tuner(tmp_path)
    for _ in range(4):
        tuner.maybe_adapt(1.0, "living_room", has_demand=True)
    tuner.maybe_adapt(1.0, "living_room", has_demand=False)
    assert tuner.maybe_adapt(1.0, "living_room", has_demand=True) is None


def test_json_round_trip(tmp_path: Path) -> None:
    state_path = tmp_path / "ladrc_tune_state.json"
    tuner = LadrcTuner(_default_config(), state_path)
    _steady_adapt(tuner, error=1.0)
    assert state_path.is_file()

    reloaded = LadrcTuner(_default_config(), state_path)
    assert reloaded.omega_c == tuner.omega_c


def test_corrupt_json_falls_back_to_config_initial(tmp_path: Path) -> None:
    state_path = tmp_path / "ladrc_tune_state.json"
    state_path.write_text("not json", encoding="utf-8")
    tuner = LadrcTuner(_default_config(), state_path)
    assert tuner.omega_c == pytest.approx(0.053)


def test_out_of_bounds_persisted_value_ignored(tmp_path: Path) -> None:
    state_path = tmp_path / "ladrc_tune_state.json"
    state_path.write_text(json.dumps({"omega_c": 0.5}), encoding="utf-8")
    tuner = LadrcTuner(_default_config(), state_path)
    assert tuner.omega_c == pytest.approx(0.053)


def test_parse_bandwidth_ladrc_config() -> None:
    config = parse_config(
        {
            "outdoor_temperature": "sensor.outdoor",
            "plant_management": "switch.pm",
            "plant_setpoint": "number.setpoint",
            "setpoint_min": 40,
            "setpoint_max": 55,
            "zones": [
                {
                    "name": "living_room",
                    "temperature": "sensor.temp",
                    "thermostats": ["climate.thermostat"],
                }
            ],
            "weather_feedforward": {
                "base": 25,
                "slope": 1.2,
                "comfort_ref": 20,
            },
            "ladrc": {
                "b0": 2.8,
                "omega_o": 19.49,
                "omega_c": 0.053,
                "omega_c_min": 0.02,
                "omega_c_max": 0.15,
                "tune": {
                    "ki": 0.005,
                    "deadband": 0.2,
                    "min_steady_ticks": 5,
                    "max_rate_fraction": 0.05,
                },
            },
        }
    )
    assert config.ladrc.kp == pytest.approx(0.053)
    assert config.ladrc.beta2 == pytest.approx(19.49**2)


def test_parse_rejects_omega_c_outside_bounds() -> None:
    with pytest.raises(ConfigError, match="omega_c must be strictly between"):
        parse_config(
            {
                "outdoor_temperature": "sensor.outdoor",
                "plant_management": "switch.pm",
                "plant_setpoint": "number.setpoint",
                "setpoint_min": 40,
                "setpoint_max": 55,
                "zones": [
                    {
                        "name": "living_room",
                        "temperature": "sensor.temp",
                        "thermostats": ["climate.thermostat"],
                    }
                ],
                "weather_feedforward": {
                    "base": 25,
                    "slope": 1.2,
                    "comfort_ref": 20,
                },
                "ladrc": {
                    "b0": 2.8,
                    "omega_o": 19.49,
                    "omega_c": 0.2,
                    "omega_c_min": 0.02,
                    "omega_c_max": 0.15,
                    "tune": {
                        "ki": 0.005,
                        "deadband": 0.2,
                        "min_steady_ticks": 5,
                        "max_rate_fraction": 0.05,
                    },
                },
            }
        )
