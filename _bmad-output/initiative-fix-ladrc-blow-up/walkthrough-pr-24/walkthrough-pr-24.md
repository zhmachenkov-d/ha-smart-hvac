# Walkthrough — PR #24: tracking-residue known input in hvac_app

Target: [PR #24](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/24) (`fix/1-2-tracking-residue-known-input` → `main`)
Focus: risks, boundaries, merge-readiness
Current block: closed — all blocks done; Wrap-up in progress (merge + story done)

## Blocks

- [x] **Intent** — done (review notes 1–3)
- [x] **Broad strokes** — done (call site first)
- [x] **Known-input seam** — done
- [x] **Wiring lock tests** — done (strengtheners 1–4)
- [x] **Periphery** — done (strengtheners committed+pushed)

## Intent

Source: [story-tracking-residue-known-input-in-hvac-app-plan.md](../epic-fix-ladrc-blow-up/story-tracking-residue-known-input-in-hvac-app-plan.md) (frozen Intent, pasted verbatim; review notes below).

**Problem:** After clamp, `hvac_app.control_tick` advances the ESO with absolute post-clamp `command` (SWT °C). Spec CAP-1 / Constraints require known input `(command − u_ff)` — the tracking residue — not absolute command and not pre-clamp `u_track`. CAP-5 tests already use path C; live app does not.

**Approach:** Keep plant write `clamp(u_ff + u_track)`. After a successful write, advance with `(command − u_ff)`. Lock the wiring with a seam/unit test (no need to mock full AppDaemon `control_tick`).

Review focus (user): risks, boundaries, merge-readiness.

**Review notes (Intent wording — apply to later blocks):**
1. Story 1.2 delivers only the **known-input half** of CAP-1. Defaults / `apps.yaml.example` remain story 1.3 — do not treat this PR as CAP-1 done or epic Success.
2. «After a successful write» means: if `_write_setpoint` fails, the tick returns without advancing the ESO (no stale known-input update).
3. Seam vs inline call is **not load-bearing** for Intent; what matters is post-clamp `(command − u_ff)` after a successful plant write. Seam is for testability.

## Broad strokes

What the change is: after successful plant write, `control_tick` advances the ESO with post-clamp `(command − u_ff)` instead of absolute SWT; plant write stays absolute clamped command. Story 1.2 is the **known-input half** of CAP-1 only — not CAP-1 complete (defaults/example = 1.3), not epic Success. The module seam `advance_with_tracking_residue` exists for testability; the load-bearing fix is the residue math. Unit tests lock `_last_u_applied` wiring.

Entry points (open in this order):

1. [control_tick call site](../../../apps/hvac/hvac_app.py) — after `_write_setpoint(command)` success; passes `u_ff` (load-bearing wiring)
2. [advance_with_tracking_residue](../../../apps/hvac/hvac_app.py) — testable wrapper: `advance(measured, command − u_ff, config)`
3. [_write_setpoint](../../../apps/hvac/hvac_app.py) — unchanged absolute plant write
4. [test_advance_with_tracking_residue_*](../../../tests/test_hvac_app.py) — lock residue vs absolute; zero when `command == u_ff`
5. [story plan Intent/Notes](../epic-fix-ladrc-blow-up/story-tracking-residue-known-input-in-hvac-app-plan.md) — known-input half CAP-1; out of scope `LadrcState` / defaults / guard / ADR

## Known-input seam

Mechanism: extracted module function so tests need no AppDaemon mock. After `_write_setpoint(command)` returns true, tick calls seam with measured, command, u_ff, effective_ladrc. Known input is post-clamp residue only — never absolute command, never pre-clamp u_track.

- [advance_with_tracking_residue](../../../apps/hvac/hvac_app.py) — one-liner wrapper
- [control_tick](../../../apps/hvac/hvac_app.py) — call after successful write; early return if write fails (no advance)
- Plant write path unchanged — absolute `command`

Risk note for reviewer: write-fail skips advance (pre-existing pattern); clamp asymmetry between plant and ESO is intentional CAP-1.

## Wiring lock tests

Mechanism: unit tests call the seam directly; assert `LadrcState._last_u_applied` equals `command − u_ff` (15 when 55−40) and `0` when `command == u_ff`. Does not mock full AppDaemon `control_tick` / Hass.

- [test_advance_with_tracking_residue_uses_command_minus_uff](../../../tests/test_hvac_app.py)
- [test_advance_with_tracking_residue_zero_when_command_equals_uff](../../../tests/test_hvac_app.py)
- [_config thermal band](../../../tests/test_hvac_app.py) — CAP-5 thermal numbers

Review-added strengtheners (Thoughts 1–4):

- [test_control_tick_uses_tracking_residue_seam](../../../tests/test_hvac_app.py) — source contract: call site uses seam, not `self._ladrc.advance(`
- [test_residue_known_input_differs_behaviorally_from_absolute](../../../tests/test_hvac_app.py) — `z1` differs residue vs absolute (no private field)
- [test_advance_with_tracking_residue_mid_band](../../../tests/test_hvac_app.py) / [negative residue](../../../tests/test_hvac_app.py) — mid-band `+5`, command `< u_ff` → `−10`
- [test_hvac_app_config_matches_cap5_thermal_band](../../../tests/test_hvac_app.py) — locks thermal constants

Merge note: locks seam math + call-site source contract; not live AppDaemon / not epic Success.

## Periphery

- [story-tracking-residue-known-input-in-hvac-app-plan.md](../epic-fix-ladrc-blow-up/story-tracking-residue-known-input-in-hvac-app-plan.md) — plan + quick review triage (0 findings)
- [PR #24](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/24) — Conventional Commits title/body
- Not in PR: LadrcState.advance, apps.yaml.example, ADRs, guard — intentionally untouched (stories 1.1 done / 1.3–1.4 later)
