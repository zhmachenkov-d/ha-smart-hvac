---
type: Concept
title: ADRC
description: Active Disturbance Rejection Control — estimate and cancel total disturbance each sample, then apply a simple outer controller.
tags: [control, adrc, plant]
timestamp: 2026-07-08T15:45:00Z
---

# ADRC

**Active Disturbance Rejection Control** (Han, 1998) treats unknown dynamics and external effects as a single [total disturbance](/concepts/total-disturbance.md), estimates it with an [extended state observer (ESO)](/concepts/extended-state-observer.md), and cancels it so a modest outer loop can track the reference.

Original ADRC uses nonlinear ESO and nonlinear feedback; parameter tuning is awkward. [LADRC](/concepts/ladrc.md) (Gao) keeps the same structure with linear observer and controller. [MADRC](/concepts/madrc.md) keeps that linear core but delays the ESO command path to cope with high-order inertia.

## In this project

`CONTEXT.md` **ADRC Controller** is the App component that applies ADRC ideas to [Set Water Temperature](/concepts/set-water-temperature.md). How that shares the OpenTherm write with the [Multi-Zone Coordinator](/concepts/multi-zone-coordinator.md) is still open (no Decision filed yet).

Literature:

- HVAC air loop (LADRC vs PID): [/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md)
- High-order lag / wide operating range (adaptive MADRC, field): [/references/wang-2026-madrc-sst.md](/references/wang-2026-madrc-sst.md)

## Related

- [/concepts/ladrc.md](/concepts/ladrc.md)
- [/concepts/madrc.md](/concepts/madrc.md)
- [/concepts/extended-state-observer.md](/concepts/extended-state-observer.md)
- [/concepts/plant.md](/concepts/plant.md)

# Citations

- [/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md) §1, §3.1
- [/references/wang-2026-madrc-sst.md](/references/wang-2026-madrc-sst.md) §3
