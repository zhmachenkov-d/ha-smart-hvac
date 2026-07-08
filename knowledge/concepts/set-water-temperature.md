---
type: Concept
title: Set Water Temperature
description: OpenTherm boiler water setpoint the App commands on the Plant.
tags: [plant, opentherm]
timestamp: 2026-07-08T15:34:24Z
---

# Set Water Temperature

**Set Water Temperature** is the OpenTherm boiler water setpoint the App commands on the [Plant](/concepts/plant.md) (the boiler’s target water temperature via OpenTherm).

Not the same as a Zone thermostat air setpoint or a mixer setpoint.

The [ADRC Controller](/concepts/adrc.md) owns this write: [Weather Feedforward](/concepts/outdoor-temperature.md) plus LADRC tracking when a Zone has Heating Demand, or **0** when idle. The [Multi-Zone Coordinator](/concepts/multi-zone-coordinator.md) supplies Critical Zone readings only.

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Set Water Temperature
