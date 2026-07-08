---
type: Concept
title: Plant
description: Boiler and primary water circuit supplying heat to Zones, commanded via OpenTherm.
tags: [plant, opentherm]
timestamp: 2026-07-08T15:45:00Z
---

# Plant

The **Plant** is the boiler and primary water circuit that supplies heat to [Zones](/concepts/zone.md), commanded via OpenTherm.

Avoid “HVAC system” (too broad) and “heater” (ambiguous with zone emitters).

Literature plants differ from this OpenTherm [Set Water Temperature](/concepts/set-water-temperature.md) circuit:

- Huang et al. (2018): AHU **coil water flow** → zone air ([/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md))
- Wang et al. (2026): **attemperation water valve** → superheated steam temperature; cascade leading/inert zones ([/references/wang-2026-madrc-sst.md](/references/wang-2026-madrc-sst.md))

Useful for control ideas ([LADRC](/concepts/ladrc.md), [MADRC](/concepts/madrc.md)); not topological templates.

## Related

- [/concepts/set-water-temperature.md](/concepts/set-water-temperature.md)
- [/concepts/adrc.md](/concepts/adrc.md)
- [/concepts/madrc.md](/concepts/madrc.md)
- [/concepts/multi-zone-coordinator.md](/concepts/multi-zone-coordinator.md)

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Plant
