"""HVAC App — 60 s LADRC control loop."""

from __future__ import annotations

import math
from typing import NamedTuple

import appdaemon.plugins.hass.hassapi as hass

from hvac.config import ConfigError, parse_config
from hvac.coordinator import select_critical_zone
from hvac.feedforward import weather_feedforward
from hvac.ladrc import LadrcState
from hvac.ladrc_tuner import LadrcTuner
from hvac.models import (
    HvacConfig,
    LadrcConfig,
    ThermostatReading,
    ZoneSnapshot,
    plant_management_enabled,
)


def advance_with_tracking_residue(
    ladrc: LadrcState,
    measured: float,
    command: float,
    u_ff: float,
    config: LadrcConfig,
) -> None:
    """Advance ESO with post-clamp tracking residue (command − u_ff)."""
    ladrc.advance(measured, command - u_ff, config)


class GuardUTrackResult(NamedTuple):
    command: float
    tripped: bool
    should_warn: bool
    latch_out: bool
    reason: str | None


def guard_u_track(
    ladrc: LadrcState,
    measured: float,
    u_track: float,
    u_ff: float,
    u_track_max: float,
    setpoint_min: float,
    setpoint_max: float,
    latch_in: bool,
) -> GuardUTrackResult:
    """Detect exploded u_track; on trip reset ESO and return ff-only command."""
    if not math.isfinite(u_track):
        tripped = True
        reason: str | None = "non-finite"
    elif abs(u_track) > u_track_max:
        tripped = True
        reason = "magnitude"
    else:
        tripped = False
        reason = None

    if tripped:
        ladrc.reset(measured)
        command = max(setpoint_min, min(setpoint_max, u_ff))
    else:
        command = max(setpoint_min, min(setpoint_max, u_ff + u_track))

    return GuardUTrackResult(
        command=command,
        tripped=tripped,
        should_warn=tripped and not latch_in,
        latch_out=tripped,
        reason=reason,
    )


def _safe_u_track_render(u_track: float) -> str:
    if math.isnan(u_track):
        return "nan"
    if math.isinf(u_track):
        return "inf" if u_track > 0 else "-inf"
    return f"{u_track}"


def format_blow_up_warning(
    reason: str,
    u_track: float,
    u_track_max: float,
    critical_zone: str,
) -> str:
    """WARNING string with Floor MUST fields (prose free beyond those)."""
    return (
        f"LADRC blow-up guard: reason={reason}, "
        f"u_track={_safe_u_track_render(u_track)}, "
        f"u_track_max={u_track_max}, critical_zone={critical_zone}"
    )


class HvacApp(hass.Hass):
    def initialize(self) -> None:
        try:
            self._config: HvacConfig = parse_config(self.args)
        except ConfigError as exc:
            self.log(f"HVAC config error: {exc}", level="ERROR")
            return

        self._ladrc = LadrcState()
        self._blow_up_latch = False
        tune_state_path = self.app_dir / self._config.tune_state_path
        self._tuner = LadrcTuner(self._config.ladrc, tune_state_path)
        self.run_every(
            self.control_tick,
            "now",
            self._config.control_interval,
        )
        self.log("HVAC LADRC app initialized")

    def control_tick(self, kwargs: dict) -> None:
        config = self._config
        if not plant_management_enabled(self.get_state(config.plant_management)):
            self._hands_off("Plant Management disabled")
            return

        outdoor = self._read_float(config.outdoor_temperature)
        if outdoor is None:
            self._go_idle(
                f"Outdoor temperature unavailable: {config.outdoor_temperature}"
            )
            return

        zones = self._read_zones(config)
        if not zones:
            self._go_idle("No zones with valid readings this tick")
            return

        decision = select_critical_zone(zones)

        if not decision.has_demand:
            self._ladrc.clear()
            self._tuner.clear_steady()
            self._blow_up_latch = False
            self._write_setpoint(0.0)
            self.log(
                f"No heating demand (max zone error {decision.zone_error:.2f} °C); "
                "setpoint 0"
            )
            return

        tracking_error = decision.reference - self._ladrc.z1
        new_omega_c = self._tuner.maybe_adapt(
            tracking_error,
            decision.critical_zone,
            decision.has_demand,
            apply=False,
        )
        effective_ladrc = config.ladrc.with_omega_c(
            new_omega_c if new_omega_c is not None else self._tuner.omega_c
        )

        u_ff = weather_feedforward(outdoor, config.weather_feedforward)
        u_track = self._ladrc.compute_tracking(
            measured=decision.measured,
            reference=decision.reference,
            config=effective_ladrc,
            critical_zone=decision.critical_zone,
        )
        guard = guard_u_track(
            self._ladrc,
            decision.measured,
            u_track,
            u_ff,
            effective_ladrc.u_track_max,
            config.setpoint_min,
            config.setpoint_max,
            self._blow_up_latch,
        )
        self._blow_up_latch = guard.latch_out
        if guard.should_warn:
            self.log(
                format_blow_up_warning(
                    guard.reason or "unknown",
                    u_track,
                    effective_ladrc.u_track_max,
                    decision.critical_zone,
                ),
                level="WARNING",
            )
        if not self._write_setpoint(guard.command):
            return

        advance_with_tracking_residue(
            self._ladrc,
            decision.measured,
            guard.command,
            u_ff,
            effective_ladrc,
        )
        if new_omega_c is not None:
            self._tuner.commit_omega_c(new_omega_c)
        self._tuner.publish_sensor(self)
        if guard.tripped:
            self.log(
                f"Critical zone {decision.critical_zone}: "
                f"error={decision.zone_error:.2f} °C, "
                f"y={decision.measured:.2f} °C, T_r={decision.reference:.2f} °C, "
                f"u_ff={u_ff:.2f}, command={guard.command:.2f} guarded"
            )
        else:
            self.log(
                f"Critical zone {decision.critical_zone}: "
                f"error={decision.zone_error:.2f} °C, "
                f"y={decision.measured:.2f} °C, T_r={decision.reference:.2f} °C, "
                f"u_ff={u_ff:.2f}, u_track={u_track:.2f}, "
                f"command={guard.command:.2f}"
            )

    def _hands_off(self, message: str) -> None:
        self._ladrc.clear()
        self._tuner.clear_steady()
        self._blow_up_latch = False
        self.log(message, level="WARNING")

    def _go_idle(self, message: str) -> None:
        self._ladrc.clear()
        self._tuner.clear_steady()
        self._blow_up_latch = False
        self._write_setpoint(0.0)
        self.log(message, level="WARNING")

    def _read_zones(self, config: HvacConfig) -> list[ZoneSnapshot]:
        snapshots: list[ZoneSnapshot] = []
        for zone in config.zones:
            zone_temp = self._read_float(zone.temperature)
            if zone_temp is None:
                self.log(
                    f"Zone {zone.name}: temperature unavailable ({zone.temperature})",
                    level="WARNING",
                )
                continue

            thermostats: list[ThermostatReading] = []
            for entity_id in zone.thermostats:
                setpoint = self._read_setpoint(entity_id)
                if setpoint is None:
                    self.log(
                        f"Zone {zone.name}: thermostat unavailable ({entity_id})",
                        level="WARNING",
                    )
                    continue
                thermostats.append(
                    ThermostatReading(
                        entity_id=entity_id,
                        setpoint=setpoint,
                        hvac_action=self._read_hvac_action(entity_id),
                    )
                )

            if not thermostats:
                continue

            snapshots.append(
                ZoneSnapshot(
                    name=zone.name,
                    zone_temp=zone_temp,
                    thermostats=tuple(thermostats),
                )
            )
        return snapshots

    def _read_float(self, entity_id: str) -> float | None:
        state = self.get_state(entity_id)
        if state in (None, "unavailable", "unknown"):
            return None
        try:
            return float(state)
        except (TypeError, ValueError):
            return None

    def _read_setpoint(self, entity_id: str) -> float | None:
        value = self.get_state(entity_id, attribute="temperature")
        if value in (None, "unavailable", "unknown"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _read_hvac_action(self, entity_id: str) -> str | None:
        value = self.get_state(entity_id, attribute="hvac_action")
        if value in (None, "unavailable", "unknown"):
            return None
        return str(value)

    def _write_setpoint(self, value: float) -> bool:
        entity_id = self._config.plant_setpoint
        if self.get_state(entity_id) in (None, "unavailable", "unknown"):
            self.log(
                f"Plant setpoint unavailable: {entity_id}",
                level="WARNING",
            )
            return False
        self.call_service(
            "number/set_value",
            entity_id=entity_id,
            value=value,
        )
        return True
