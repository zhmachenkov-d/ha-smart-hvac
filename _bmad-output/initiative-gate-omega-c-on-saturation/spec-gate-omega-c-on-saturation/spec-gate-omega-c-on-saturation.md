---
id: SPEC-gate-omega-c-on-saturation
companions:
  - control-tick-behaviors.md
  - architecture-diagrams.md
  - ../../../../docs/adr/0003-online-ladrc-omega-c-auto-tune.md
  - ../../../../docs/house-calibration.md
sources:
  - ../forge-gate-omega-c-on-saturation/forge-gate-omega-c-on-saturation.md
  - /home/vscode/.cursor/plans/gate_omega_c_on_saturation_2ead8ef3.plan.md
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Gate ωc on saturation

## Why

**Pain to solve.** After sustained Critical Zone underheat with Set Water Temperature already at `setpoint_max`, healthy-but-saturated ticks still let the online ωc tuner ratchet upward. A later ESO reset then drives `|u_track|` past the blow-up guard every tick, latches soft-kill (feedforward-only), and leaves the loop stuck. Criterion of success is **A**: stop that soft-kill path — not a broader “adapt only with actuation headroom” principle. Behavior matrices: `control-tick-behaviors.md`.

## Capabilities

- **CAP-1**
  - **intent:** The control tick can refuse to commit an ωc adaptation that would push further into the saturated plant direction, while still allowing ωc moves that relieve saturation.
  - **success:** With command at `setpoint_max`, an upward proposed ωc is not committed; a downward proposed ωc may commit. Symmetric at `setpoint_min`. Guard trip still blocks commit. Full freeze on any clamp does not occur.

- **CAP-2**
  - **intent:** When a directional (or guard) block prevents commit, that tick’s tracking computation cannot use the blocked proposed ωc.
  - **success:** On a blocked tick, `compute_tracking` runs with the current committed ωc; a Hass-free ratchet scenario that previously climbed ωc via one-tick proposed apply no longer increases committed or applied ωc across saturated upward proposals.

- **CAP-3**
  - **intent:** The app can avoid redundant Home Assistant `number/set_value` calls when the desired Set Water Temperature already matches the plant entity, without stalling the rest of the control tick when a float state was read.
  - **success:** When desired equals the entity float state, no `number/set_value` is issued and the tick continues (ESO reset/advance and adapt/gate/decay). When entity state is unavailable/unknown/unparseable, behavior stays fail-closed: no write, `_write_setpoint` false, tick aborts. Applies on demand and idle/0 paths inside `_write_setpoint`.

- **CAP-4**
  - **intent:** While the blow-up soft-kill latch is held, the system can step ωc down over successive ticks until tracking residue leaves the latch-stick band, persist those steps, and not run normal adapt during that recovery.
  - **success:** With latch already active at tick start, `maybe_adapt` is not called. If `|u_track| > 0.8 · u_track_max` (or non-finite `u_track`), each such tick reduces committed ωc by existing tuner `max_rate_fraction` (≥ `omega_c_min`) and persists; decay stops once finite `|u_track| ≤ 0.8 · u_track_max`. Guard-trip skip of `commit_omega_c` does not prevent decay persist. Criterion uses actual tick `|u_track|`, not `|ωc·e/b0|`.

- **CAP-5**
  - **intent:** Maintainers reading ADR 0003 Guards and house-calibration §5 understand the directional clamp and latch decay under criterion A.
  - **success:** Those docs describe skip of upward commit at max / downward at min, strict apply, latched `|u_track|` decay with adapt skipped while latched, and fail-closed unreadability — not a headroom-only full freeze or “ops reset only” recovery story.

- **CAP-6**
  - **intent:** Automated tests lock the directional matrix, strict-apply no-ratchet path, write-on-change skip vs fail-closed unreadability, and latched decay exit so regressions cannot return silently.
  - **success:** Tests cover (a) commit helper/matrix for None / tripped / max+up / max+down / min+down / min+up / interior, (b) saturated upward proposals do not raise applied or committed ωc, (c) identical entity state skips `set_value` without aborting tick side effects, (d) unreadable entity aborts the tick, (e) while latched, adapt is skipped and multi-tick `|u_track|` above threshold decays ωc until below `0.8 · u_track_max`.

## Constraints

- Directional clamp and strict apply are both required; persistence-only gating is forbidden.
- Write-on-change baseline is **current plant entity float state** with exact equality; not a last-written cache. Equality-skip continues the tick; unreadability stays **fail-closed** (abort tick).
- While latch is already active at tick start: **skip `maybe_adapt` entirely**; only decay+persist when residue condition holds — no propose-then-override.
- Latch decay persists even when guard trip blocks normal `commit_omega_c`.
- Decay / commit gates use actual tick `|u_track|` (and non-finite); predicted `|ωc·e/b0|` is not a gate or decay criterion.
- Threshold `0.8 · u_track_max` is a fixed code constant (not a yaml knob). Decay step/floor reuse existing tuner `max_rate_fraction` / `omega_c_min`.
- Online auto-tune remains **ωc only** (ADR 0003); no online `b0` / `ωo` / MADRC work here.
- Do not change `setpoint_min` / `setpoint_max` or `u_track_max` as the fix.
- Docs must frame criterion **A**, not headroom-only philosophy.

## Non-goals

- Full freeze of ωc commit whenever SWT is at either clamp.
- ESO anti-windup redesign or changing package-A / `u_track_max` defaults.
- Hard reset of ωc to `config.omega_c` on trip, or a one-shot “safe ωc” jump as the sole recovery.
- Treating a one-time ops delete of `ladrc_tune_state.json` as the product fix (ops may still help a stuck file before this ships).
- Online adaptation of `b0`, `ωo`, or MADRC.

## Success signal

Under a sustained underheat-at-max scenario, ωc no longer ratchets upward on saturated ticks; after a guard latch, adapt stays off and stepped decay on real `|u_track|` brings residue to ≤ `0.8 · u_track_max` without relying on ops reset; redundant identical SWT writes are skipped without freezing the tick, while unreadable plant state still aborts — demonstrated by CAP-6 tests and matching ADR/calibration wording under criterion A.
