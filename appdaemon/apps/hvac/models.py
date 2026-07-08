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
    hvac_action: str | None = None


@dataclass(frozen=True)
class ZoneSnapshot:
    name: str
    zone_temp: float
    thermostats: tuple[ThermostatReading, ...]

    def _eligible_thermostats(self) -> tuple[ThermostatReading, ...]:
        return tuple(t for t in self.thermostats if t.hvac_action == "heating")

    @property
    def zone_error(self) -> float:
        thermostats = self._eligible_thermostats()
        if not thermostats:
            return float("-inf")
        return max(t.setpoint - self.zone_temp for t in thermostats)

    def reference_setpoint(self) -> float:
        """Setpoint of the thermostat with the largest error in this zone."""
        thermostats = self._eligible_thermostats()
        if not thermostats:
            raise ValueError("Zone has no eligible heating thermostats")
        best = max(
            thermostats,
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
