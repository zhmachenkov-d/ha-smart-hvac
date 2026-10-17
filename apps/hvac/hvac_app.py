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
    u_track: float,
    u_ff: float,
    u_track_max: float,
    setpoint_min: float,
    setpoint_max: float,
    latch_in: bool,
) -> GuardUTrackResult:
    """Detect exploded u_track; on trip return ff-only command (no ESO mutate).

    Caller resets the ESO only after a successful plant write (AI-6).
    """
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


def latch_after_zone_change(
    prev_zone: str | None,
    new_zone: str | None,
    latch_in: bool,
) -> bool:
    """Clear blow-up latch only when Critical Zone actually changes."""
    if prev_zone is not None and prev_zone != new_zone:
        return False
    return latch_in


def should_commit_omega_c(
    proposed: float | None,
    current: float,
    *,
    guard_tripped: bool,
    command: float,
    setpoint_min: float,
    setpoint_max: float,
) -> bool:
    """Directional clamp + guard trip gate for applying/committing proposed ωc."""
    if proposed is None:
        return False
    if guard_tripped:
        return False
    if command >= setpoint_max and proposed > current:
        return False
    if command <= setpoint_min and proposed < current:
        return False
    return True


# CAP-4: latch-decay stop band as a fraction of u_track_max (not a yaml knob).
LATCH_DECAY_U_TRACK_FRACTION = 0.8


def latch_decay_residue_holds(u_track: float, u_track_max: float) -> bool:
    """True when latched decay should continue (high or non-finite |u_track|)."""
    if not math.isfinite(u_track):
        return True
    return abs(u_track) > LATCH_DECAY_U_TRACK_FRACTION * u_track_max


def next_decayed_omega_c(
    current: float,
    max_rate_fraction: float,
    omega_c_min: float,
) -> float:
    """One max_rate_fraction step down, floored at omega_c_min."""
    step = max_rate_fraction * current
    return max(omega_c_min, current - step)


def sticky_blow_up_latch(
    latch_in: bool,
    tripped: bool,
    u_track: float,
    u_track_max: float,
) -> bool:
    """CAP-4 sticky soft-kill: hold while residue is above the 0.8 band."""
    return tripped or (latch_in and latch_decay_residue_holds(u_track, u_track_max))


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

        # CAP-4: skip adapt when latch already active at tick start.
        latch_at_start = self._blow_up_latch
        tracking_error = decision.reference - self._ladrc.z1
        if latch_at_start:
            new_omega_c = None
        else:
            new_omega_c = self._tuner.maybe_adapt(
                tracking_error,
                decision.critical_zone,
                decision.has_demand,
                apply=False,
            )
        current_omega_c = self._tuner.omega_c
        committed_ladrc = config.ladrc.with_omega_c(current_omega_c)

        u_ff = weather_feedforward(outdoor, config.weather_feedforward)
        prev_zone = self._ladrc.critical_zone
        self._blow_up_latch = latch_after_zone_change(
            prev_zone,
            decision.critical_zone,
            self._blow_up_latch,
        )
        # latch_in for sticky CAP-4 (same value passed to the write-path guard).
        latch_in = self._blow_up_latch

        # Strict apply: provisional track+guard with proposed ωc decides apply;
        # blocked proposals never enter write-path tracking (CAP-2).
        apply_proposed = False
        if new_omega_c is not None:
            proposed_ladrc = config.ladrc.with_omega_c(new_omega_c)
            u_track = self._ladrc.compute_tracking(
                measured=decision.measured,
                reference=decision.reference,
                config=proposed_ladrc,
                critical_zone=decision.critical_zone,
            )
            guard = guard_u_track(
                u_track,
                u_ff,
                proposed_ladrc.u_track_max,
                config.setpoint_min,
                config.setpoint_max,
                latch_in,
            )
            apply_proposed = should_commit_omega_c(
                new_omega_c,
                current_omega_c,
                guard_tripped=guard.tripped,
                command=guard.command,
                setpoint_min=config.setpoint_min,
                setpoint_max=config.setpoint_max,
            )
            if apply_proposed:
                effective_ladrc = proposed_ladrc
            else:
                # Discard provisional; final track+guard with committed ωc.
                # Do not re-eval the helper on this final guard (no resurrect).
                u_track = self._ladrc.compute_tracking(
                    measured=decision.measured,
                    reference=decision.reference,
                    config=committed_ladrc,
                    critical_zone=decision.critical_zone,
                )
                guard = guard_u_track(
                    u_track,
                    u_ff,
                    committed_ladrc.u_track_max,
                    config.setpoint_min,
                    config.setpoint_max,
                    latch_in,
                )
                effective_ladrc = committed_ladrc
        else:
            u_track = self._ladrc.compute_tracking(
                measured=decision.measured,
                reference=decision.reference,
                config=committed_ladrc,
                critical_zone=decision.critical_zone,
            )
            guard = guard_u_track(
                u_track,
                u_ff,
                committed_ladrc.u_track_max,
                config.setpoint_min,
                config.setpoint_max,
                latch_in,
            )
            effective_ladrc = committed_ladrc

        # Sticky CAP-4 latch from write-path guard (not latch_out alone).
        self._blow_up_latch = sticky_blow_up_latch(
            latch_in,
            guard.tripped,
            u_track,
            effective_ladrc.u_track_max,
        )
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
        # AI-6: reset ESO only after successful plant write (not inside guard).
        if guard.tripped:
            self._ladrc.reset(decision.measured)

        advance_with_tracking_residue(
            self._ladrc,
            decision.measured,
            guard.command,
            u_ff,
            effective_ladrc,
        )
        # CAP-4 decay persist (even when guard trip blocks normal commit).
        if self._blow_up_latch and latch_decay_residue_holds(
            u_track, effective_ladrc.u_track_max
        ):
            self._tuner.commit_omega_c(
                next_decayed_omega_c(
                    current_omega_c,
                    effective_ladrc.tune.max_rate_fraction,
                    effective_ladrc.omega_c_min,
                )
            )
        else:
            # Commit only on applied proposals via helper on the write-path guard.
            # Blocked apply passes None so a final interior command cannot resurrect.
            omega_to_commit = new_omega_c if apply_proposed else None
            if should_commit_omega_c(
                omega_to_commit,
                current_omega_c,
                guard_tripped=guard.tripped,
                command=guard.command,
                setpoint_min=config.setpoint_min,
                setpoint_max=config.setpoint_max,
            ):
                assert omega_to_commit is not None
                self._tuner.commit_omega_c(omega_to_commit)
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
