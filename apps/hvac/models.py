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
class LadrcTuneConfig:
    ki: float
    deadband: float
    min_steady_ticks: int
    max_rate_fraction: float


@dataclass(frozen=True)
class LadrcConfig:
    b0: float
    omega_o: float
    omega_c: float
    omega_c_min: float
    omega_c_max: float
    tune: LadrcTuneConfig
    dt: float = 60.0

    @property
    def kp(self) -> float:
        return self.omega_c

    @property
    def beta2(self) -> float:
        return self.omega_o * self.omega_o

    def with_omega_c(self, omega_c: float) -> LadrcConfig:
        return LadrcConfig(
            b0=self.b0,
            omega_o=self.omega_o,
            omega_c=omega_c,
            omega_c_min=self.omega_c_min,
            omega_c_max=self.omega_c_max,
            tune=self.tune,
            dt=self.dt,
        )


def plant_management_enabled(switch_state: str | None) -> bool:
    return switch_state == "on"


@dataclass(frozen=True)
class HvacConfig:
    outdoor_temperature: str
    plant_management: str
    plant_setpoint: str
    setpoint_min: float
    setpoint_max: float
    control_interval: int
    weather_feedforward: WeatherFeedforwardConfig
    ladrc: LadrcConfig
    tune_state_path: str
    zones: tuple[ZoneConfig, ...]
