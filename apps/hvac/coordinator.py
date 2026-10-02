"""Multi-Zone Coordinator — Critical Zone selection."""

from __future__ import annotations

from hvac.models import ControlDecision, ZoneSnapshot


def select_critical_zone(zones: list[ZoneSnapshot]) -> ControlDecision:
    """Pick the zone with the largest positive zone error."""
    if not zones:
        return ControlDecision(
            critical_zone=None,
            reference=None,
            measured=None,
            zone_error=0.0,
            has_demand=False,
        )

    best = max(zones, key=lambda z: z.zone_error)
    has_demand = best.zone_error > 0

    if not has_demand:
        return ControlDecision(
            critical_zone=None,
            reference=None,
            measured=None,
            zone_error=best.zone_error,
            has_demand=False,
        )

    return ControlDecision(
        critical_zone=best.name,
        reference=best.reference_setpoint(),
        measured=best.zone_temp,
        zone_error=best.zone_error,
        has_demand=True,
    )
