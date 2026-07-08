"""Tests for Multi-Zone Coordinator."""

from hvac.coordinator import select_critical_zone
from hvac.models import ThermostatReading, ZoneSnapshot


def _zone(name: str, temp: float, setpoints: list[float]) -> ZoneSnapshot:
    thermostats = tuple(
        ThermostatReading(f"climate.{name}_{i}", sp) for i, sp in enumerate(setpoints)
    )
    return ZoneSnapshot(name=name, zone_temp=temp, thermostats=thermostats)


def test_picks_zone_with_largest_error():
    zones = [
        _zone("living_room", 18.0, [20.0]),
        _zone("bedroom", 17.0, [21.0]),
    ]
    decision = select_critical_zone(zones)
    assert decision.critical_zone == "bedroom"
    assert decision.zone_error == 4.0
    assert decision.reference == 21.0
    assert decision.measured == 17.0
    assert decision.has_demand is True


def test_multi_thermostat_zone_uses_max_error():
    zones = [
        ZoneSnapshot(
            name="living_room",
            zone_temp=19.0,
            thermostats=(
                ThermostatReading("climate.lr_a", 20.0),
                ThermostatReading("climate.lr_b", 22.0),
            ),
        ),
    ]
    decision = select_critical_zone(zones)
    assert decision.zone_error == 3.0
    assert decision.reference == 22.0


def test_no_demand_when_all_errors_non_positive():
    zones = [
        _zone("living_room", 21.0, [20.0]),
        _zone("bedroom", 20.5, [20.0]),
    ]
    decision = select_critical_zone(zones)
    assert decision.has_demand is False
    assert decision.critical_zone is None
    assert decision.zone_error == -0.5


def test_empty_zones():
    decision = select_critical_zone([])
    assert decision.has_demand is False
