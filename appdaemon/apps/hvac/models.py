"""Data models for HVAC control."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ZoneConfig:
    name: str
    temperature: str
    thermostats: tuple[str, ...]


@dataclass(frozen=True)
class ThermostatReading:
    entity_id: str
    setpoint: float


@dataclass(frozen=True)
class ZoneSnapshot:
    name: str
    zone_temp: float
    thermostats: tuple[ThermostatReading, ...]

    @property
    def zone_error(self) -> float:
        if not self.thermostats:
            return float("-inf")
        return max(t.setpoint - self.zone_temp for t in self.thermostats)

    def reference_setpoint(self) -> float:
        """Setpoint of the thermostat with the largest error in this zone."""
        best = max(
            self.thermostats,
            key=lambda t: t.setpoint - self.zone_temp,
        )
        return best.setpoint


@dataclass(frozen=True)
class ControlDecision:
    critical_zone: str | None
    reference: float | None
    measured: float | None
    zone_error: float
    has_demand: bool


@dataclass(frozen=True)
class WeatherFeedforwardConfig:
    base: float
    slope: float
    comfort_ref: float


@dataclass(frozen=True)
class LadrcConfig:
    b0: float
    kp: float
    beta1: float
    beta2: float
    dt: float = 60.0


@dataclass(frozen=True)
class HvacConfig:
    outdoor_temperature: str
    plant_setpoint: str
    setpoint_min: float
    setpoint_max: float
    control_interval: int
    weather_feedforward: WeatherFeedforwardConfig
    ladrc: LadrcConfig
    zones: tuple[ZoneConfig, ...]
