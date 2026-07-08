---
type: Concept
title: Multi-Zone Coordinator
description: App logic that picks the Critical Zone and turns its need plus Outdoor Temperature into desired Plant water temperature.
tags: [zone, control]
timestamp: 2026-07-08T15:34:24Z
---

# Multi-Zone Coordinator

The **Multi-Zone Coordinator** computes [Zone Error](/concepts/zone-error.md) per [Zone](/concepts/zone.md), selects the [Critical Zone](/concepts/critical-zone.md), and passes its air temperature and reference setpoint to the [ADRC Controller](/concepts/adrc.md). It does not own the OpenTherm write to [Set Water Temperature](/concepts/set-water-temperature.md).

Not a thermostat or scheduler unless that is all it does.

Huang et al. (2018) study a **single** zone LADRC loop — no multi-zone coordination ([/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md)).

# Citations

- [`CONTEXT.md`](../../CONTEXT.md) — Multi-Zone Coordinator
