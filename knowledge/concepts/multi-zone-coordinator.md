---
type: Concept
title: Multi-Zone Coordinator
description: App logic that picks the Critical Zone and turns its need plus Outdoor Temperature into desired Plant water temperature.
tags: [zone, control]
timestamp: 2026-07-08T15:34:24Z
---

# Multi-Zone Coordinator

The **Multi-Zone Coordinator** picks the [Critical Zone](/concepts/critical-zone.md) from all [Zones](/concepts/zone.md) and turns its need (plus [Outdoor Temperature](/concepts/outdoor-temperature.md)) into a desired [Plant](/concepts/plant.md) water temperature.

Not a thermostat or scheduler unless that is all it does.

How it shares the OpenTherm write with the [ADRC Controller](/concepts/adrc.md) is still under discussion.

Huang et al. (2018) study a **single** zone LADRC loop — no multi-zone coordination ([/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md)).

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Multi-Zone Coordinator
