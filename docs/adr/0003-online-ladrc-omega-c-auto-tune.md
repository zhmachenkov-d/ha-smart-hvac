# Online LADRC ωc auto-tune

The HVAC App slowly adapts LADRC **Controller Bandwidth (ωc)** during normal heating when Plant Management is on. **Observer Bandwidth (ωo)** and plant gain **b₀** stay fixed at config time; Weather Feedforward stays manual.

## Why ωc only

- **ωc** sets outer-loop tracking speed (`kp = ωc`). Sustained Critical Zone tracking error (`reference − z₁`) indicates the loop is too slow or too aggressive; a small integral nudge on ωc is safe with rate limits and bounds.
- **b₀** appears in the denominator of `u = (u₀ − z₂) / b₀`. Online changes would shift the control law discontinuously and confuse the ESO's disturbance estimate.
- **ωo** trades noise rejection against disturbance tracking in the ESO. That trade-off is commissioning work, separate from outer-loop tracking speed.

## Why tracking error, not Zone Error

Zone Error uses raw zone sensor temperature. LADRC tracks against the ESO estimate **z₁**, which lags the sensor and smooths noise. Adaptation uses `reference − z₁` so the tuner responds to what the controller actually sees.

## Guards

Adaptation runs only when there is Heating Demand, the Critical Zone has been stable for `min_steady_ticks`, `|tracking error| ≥ deadband`, and the per-tick change is clamped to `max_rate_fraction × ωc` and to `[omega_c_min, omega_c_max]`. On Critical Zone switch the tuner freezes for that tick and resets its steady counter (ESO reset is handled separately per ADR 0002).

## Persistence

Adapted ωc is stored in `ladrc_tune_state.json` under the AppDaemon app directory. Steady-tick state is not persisted.

## Out of scope

Weather Feedforward auto-tune, online b₀ or ωo adaptation, relay/step commissioning, MADRC inertia compensator.
