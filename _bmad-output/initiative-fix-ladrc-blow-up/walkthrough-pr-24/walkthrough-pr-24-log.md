# Review log: PR #24 tracking-residue known input

Target: https://github.com/zhmachenkov-d/ha-smart-hvac/pull/24

## 1 — orientation — started

Session: unavailable · Timestamp: 2026-10-16T17:15:00+03:00

- Action: Orientation started for story 1.2 / PR #24 (`fix/1-2-tracking-residue-known-input` → `main`); created walkthrough scaffolding
- Result: `walkthrough-pr-24.md` + `walkthrough-pr-24-log.md` in place; narrative blocks are placeholders only
- Evidence: [PR #24](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/24); branch `fix/1-2-tracking-residue-known-input`
- Open: Await parent write instructions; define Intent/Broad strokes/slices; user confirmation of review focus

## 2 — orientation — approved

Session: c250d733-0953-4430-bc20-39881c9df912 · Timestamp: 2026-10-16T17:15:30+03:00

- Action: User approved target PR #24 (full story 1.2) and focus risks/boundaries/merge-readiness; drafted full narrative blocks
- Result: Narrative written; current block Intent (in progress)
- Evidence: PR #24; story-tracking-residue-known-input-in-hvac-app-plan.md frozen Intent
- Open: none for orientation

## 2 — orientation — approved

Session: c250d733-0953-4430-bc20-39881c9df912 · Timestamp: 2026-10-16T17:16:23+03:00

- Action: User approved target PR #24 + focus risks/boundaries/merge-readiness
- Result: Narrative fully drafted; current block Intent
- Evidence: [PR #24](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/24); [story plan](../epic-fix-ladrc-blow-up/story-tracking-residue-known-input-in-hvac-app-plan.md) frozen Intent
- Open: none for orientation

## 3 — Intent — Thoughts

Session: c250d733-0953-4430-bc20-39881c9df912 · Timestamp: 2026-10-16T17:17:00+03:00

- Action: User chose Thoughts on Intent; examined frozen Intent vs CAP-1/Constraints and live control_tick wiring claim
- Result: Intent accurate for story 1.2 known-input half of CAP-1; no Intent rewrite needed. Findings (open for reviewer): (1) CAP-1 success also needs defaults/example — deferred to 1.3, Intent correctly scoped; (2) Intent says after successful write — matches early-return before advance; (3) seam vs inline not load-bearing for Intent. Disposition: accepted as-is pending user done
- Evidence: spec-fix-ladrc-blow-up.md Constraints known-input; apps/hvac/hvac_app.py control_tick ~L102-110; story plan frozen Intent
- Open: await user done or further Intent moves

## 4 — Intent — wording revision

Session: c250d733-0953-4430-bc20-39881c9df912 · Timestamp: 2026-10-16T17:19:00+03:00

- Action: User requested Intent wording fixes 1-3 (CAP-1 half-scope; write-fail no-advance; seam not load-bearing)
- Result: Narrative Intent gained Review notes; constraint for later blocks recorded. Frozen plan Intent untouched
- Evidence: walkthrough-pr-24.md Intent; user chose 1-3
- Open: await user done or further Intent moves

## 5 — Intent — done

Session: c250d733-0953-4430-bc20-39881c9df912 · Timestamp: 2026-10-16T17:19:30+03:00

- Action: User marked Intent done
- Result: Intent accepted with review notes 1-3; advancing to Broad strokes
- Evidence: walkthrough-pr-24.md
- Open: none for Intent

## 6 — Broad strokes — presented

Session: c250d733-0953-4430-bc20-39881c9df912 · Timestamp: 2026-10-16T17:19:35+03:00

- Action: Presented Broad strokes block
- Result: awaiting user move/done
- Evidence: narrative Broad strokes
- Open: await user

## 7 — Broad strokes — Thoughts

Session: c250d733-0953-4430-bc20-39881c9df912 · Timestamp: 2026-10-16T17:20:00+03:00

- Action: User chose Thoughts on Broad strokes; reviewed 5 entry points vs Intent notes
- Result: Entry map adequate. Findings: (1) seam first is navigation OK but call site is load-bearing risk; (2) tests lock seam not control_tick — Wiring block gap; (3) entry 5 half-CAP-1 scope correct. Disposition open pending user
- Evidence: apps/hvac/hvac_app.py; tests/test_hvac_app.py
- Open: await done or further Broad strokes moves

## 8 — Broad strokes — entry-point order

Session: c250d733-0953-4430-bc20-39881c9df912 · Timestamp: 2026-10-16T17:20:30+03:00

- Action: User requested reorder entry points; call site first, seam second
- Result: Broad strokes entry list updated; load-bearing wiring first per Thoughts
- Evidence: walkthrough-pr-24.md Broad strokes
- Open: await done or further Broad strokes moves

## 9 — Broad strokes — done

Session: c250d733-0953-4430-bc20-39881c9df912 · Timestamp: 2026-10-16T17:21:30+03:00

- Action: User marked Broad strokes done
- Result: accepted with call-site-first entry order; advancing to Known-input seam
- Evidence: walkthrough-pr-24.md
- Open: none for Broad strokes

## 10 — Known-input seam — presented

Session: c250d733-0953-4430-bc20-39881c9df912 · Timestamp: 2026-10-16T17:21:35+03:00

- Action: Presented Known-input seam block
- Result: awaiting user move/done
- Evidence: narrative Known-input seam
- Open: await user

## 11 — Known-input seam — Thoughts

Session: c250d733-0953-4430-bc20-39881c9df912 · Timestamp: 2026-10-16T17:22:30+03:00

- Action: User chose Thoughts on Known-input seam
- Result: Wiring matches CAP-1 residue after successful write. Findings: (1) post-clamp command−u_ff correct; (2) write-fail skip advance intentional; (3) no-demand idle path still writes 0 without residue advance — out of story scope / OK; (4) seam thin — regression risk is call-site args not wrapper. Disposition open pending user
- Evidence: apps/hvac/hvac_app.py L73 idle write; L102-110 residue path
- Open: await done or further seam moves

## 12 — Known-input seam — Test

Session: c250d733-0953-4430-bc20-39881c9df912 · Timestamp: 2026-10-16T17:23:30+03:00

- Action: Ran `uv run pytest tests/test_ladrc.py tests/test_hvac_app.py -q` and `uv run ruff check apps/hvac/hvac_app.py tests/test_hvac_app.py`
- Result: 10 passed; ruff clean. Verified: seam math (_last_u_applied). Unverified: control_tick call-site integration, live AppDaemon write/advance ordering
- Evidence: pytest 10 passed; ruff All checks passed
- Open: await done or further seam moves

## 13 — Known-input seam — done

Session: c250d733-0953-4430-bc20-39881c9df912 · Timestamp: 2026-10-16T17:24:30+03:00

- Action: User marked Known-input seam done
- Result: accepted after Thoughts+Test (10 pytest pass); advancing to Wiring lock tests
- Evidence: walkthrough-pr-24.md; log #11-12
- Open: none for seam

## 14 — Wiring lock tests — presented

Session: c250d733-0953-4430-bc20-39881c9df912 · Timestamp: 2026-10-16T17:24:35+03:00

- Action: Presented Wiring lock tests block
- Result: awaiting user
- Evidence: narrative Wiring lock tests
- Open: await user

## 15 — Wiring lock tests — Thoughts

Session: c250d733-0953-4430-bc20-39881c9df912 · Timestamp: 2026-10-16T17:26:00+03:00

- Action: User chose Thoughts on Wiring lock tests
- Result: Tests lock seam math adequately for story AC. Findings: (1) no control_tick integration — accepted boundary per Intent note 3; (2) asserts via private _last_u_applied — brittle but pragmatic; (3) no clamp-midcase test (e.g. u_ff+u_track above max) — optional strengthener not blocking merge. Disposition open
- Evidence: tests/test_hvac_app.py
- Open: await done or further moves

## 16 — Wiring lock tests — add cases 1-4

Session: c250d733-0953-4430-bc20-39881c9df912 · Timestamp: 2026-10-16T17:33:00+03:00

- Action: User asked add cases for Thoughts findings 1-4; parent implemented in tests/test_hvac_app.py
- Result: added call-site source contract, behavioral z1 contrast, mid/negative residue, thermal config lock; pytest+ruff pending parent report (assume green if parent says)
- Evidence: tests/test_hvac_app.py
- Open: await user done or further moves; tree dirty with test edits

## 17 — Wiring lock tests — done

Session: c250d733-0953-4430-bc20-39881c9df912 · Timestamp: 2026-10-16T17:35:30+03:00

- Action: User marked Wiring lock tests done
- Result: accepted with strengtheners 1-4; advancing to Periphery
- Evidence: walkthrough-pr-24.md; tests/test_hvac_app.py 15 passed earlier
- Open: tree dirty (tests + walkthrough); commit question pending

## 18 — Periphery — presented

Session: c250d733-0953-4430-bc20-39881c9df912 · Timestamp: 2026-10-16T17:35:35+03:00

- Action: Presented Periphery block
- Result: awaiting user
- Evidence: narrative Periphery
- Open: await user

## 19 — Periphery — Thoughts

Session: c250d733-0953-4430-bc20-39881c9df912 · Timestamp: 2026-10-16T17:37:30+03:00

- Action: User chose Thoughts on Periphery
- Result: Plan/PR messaging OK for half CAP-1. Findings: (1) local strengtheners+walkthrough not on PR yet — merge gap until commit/push; (2) PR body still says story 1.2 OK, avoid CAP-1 done claim; (3) out-of-scope list correct. Disposition open
- Evidence: PR #24; story plan; dirty tests/test_hvac_app.py + walkthrough-pr-24/
- Open: await done/commit/wrap-up
