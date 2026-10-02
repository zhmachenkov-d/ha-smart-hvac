"""Validate and parse apps.yaml arguments."""

from __future__ import annotations

from typing import Any

from hvac.models import (
    HvacConfig,
    LadrcConfig,
    LadrcTuneConfig,
    WeatherFeedforwardConfig,
    ZoneConfig,
)


class ConfigError(ValueError):
    pass


def _require(mapping: dict[str, Any], key: str) -> Any:
    if key not in mapping:
        raise ConfigError(f"Missing required config key: {key}")
    return mapping[key]


def _parse_zone(raw: Any) -> ZoneConfig:
    if not isinstance(raw, dict):
        raise ConfigError("Each zone must be a mapping")
    name = _require(raw, "name")
    temperature = _require(raw, "temperature")
    thermostats = _require(raw, "thermostats")
    if not isinstance(name, str) or not name:
        raise ConfigError("Zone name must be a non-empty string")
    if not isinstance(temperature, str) or not temperature:
        raise ConfigError(f"Zone {name!r}: temperature must be a non-empty entity id")
    if not isinstance(thermostats, list) or not thermostats:
        raise ConfigError(f"Zone {name!r}: thermostats must be a non-empty list")
    for entity_id in thermostats:
        if not isinstance(entity_id, str) or not entity_id:
            raise ConfigError(f"Zone {name!r}: invalid thermostat entity id")
    return ZoneConfig(
        name=name, temperature=temperature, thermostats=tuple(thermostats)
    )


def _parse_weather_feedforward(raw: Any) -> WeatherFeedforwardConfig:
    if not isinstance(raw, dict):
        raise ConfigError("weather_feedforward must be a mapping")
    return WeatherFeedforwardConfig(
        base=float(_require(raw, "base")),
        slope=float(_require(raw, "slope")),
        comfort_ref=float(_require(raw, "comfort_ref")),
    )


def _parse_ladrc_tune(raw: Any) -> LadrcTuneConfig:
    if not isinstance(raw, dict):
        raise ConfigError("ladrc.tune must be a mapping")
    min_steady_ticks = int(_require(raw, "min_steady_ticks"))
    if min_steady_ticks <= 0:
        raise ConfigError("ladrc.tune.min_steady_ticks must be positive")
    max_rate_fraction = float(_require(raw, "max_rate_fraction"))
    if max_rate_fraction <= 0:
        raise ConfigError("ladrc.tune.max_rate_fraction must be positive")
    return LadrcTuneConfig(
        ki=float(_require(raw, "ki")),
        deadband=float(_require(raw, "deadband")),
        min_steady_ticks=min_steady_ticks,
        max_rate_fraction=max_rate_fraction,
    )


def _parse_ladrc(raw: Any, control_interval: int) -> LadrcConfig:
    if not isinstance(raw, dict):
        raise ConfigError("ladrc must be a mapping")
    omega_c_min = float(_require(raw, "omega_c_min"))
    omega_c_max = float(_require(raw, "omega_c_max"))
    omega_c = float(_require(raw, "omega_c"))
    if omega_c_min >= omega_c_max:
        raise ConfigError("ladrc.omega_c_min must be less than ladrc.omega_c_max")
    if not omega_c_min < omega_c < omega_c_max:
        raise ConfigError(
            "ladrc.omega_c must be strictly between omega_c_min and omega_c_max"
        )
    return LadrcConfig(
        b0=float(_require(raw, "b0")),
        omega_o=float(_require(raw, "omega_o")),
        omega_c=omega_c,
        omega_c_min=omega_c_min,
        omega_c_max=omega_c_max,
        tune=_parse_ladrc_tune(_require(raw, "tune")),
        dt=float(control_interval),
    )


def parse_config(args: dict[str, Any]) -> HvacConfig:
    """Parse AppDaemon app arguments into a validated HvacConfig."""
    outdoor_temperature = _require(args, "outdoor_temperature")
    plant_management = _require(args, "plant_management")
    plant_setpoint = _require(args, "plant_setpoint")
    if not isinstance(outdoor_temperature, str) or not outdoor_temperature:
        raise ConfigError("outdoor_temperature must be a non-empty entity id")
    if not isinstance(plant_management, str) or not plant_management:
        raise ConfigError("plant_management must be a non-empty entity id")
    if not isinstance(plant_setpoint, str) or not plant_setpoint:
        raise ConfigError("plant_setpoint must be a non-empty entity id")

    setpoint_min = float(_require(args, "setpoint_min"))
    setpoint_max = float(_require(args, "setpoint_max"))
    if setpoint_min >= setpoint_max:
        raise ConfigError("setpoint_min must be less than setpoint_max")

    control_interval = int(args.get("control_interval", 60))
    if control_interval <= 0:
        raise ConfigError("control_interval must be positive")

    zones_raw = _require(args, "zones")
    if not isinstance(zones_raw, list) or not zones_raw:
        raise ConfigError("zones must be a non-empty list")

    tune_state_path = args.get("tune_state_path", "ladrc_tune_state.json")
    if not isinstance(tune_state_path, str) or not tune_state_path:
        raise ConfigError("tune_state_path must be a non-empty string")

    return HvacConfig(
        outdoor_temperature=outdoor_temperature,
        plant_management=plant_management,
        plant_setpoint=plant_setpoint,
        setpoint_min=setpoint_min,
        setpoint_max=setpoint_max,
        control_interval=control_interval,
        weather_feedforward=_parse_weather_feedforward(
            _require(args, "weather_feedforward")
        ),
        ladrc=_parse_ladrc(_require(args, "ladrc"), control_interval),
        tune_state_path=tune_state_path,
        zones=tuple(_parse_zone(z) for z in zones_raw),
    )
