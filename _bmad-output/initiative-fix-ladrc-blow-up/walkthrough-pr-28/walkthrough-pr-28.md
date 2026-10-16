# Walkthrough — PR #28: refactor sweep (cleanup + latch hygiene)

Target: [PR #28](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/28) (`refactor/1-5-refactor-sweep` → `main`, commit `9cb6eed`)
Focus: human review of cleanup + latch hygiene
Current block: closed — walkthrough complete; story 1.5 marked `done`; PR #28 merge + branch delete in wrap-up

## Blocks

- [x] **Intent** — done
- [x] **Broad strokes** — done
- [x] **with_omega_c replace** — done
- [x] **Zone-change latch hygiene** — done
- [x] **CAP-5 / warn-before-write locks** — done
- [x] **Periphery** — done

## Intent

Source: [story-refactor-sweep-plan.md](../epic-fix-ladrc-blow-up/story-refactor-sweep-plan.md) (frozen Intent, pasted verbatim).

**Problem:** Entries 1–4 left deferred review nits (hand-listed `with_omega_c` copy, weak CAP-5 diverge OR, missing WARNING-before-write inspect lock) plus latch hygiene gap: Critical Zone change resets the ESO but can leave `_blow_up_latch` set and suppress the next WARNING.

**Approach:** Closing sweep = mechanical cleanup/test hardenings **and** latch hygiene on Critical Zone change (Decision A). No new capabilities (Huang CAP-3a, validation, refuse-to-advance stay out). Do not claim “no production behavior change” — latch clear is intentional, small, and in scope.

**Decisions:**
- Critical-zone latch: **A** — when Critical Zone changes under demand, clear `_blow_up_latch` before guard so a trip in the new zone can emit WARNING ([walkthrough-18e21d1](../walkthrough-18e21d1/walkthrough-18e21d1.md)).
- Framing: Intent names **cleanup + latch hygiene**, not “strictly no prod behavior.”
- Zone-latch AC: pure Hass-free helper + Matrix rows for `None→first`, `A→A`, `A→B` (party #2) — not inspect-only.
- `last_u_applied` API: **drop** — leave residue tests on `_last_u_applied` (pr-24 accepted pragmatic); no new public property (party #3).

**Review notes (Intent):**
1. Approach and Decisions name the intentional production delta (latch clear on Critical Zone change) — not “strictly no prod behavior.”
2. Decision A scope is accurate: latch clears under demand when Critical Zone changes, on the path before the guard runs.
3. `None→first` keeping an existing latch is intentional asymmetry; story “before guard” wording vs wiring before [`compute_tracking`](../../../apps/hvac/ladrc.py) is aligned (helper clears latch before tracking; guard still sees the updated latch).

## Broad strokes

What the change is: closing sweep — [`with_omega_c`](../../../apps/hvac/models.py) via `dataclasses.replace`; CAP-5 diverge requires track blow; demand-path warn-before-write inspect; clear `_blow_up_latch` on Critical Zone change via pure helper before [`compute_tracking`](../../../apps/hvac/ladrc.py).

Entry points (open in this order):

1. [`with_omega_c` — `replace(self, omega_c=…)`](../../../apps/hvac/models.py) — hand-list dropped; future fields preserved
2. [`latch_after_zone_change`](../../../apps/hvac/hvac_app.py) + [`control_tick`](../../../apps/hvac/hvac_app.py) wire before [`compute_tracking`](../../../apps/hvac/ladrc.py)
3. [tests/test_hvac_app.py](../../../tests/test_hvac_app.py) — latch Matrix + inspect locks (warn-before-write, helper before tracking)
4. [tests/test_ladrc.py](../../../tests/test_ladrc.py) — CAP-5 diverge assert on track sequence
5. [story-refactor-sweep-plan.md](../epic-fix-ladrc-blow-up/story-refactor-sweep-plan.md) — built plan / AC

**Review notes (Broad strokes):**
1. Entry map OK — only entry #2 is behavioral (latch wire before tracking); the rest are cleanup/tests/plan.
2. Live [`with_omega_c`](../../../apps/hvac/hvac_app.py) call in [`control_tick`](../../../apps/hvac/hvac_app.py) — carry into the replace slice, not a separate entry point.
3. Entry #3 ([test_hvac_app.py](../../../tests/test_hvac_app.py) locks + Matrix) is dense but OK for one stop.
4. Test: 47 passed; ruff clean (local).
5. CI: all checks SUCCESS; PR MERGEABLE.

## with_omega_c replace

The online tuner path still calls [`LadrcConfig.with_omega_c`](../../../apps/hvac/models.py) every demand tick; the implementation now uses [`dataclasses.replace`](../../../apps/hvac/models.py) with only `omega_c=` overridden instead of re-copying every field. That removes the hand-list footgun from entry 3 while automatically preserving later fields such as `u_track_max`.

- [`with_omega_c`](../../../apps/hvac/models.py)
- [test_with_omega_c_preserves_u_track_max](../../../tests/test_ladrc_tuner.py)

**Review notes:**
1. [`dataclasses.replace`](../../../apps/hvac/models.py) is the right tool for the frozen [`LadrcConfig`](../../../apps/hvac/models.py) dataclass.
2. Live [`effective_ladrc`](../../../apps/hvac/hvac_app.py) path unchanged — [`control_tick`](../../../apps/hvac/hvac_app.py) still calls [`with_omega_c`](../../../apps/hvac/models.py) each demand tick.
3. [test_with_omega_c_preserves_u_track_max](../../../tests/test_ladrc_tuner.py) green (focused pytest with parse test).
4. No replace-AST inspect lock needed for the one-liner implementation.
5. Field validation still out of scope for this story.

## Zone-change latch hygiene

[`latch_after_zone_change`](../../../apps/hvac/hvac_app.py) is a pure helper: it clears the latch only when `prev_zone is not None` and `prev_zone != new_zone`; otherwise it returns `latch_in` unchanged (so `None→first` keeps an existing latch). [`control_tick`](../../../apps/hvac/hvac_app.py) captures `prev_zone = self._ladrc.critical_zone`, applies the helper to `_blow_up_latch`, then calls [`compute_tracking`](../../../apps/hvac/ladrc.py) so ESO zone reset and latch hygiene stay aligned before the guard runs.

- [`latch_after_zone_change`](../../../apps/hvac/hvac_app.py)
- [`control_tick` latch wire](../../../apps/hvac/hvac_app.py)
- [test_latch_after_zone_change_matrix](../../../tests/test_hvac_app.py)
- [test_control_tick_latch_helper_before_compute_tracking](../../../tests/test_hvac_app.py)

**Review notes:**
1. Capture `prev_zone` before [`compute_tracking`](../../../apps/hvac/ladrc.py) — required so zone reset and latch hygiene stay aligned.
2. WARNING semantics unchanged — guard [`should_warn`](../../../apps/hvac/ladrc.py) / latch still drive emit-once behavior after the helper runs.
3. [test_latch_after_zone_change_matrix](../../../tests/test_hvac_app.py) rows match story AC (`None→first`, `A→A`, `A→B`).
4. No Hass e2e for zone flip — story Never list; matrix + order inspect are sufficient.
5. App owns `_blow_up_latch` — helper clears on zone change; guard overwrites with `latch_out` afterward.

## CAP-5 / warn-before-write locks

CAP-5 diverge is locked on the **track** sequence: frozen exp_map + thermal+C must show non-finite `u_track` or `|u_track|≥1e6` — a z-only finite path is no longer enough to pass. On the demand slice of [`control_tick`](../../../apps/hvac/hvac_app.py), inspect asserts [`format_blow_up_warning`](../../../apps/hvac/hvac_app.py) appears before [`_write_setpoint(guard.command)`](../../../apps/hvac/hvac_app.py), excluding the no-demand `_write_setpoint(0)` path.

- [test_cap5_exp_map_thermal_c_diverges](../../../tests/test_ladrc.py)
- [test_control_tick_warns_before_write_on_demand_path](../../../tests/test_hvac_app.py)


**Review notes (CAP-5 / warn-before-write locks):**
1. CAP-5 track-only assert closes the weak OR; continuous neighbor stays complementary.
2. Demand-slice inspect excludes no-demand write; matches story Always.
3. Inspect split-on-return is slightly brittle; fine for current control_tick shape.
4. Focused tests: 2 passed.

## Periphery

- [story-refactor-sweep-plan.md](../epic-fix-ladrc-blow-up/story-refactor-sweep-plan.md) — status `built`; planning artifact and AC source
- [party-mode memlog](../../party-mode/memories/installed/.memlog.md) — incidental party session log (not load-bearing)
- [PR #28](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/28) test plan — pytest + ruff per story Tasks

**Review notes (Periphery):**
1. Story plan flipped `built` → `done` in Wrap-up.
2. Party memlog incidental — A/Stay.
3. `walkthrough-pr-28/` committed in Wrap-up.
4. CI SUCCESS already verified.

