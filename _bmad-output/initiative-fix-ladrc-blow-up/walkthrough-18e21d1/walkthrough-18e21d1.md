# Walkthrough — commit 18e21d1: LADRC u_track blow-up guard

Target: commit [`18e21d1`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/18e21d100e4884fda3f3c824198872e228caeb14) (`fix(hvac): add LADRC u_track blow-up guard in hvac_app`)
Focus: human review of mechanism (story 1.4)
Current block: closed — walkthrough complete; wrap-up: commit walkthrough, merge PR #27, delete feature branch; story done; CAP-2 deferred

## Blocks

- [x] **Intent** — done
- [x] **Broad strokes** — done
- [x] **Guard seam** — done
- [x] **control_tick wiring** — done
- [x] **Episode latch** — done
- [x] **CAP-3(c) regression** — done
- [x] **Periphery** — done

## Intent

Source: [story-blow-up-guard-in-hvac-app-plan.md](../epic-fix-ladrc-blow-up/story-blow-up-guard-in-hvac-app-plan.md) (frozen Intent, pasted verbatim).

**Problem:** After `compute_tracking`, a non-finite or over-threshold `|u_track|` still drives `clamp(u_ff + u_track)` and can brick the loop until zone change / idle / plant-off; CAP-3(c) has no regression.

**Approach:** Add an `hvac_app`-only blow-up guard (pure Hass-free seam + WARNING formatter) that trips on non-finite or `|u_track| > u_track_max`, resets ESO, yields `clamp(u_ff)`, WARNING once per episode (Floor MUST fields), advances ESO after reset on the trip tick (decision B), and locks CAP-3(c) without AppDaemon.

**Review notes (Intent):**
1. Thoughts: Intent matches `18e21d1`; Approach bullets present; plan + example comment are periphery.

## Broad strokes

What the change is: after `compute_tracking`, a pure `guard_u_track` seam either clamps `u_ff+u_track` or (on trip) resets ESO and clamps `u_ff` alone; episode latch drives one WARNING; `control_tick` always advances with the guarded command (decision B); CAP-3(c) locks this without Hass.

Entry points (open in this order):

1. [`guard_u_track`](../../../apps/hvac/hvac_app.py) (~L43–76) — pure trip/reset/ff-only seam
2. [`control_tick` guard wire](../../../apps/hvac/hvac_app.py) (~L169–217) — latch, WARNING before write, advance B, trip INFO `guarded`
3. [`format_blow_up_warning`](../../../apps/hvac/hvac_app.py) (~L87–98) — Floor MUST WARNING string
4. [latch clears](../../../apps/hvac/hvac_app.py) — `_blow_up_latch=False` on no-demand / `_hands_off` / `_go_idle` (+ init)
5. [CAP-3(c) tests](../../../tests/test_hvac_app.py) (~L149+) — Hass-free seam + inspect locks

**Review notes (Broad strokes):**
1. Threshold is `effective_ladrc.u_track_max`, not raw config.
2. “Always advance” is after successful write — write-fail early return still skips advance (same as pre-guard).
3. Formatter as its own entry is thin; Floor MUST fields still justify listing it.
4. Test: `tests/test_hvac_app.py` 17 passed; ruff clean; CAP-2 live WARNING unverified.

## Guard seam

Mechanism: `guard_u_track` owns trip detection (non-finite or `|u_track|>u_track_max`), calls `ladrc.reset(measured)` on trip, returns clamped ff-only vs ff+track, and computes `should_warn`/`latch_out` from `latch_in`.

- [`GuardUTrackResult`](../../../apps/hvac/hvac_app.py) (~L35–40)
- [`guard_u_track`](../../../apps/hvac/hvac_app.py) (~L43–76)

**Review notes (Guard seam):**
1. `isfinite` before magnitude is load-bearing (NaN fails `abs > max`).
2. Test: 9 guard/formatter tests passed; inspect/idle left to later blocks.

## control_tick wiring

Mechanism: after `compute_tracking`, call guard; assign latch; emit WARNING when `should_warn` BEFORE `_write_setpoint` (so write failure cannot swallow the one-per-episode warn); always `advance_with_tracking_residue(..., guard.command, ...)`; trip INFO omits raw `u_track` and marks `guarded`.

- [`control_tick`](../../../apps/hvac/hvac_app.py) (~L160–217)

**Review notes (control_tick wiring):**
1. Warn-before-write is correct; write-fail skips advance and guarded INFO.
2. Inspect locks order + `guarded`; does not lock WARNING-before-write (accepted/deferred).

## Episode latch

Mechanism: `HvacApp._blow_up_latch` carries episode state; healthy tick clears via `latch_out=False`; idle/hands-off/no-demand force `False` alongside LADRC clear.

- [initialize](../../../apps/hvac/hvac_app.py) (~L110)
- [no-demand](../../../apps/hvac/hvac_app.py) (~L143)
- [`_hands_off` / `_go_idle`](../../../apps/hvac/hvac_app.py) (~L219–229)

**Review notes (Episode latch):**
1. Clear sites match story Always.
2. Critical-zone change resets ESO but not latch — accepted (not in Always); may suppress WARNING across zone switch until healthy/idle.

## CAP-3(c) regression

Mechanism: Hass-free tests cover healthy/magnitude/non-finite/consecutive/latch-clear/poisoned-z2/formatter Floor plus inspect for call-site order, latch clears, and guarded INFO.

- [CAP-3(c) tests](../../../tests/test_hvac_app.py) (~L149+)

**Review notes (CAP-3(c)):**
1. Story I/O matrix rows covered via seam or inspect.
2. Test: subset 10 passed; full `test_hvac_app.py` 17 passed; CAP-2 manual open.

## Periphery

- [`apps.yaml.example`](../../../apps/apps.yaml.example) — `u_track_max` comment now live magnitude guard (°C)
- [story plan](../epic-fix-ladrc-blow-up/story-blow-up-guard-in-hvac-app-plan.md) — status built; planning artifact

**Review notes (Periphery):**
1. Example comment matches live guard; story plan artifact expected in commit.
2. Untracked walkthrough dirs left for Wrap-up (commit `walkthrough-18e21d1/`; drop obsolete `walkthrough-pr-27/`).
