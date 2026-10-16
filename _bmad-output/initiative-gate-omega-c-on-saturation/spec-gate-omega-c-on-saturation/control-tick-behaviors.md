# Control-tick behaviors (gate ωc on saturation)

Load-bearing rules for CAP-1–CAP-4. Kernel holds intent; this file holds the matrices.

## Directional commit clamp (CAP-1)

Skip `commit_omega_c` when any of:

| Condition | Skip commit? |
| --- | --- |
| Guard tripped (existing) | yes |
| `command >= setpoint_max` and proposed ωc **increases** | yes |
| `command <= setpoint_min` and proposed ωc **decreases** | yes |
| `command >= setpoint_max` and proposed ωc **decreases** | no (allow) |
| `command <= setpoint_min` and proposed ωc **increases** | no (allow) |
| Interior command (strictly inside clamp) and not tripped | no (allow) |

Full freeze on any SWT clamp is out of scope.

## Strict apply (CAP-2)

On a tick where the directional clamp (or guard trip) would block commit of a proposed increase/decrease:

1. Do **not** call `config.ladrc.with_omega_c(proposed)` for that tick’s `compute_tracking`.
2. Tracking / guard / write use the **current committed** ωc.
3. Proposed ωc is discarded for both apply and persistence on that tick.

Gate-only-on-persistence (apply proposed, skip commit) is rejected — it reopens the one-tick ratchet.

## Write-on-change (CAP-3)

Inside `_write_setpoint` for **all** paths (demand and idle/0):

1. Read current plant entity state.
2. If state is `None` / `unavailable` / `unknown` or not parseable as float → **fail-closed** (existing): no `set_value`, return false, **control tick aborts** (no advance).
3. If desired equals the parsed float (exact compare), skip `number/set_value` but return success so the tick continues (ESO reset / advance / gates / decay).
4. Otherwise call `number/set_value`.

Baseline for equality is entity state, not a last-written cache. Equality-skip must not early-return the tick; unreadability abort is separate and intentional.

## Latch ωc decay (CAP-4)

While the blow-up soft-kill latch is **already active at tick start**:

1. **Skip `maybe_adapt` entirely** — no propose, no propose-then-override.
2. After `u_track` for the tick is known: if `|u_track| > 0.8 · u_track_max` **or** `u_track` is non-finite → step committed ωc down by existing tuner `max_rate_fraction`, clamp to `≥ omega_c_min`, **persist**.
3. Stop decaying when `u_track` is finite and `|u_track| ≤ 0.8 · u_track_max` (still skip adapt while latch remains active).
4. This persist path runs even though normal `commit_omega_c` is skipped on guard trip.
5. Criterion uses **actual tick `|u_track|`**, not `|ωc · e / b0|`.
6. `0.8` is a fixed code constant — not a yaml knob. Step/floor reuse existing tuner config.

On the trip-edge tick (latch was inactive at start), adapt may still have proposed before the guard; commit remains skipped by guard trip; decay applies from that tick onward when the residue condition holds.

Rejected as sufficient recovery alone: one step on trip edge (R1), hard reset to `config.omega_c` (R3), one-shot safe-ωc jump (R4).
