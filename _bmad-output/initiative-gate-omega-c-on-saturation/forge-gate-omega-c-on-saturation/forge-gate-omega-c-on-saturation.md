---
title: Gate ωc on saturation (directional) + write-on-change + latch decay
status: hardened
created: 2026-10-17
updated: 2026-10-17
---

# Gate ωc under plant saturation

## Locked

- Success = **A**: stop soft-kill after sustained underheat — not “adapt only with actuation headroom.”
- **Directional clamp:** skip `commit_omega_c` only when `(command ≥ setpoint_max ∧ ωc↑)` or `(command ≤ setpoint_min ∧ ωc↓)`; still skip on guard trip.
- **Strict apply:** when directional blocks commit, do not feed proposed ωc into `with_omega_c` — compute with current.
- **Write-on-change** in `_write_setpoint` (all paths): if desired equals plant entity float state, skip `number/set_value` but continue the tick (advance / reset / gates).
- **Write unreadability fail-closed:** `None` / `unavailable` / `unknown` / unparseable entity state → no `set_value`, `_write_setpoint` false, tick aborts (existing behavior).
- **Recovery while latched:** if latch is already active at tick start, **skip `maybe_adapt` entirely**. Each tick, if `|u_track| > 0.8 · u_track_max` (or `u_track` non-finite), step ωc down by existing tuner `max_rate_fraction` (≥ `omega_c_min`), persist. Stop when finite `|u_track| ≤ 0.8 · u_track_max`. Decay persist is not blocked by the guard-trip skip of normal commit.
- **`0.8 · u_track_max`** is a fixed code constant (not a yaml knob). Decay step/floor reuse existing tuner config.
- Docs/ADR wording must describe the failure mode (A), not headroom-only philosophy.

## Rejected

- Full freeze of commit on any SWT clamp.
- Predicted `|ωc·e/b0|` as commit gate or as decay criterion (ignores `z₂` on latched ticks).
- Gate only on persistence while still applying proposed ωc for the tick.
- Write-on-change as early-return (would freeze ESO/tick).
- Skip-write-and-continue when entity state is unreadable (fail-closed instead).
- Last-written cache as equality baseline (use entity state).
- Propose-then-override while latched (adapt must be skipped when latch already active).
- R1-only (one step on trip edge) as sufficient recovery.
- R3 hard reset to `config.omega_c` on trip.
- One-shot safe-ωc jump (R4-A) instead of stepped decay on real `|u_track|`.

## Why (load-bearing)

- Live failure: healthy-but-saturated ticks still ratchet ωc up → post-reset `|u_track|` sticks above guard.
- Directional + strict stops the ratchet without silencing all adaptation at max in winter.
- Decay on actual `|u_track|` while latched exits soft-kill without a `z₂`-blind proxy; skip adapt while latched avoids fighting recovery.
