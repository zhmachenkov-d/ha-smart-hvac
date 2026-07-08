---
type: Concept
title: Total disturbance
description: ADRC’s lumped unknown — internal model error plus external loads — estimated by the ESO and cancelled in the control law.
tags: [control, adrc]
timestamp: 2026-07-08T15:45:00Z
---

# Total disturbance

In [ADRC](/concepts/adrc.md) / [LADRC](/concepts/ladrc.md) / [MADRC](/concepts/madrc.md), **total disturbance** is the single extended state that stands for everything the controller does not model explicitly: unmodelled dynamics, parameter error, and external loads.

For HVAC air loops, Huang et al. treat effects such as door/window opening as step-like disturbances on the zone. Their Simulink test injects a step at \(t=500\,\mathrm{s}\); LADRC returns to the 20 °C setpoint faster than PID or integral-fuzzy ([/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md)).

In [MADRC](/concepts/madrc.md), after inertia compensation the residual in \(f\) still includes gain/time-constant mismatch relative to \(b_0\) and \(T\) ([/references/wang-2026-madrc-sst.md](/references/wang-2026-madrc-sst.md)).

For this project's [Plant](/concepts/plant.md), analogous externals include occupancy gains, solar, and [Outdoor Temperature](/concepts/outdoor-temperature.md) — but the controlled channel is OpenTherm water setpoint, not AHU coil flow or attemperation spray.

## Related

- [/concepts/extended-state-observer.md](/concepts/extended-state-observer.md)
- [/concepts/madrc.md](/concepts/madrc.md)
- [/concepts/zone.md](/concepts/zone.md)
- [/concepts/outdoor-temperature.md](/concepts/outdoor-temperature.md)

# Citations

- [/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md) §1, §3.3
- [/references/wang-2026-madrc-sst.md](/references/wang-2026-madrc-sst.md) §3, Eq. (17)
