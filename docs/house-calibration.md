# House calibration

How to calibrate the HVAC App for a specific house. There is no relay/step commissioning procedure in this project ([ADR 0003](adr/0003-online-ladrc-omega-c-auto-tune.md) leaves that out of scope). Calibration is **manual `apps.yaml` tuning** plus **online adaptation of Controller Bandwidth (ωc) only**.

Copy [`apps.yaml.example`](../apps.yaml.example) to `apps.yaml` next to the installed `ha_smart_hvac/` package, then work through the sections below. Never commit live house entity IDs.

Domain terms: [`CONTEXT.md`](../CONTEXT.md). Control decisions: [ADR 0002](adr/0002-ladrc-critical-zone-control.md), [ADR 0003](adr/0003-online-ladrc-omega-c-auto-tune.md).

## 1. House wiring (required)

Replace every `YOUR_*` placeholder:

| Key | Role |
|-----|------|
| `outdoor_temperature` | Outdoor Temperature sensor |
| `plant_management` | Switch: when off, the App does not write Set Water Temperature and clears controller state |
| `plant_setpoint` | OpenTherm Set Water Temperature (`number` entity) |
| `zones[]` | Per Zone: air temperature sensor + one or more climate thermostats |

Without correct wiring the App is not bound to the house.

## 2. Plant clamps

```yaml
setpoint_min: 40
setpoint_max: 55
control_interval: 60
```

These bound the commanded Set Water Temperature. Match them to the boiler / primary circuit limits.

## 3. Weather Feedforward (manual)

Linear outdoor baseline:

\[
u_{ff} = \texttt{base} + \texttt{slope} \times (\texttt{comfort\_ref} - T_{out})
\]

Example starting point: `base: 25`, `slope: 1.2`, `comfort_ref: 20`.

Tune so that in typical winter weather `u_ff` alone already produces a sensible water temperature, with LADRC contributing a modest tracking correction. There is no online feedforward auto-tune.

## 4. LADRC plant channel: `b0` and `ωo` (manual)

Huang et al. coil-flow gains (`b₀ ≈ 2.8`, large `ωo`) **must not** be used on this OpenTherm water-temperature plant at `dt=60` ([ADR 0002](adr/0002-ladrc-critical-zone-control.md)). Example defaults are thermal-band **starting points** and need house calibration:

```yaml
ladrc:
  b0: 5.0e-4      # typical band ~1e-4 … 1e-3
  omega_o: 0.03   # Euler-stable at dt=60 / 2 substeps: ~0.01 … below 1/30≈0.033 (0.05 is unstable)
  omega_c: 0.03   # start for online ωc tune (ADR 0003); paired with u_track_max below
  u_track_max: 250  # magnitude guard; with example b0/ωc, |e|≲3 °C stays tracking
```

After a Critical Zone reset, `|u_track| ≈ ωc·|e|/b0`. Example package A keeps cold-start `|e|=2` under the guard (`≈120 < 250`); `|e|=5` may trip. Raise `u_track_max` or lower `ωc` together if you change either.

Forward-Euler ESO (`apps/ha_smart_hvac/ladrc.py`, `_ESO_EULER_SUBSTEPS=2`): stability needs `|1 − 2·h·ωo| < 1` with `h = dt/2`. At `dt=60`, that is **`ωo` below `1/30 ≈ 0.033`**. Do not use the old “~0.05” upper end — it reintroduces divergence the continuous-form change fixed. If you raise `control_interval`, lower `ωo` or expect a code change to derive substeps from `ωo·dt`.

| Parameter | Effect |
|-----------|--------|
| `b0` | Estimated air °C per second per water °C. Too small → aggressive `u_track`; too large → sluggish loop. |
| `omega_o` | Observer Bandwidth. Higher → faster disturbance tracking, more noise; lower → quieter, slower. Fixed at config time. Stay in the Euler-stable band above. |
| `u_track_max` | App-level blow-up guard (°C). Trip → FF-only + ESO reset. Not a comfort clamp — keep above routine cold-start `|u_track|`. |

Neither `b0` nor `ωo` is adapted online.

## 5. Controller Bandwidth (ωc) — online only

When Plant Management is on and there is Heating Demand, LADRC Auto-Tune slowly adjusts **ωc** from sustained Critical Zone tracking error (`reference − z₁`), inside `[omega_c_min, omega_c_max]`, with deadband, rate limit, and freeze on Critical Zone switch ([ADR 0003](adr/0003-online-ladrc-omega-c-auto-tune.md)). Adapted ωc is persisted in `ladrc_tune_state.json` under the AppDaemon app directory.

Saturation and soft-kill recovery follow **criterion A** (not headroom-only full freeze): upward ωc commits are skipped when the tick’s Set Water Temperature command is at `setpoint_max` and downward at `setpoint_min` (relieving moves allowed); a blocked proposal is not applied to tracking that tick. When the blow-up latch is already active at tick start, adapt is skipped; while the latch is held after a successful plant write, ωc may step down by `max_rate_fraction × ωc` on real `|u_track|` above `0.8 · u_track_max` until residue leaves that band — not ops-reset-only. Identical Set Water Temperature values skip HA writes; unreadable plant state aborts the tick (fail-closed).

Weather Feedforward, `b0`, and `ωo` stay manual.

## 6. Safe order on a live house

1. Fill entity IDs and Zones.
2. Set sensible `setpoint_min` / `setpoint_max`.
3. Tune Weather Feedforward to a familiar compensation curve.
4. Keep thermal-band `b0` / `omega_o` from the example (not Huang).
5. Enable Plant Management; watch water temperature, Zone air, and tracking magnitude.
6. If needed, hand-adjust `b0` / `omega_o` / feedforward; let ωc adapt within its bounds.
7. Disable Plant Management to stop all Set Water Temperature writes and clear controller state.

## What is not calibrated here

- Relay or open-loop step commissioning
- Online `b0` or `ωo` adaptation
- Weather Feedforward auto-tune
- MADRC inertia compensator
