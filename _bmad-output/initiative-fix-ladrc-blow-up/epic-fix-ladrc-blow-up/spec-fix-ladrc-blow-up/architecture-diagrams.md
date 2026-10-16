# Architecture diagrams — LADRC blow-up

## Saturation thrashing loop (observed failure)

When `u_track` diverges, `clamp(u_ff + u_track)` to `[setpoint_min, setpoint_max]` produces bang-bang commands; the ESO then advances on those absolute SWT values and the divergence persists.

```mermaid
flowchart LR
  u_ff["u_ff ~ 40"] --> sum["u_ff + u_track"]
  u_track["u_track → ±1e12…1e24"] --> sum
  sum --> clamp["clamp 40..55"]
  clamp --> cmd["command bang-bang"]
  cmd --> eso["ESO advance with absolute SWT"]
  eso --> u_track
```
