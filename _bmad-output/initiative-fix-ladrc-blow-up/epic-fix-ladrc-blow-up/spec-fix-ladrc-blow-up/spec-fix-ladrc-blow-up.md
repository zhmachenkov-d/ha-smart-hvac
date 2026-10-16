---
id: SPEC-fix-ladrc-blow-up
companions:
  - architecture-diagrams.md
  - ../../../../docs/adr/0002-ladrc-critical-zone-control.md
  - ../../../../docs/adr/0003-online-ladrc-omega-c-auto-tune.md
sources:
  - /home/vscode/.cursor/plans/fix_ladrc_blow-up_4f4b86eb.plan.md
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Fix LADRC u_track blow-up

## Why

**Pain to solve.** On the live plant, LADRC `u_track` is numerically exploding (~10^12–10^24) while weather feedforward `u_ff` stays sane (~40). The clamp to `[setpoint_min, setpoint_max]` turns the sum into bang-bang Set Water Temperature (40↔55), so zone error stays stuck and the boiler thrashing looks like “steering jumps.” Example defaults (`b0=2.8`, `omega_o=19.49`) at `dt=60` with absolute SWT make the ESO prediction and discrete observer gains physically absurd for this OpenTherm plant; there is no finite/magnitude recovery today. Until code lands, operators should turn Plant Management off (or stop demand) so the app stops writing SWT and clears LADRC. Failure-mode diagram: `architecture-diagrams.md`.

## Capabilities

- **CAP-1**
  - **intent:** Operators get plant-channel LADRC defaults (`b0`, `omega_o`) that keep the ESO and tracking term numerically stable under absolute Set Water Temperature at the app’s 60 s sample time.
  - **success:** With the new example defaults, advancing many ticks at realistic `y≈21`, `T_r` near zone air, and applied `u∈[40,55]` keeps `u_track`, `z1`, and `z2` finite with `|u_track|` in a sane band (tens of °C, not 1e6+). `apps/apps.yaml.example` carries the new values.

- **CAP-2**
  - **intent:** On a bad control tick the app detects non-finite or magnitude-exploded `u_track`, clears diverged ESO state, and still issues a safe feedforward-only water command for that tick.
  - **success:** In the `hvac_app` tick path, after `compute_tracking`, when `u_track` is non-finite or `|u_track|` exceeds the configured magnitude threshold (example/default **100** °C), the tick yields `command = clamp(u_ff)`, ESO `reset(measured)`, and a WARNING visible in HA logs once per episode; the loop does not remain bricked until zone change / idle / plant-off.

- **CAP-3**
  - **intent:** Automated tests lock the blow-up diagnosis and the fix so old unsafe gains cannot silently return.
  - **success:** Tests (a) reproduce divergence under old/large `b0`/`omega_o` over multiple advances, (b) assert new-default boundedness over N ticks with absolute SWT, and (c) assert the guard path resets and returns feedforward-only command.

- **CAP-4**
  - **intent:** Maintainers reading ADR 0002 know Huang `b0`/`ωo` must not be used at `dt=60` with absolute SWT, and that the new defaults are thermal-plant starting points requiring house calibration.
  - **success:** ADR 0002 carries that amendment; ADR 0003 remains ωc-only (no claim of online `b0`/`omega_o` adaptation).

## Constraints

- Keep control law and feedforward structure: `command = clamp(u_ff + u_track)`; advance the ESO with the **actually applied** absolute SWT command.
- Online auto-tune remains **ωc only** (ADR 0003); this work must not introduce online `b0` or `omega_o` adaptation.
- Do not change `setpoint_min`/`setpoint_max` (plant limits 40/55); bang-bang was clamp thrashing, not a limits bug.
- Exact numeric defaults are locked by the CAP-3 boundedness tests, not by copying Huang. Starting-point bands from the plan: `b0` ~`1e-4`–`1e-3` °C_air/(°C_water·s); `omega_o` ~`0.01`–`0.05` so `omega_o * dt` is moderate at `dt=60` while remaining faster than `omega_c`.
- The `|u_track|` magnitude blow-up threshold is a **config field** with example/default **100** (°C); non-finite `u_track` always trips regardless of that value.
- Blow-up guard lives in **`hvac_app` only** (after `compute_tracking`); `LadrcState` stays a pure tracker/ESO and does not grow a guard API.
- Optionally refuse to `advance` with non-finite state after a guard trip.

## Non-goals

- Changing feedforward structure or Critical Zone selection.
- Adapting `b0` / `omega_o` online.
- Changing Set Water Temperature min/max (40/55).
- Treating the `omega_c` tuner as the fault or changing its bounds.
- Putting the blow-up guard inside `LadrcState`.

## Success signal

After retune + guard, multi-tick simulation (and live ticks under demand) no longer produce non-finite or astronomical `u_track`; command leaves bang-bang thrashing and stays a smooth `clamp(u_ff + u_track)` within plant limits, with regression tests failing if old defaults or an unguarded explode path return.
