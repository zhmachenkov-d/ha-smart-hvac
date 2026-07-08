---
type: Concept
title: Extended State Observer
description: Observer that estimates plant output (or state) and an extra state for total disturbance — the sensing core of ADRC/LADRC.
tags: [control, adrc, observer]
timestamp: 2026-07-08T15:45:00Z
---

# Extended State Observer

An **extended state observer (ESO)** augments the usual estimated states with one (or more) channel(s) for [total disturbance](/concepts/total-disturbance.md). ADRC uses the disturbance estimate to cancel effects each sampling period before the outer controller runs.

In Huang et al. (2018) [LADRC](/concepts/ladrc.md) for HVAC, a **first-order ESO** produces \(z_1\) (zone temperature estimate) and \(z_2\) (lumped disturbance). Gains \(\beta_1,\beta_2\) set observer bandwidth; they were tuned empirically for that Simulink plant. Bandwidth parameterization often uses \(\beta_1=2\omega_o\), \(\beta_2=\omega_o^2\) ([/references/wang-2026-madrc-sst.md](/references/wang-2026-madrc-sst.md)).

On high-order lag plants the raw command \(u\) and delayed measurement \(y\) can desynchronize the ESO. [MADRC](/concepts/madrc.md) feeds the observer a filtered \(u_f\) instead of \(u\).

## Related

- [/concepts/adrc.md](/concepts/adrc.md)
- [/concepts/ladrc.md](/concepts/ladrc.md)
- [/concepts/madrc.md](/concepts/madrc.md)
- [/concepts/total-disturbance.md](/concepts/total-disturbance.md)

# Citations

- [/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md) §1, Eq. (5)
- [/references/wang-2026-madrc-sst.md](/references/wang-2026-madrc-sst.md) §3, Eqs. (10)–(11), (18)
