# Review log: PR #26 retune defaults, u_track_max, ADR 0002

Target: https://github.com/zhmachenkov-d/ha-smart-hvac/pull/26

## 1 — orientation — started

Session: unavailable · Timestamp: 2026-10-16T18:39:00+03:00

- Action: Orientation started for initiative-fix-ladrc-blow-up; assumed target PR #26 (`fix/1-3-retune-defaults-u-track-max` @ `81e3378` → `main`); created walkthrough scaffolding
- Result: `walkthrough-pr-26.md` + `walkthrough-pr-26-log.md` in place; narrative is stub only (Target pending confirmation)
- Evidence: [PR #26](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/26); prior pattern [walkthrough-pr-24](../walkthrough-pr-24/walkthrough-pr-24.md)
- Open: Await user confirmation of target (PR #26) and review focus; then draft Intent/Broad strokes/slices

## 2 — orientation — approved

Session: f9d46452-4497-493f-ad88-641b8bb3c947 · Timestamp: 2026-10-16T18:40:00+03:00

- Action: User approved full PR #26; focus risks/boundaries/merge-readiness; drafted all narrative blocks
- Result: Narrative written; current block Intent (in progress)
- Evidence: PR #26; story-retune-defaults-u-track-max-config-adr-amend-plan.md frozen Intent
- Open: none for orientation

## 3 — Intent — Thoughts

Session: f9d46452-4497-493f-ad88-641b8bb3c947 · Timestamp: 2026-10-16T18:42:00+03:00

- Action: Thoughts on Intent vs PR #26 diff and Never-list (no guard wire)
- Result: Intent accurate; scopes field-only u_track_max + thermal retune + CAP-3(b) + ADR 0002; guard deferred entry 4. Findings (notes): (1) hvac_app has zero u_track_max refs — matches Approach; (2) ADR 0003 absent from diff — matches; (3) omega_c kept 0.053 in example — Approach says b0/omega_o thermal only. Disposition: accepted as-is pending user done
- Evidence: apps/apps.yaml.example; apps/hvac/models.py; apps/hvac/config.py; docs/adr/0002; git diff main...HEAD no ADR 0003 / no hvac_app
- Open: await user done or further Intent moves

## 4 — Intent — done

Session: f9d46452-4497-493f-ad88-641b8bb3c947 · Timestamp: 2026-10-16T18:43:00+03:00

- Action: User marked Intent done; advance to Broad strokes
- Result: Intent accepted as-is; current block Broad strokes
- Evidence: walkthrough-pr-26.md Intent section
- Open: none

## 5 — Broad strokes — Thoughts

Session: f9d46452-4497-493f-ad88-641b8bb3c947 · Timestamp: 2026-10-16T18:44:00+03:00

- Action: Thoughts on Broad strokes entry-point order vs load-bearing seams
- Result: Order OK for human scan. Findings (open notes): (1) with_omega_c live call site hvac_app.py ~L87 is why preserve matters — not listed as entry; OK for slice Config handoff; (2) CAP-3(b) vs CAP-5: example-aligned omega_c=0.053 vs thermal CAP-5 0.01 — Broad strokes correctly points at CAP-3(b) not CAP-5; (3) test_parse_apps_yaml_example bridges example→parse — could be entry but fine in Config handoff slice. Disposition: accepted pending user done
- Evidence: tests/test_ladrc.py CAP-3(b)/CAP-5; apps/hvac/hvac_app.py with_omega_c; test_ladrc_tuner.py parse example
- Open: await done or further moves

## 6 — Broad strokes — Test

Session: f9d46452-4497-493f-ad88-641b8bb3c947 · Timestamp: 2026-10-16T18:44:30+03:00

- Action: Ran PR test plan — pytest test_ladrc+test_ladrc_tuner; ruff on touched py; empty ADR 0003 diff
- Result: 27 passed; ruff clean; ADR 0003 diff 0 bytes. Disposition: verified green. Spot-check ADR/example comments still human (not auto-tested)
- Evidence: uv run pytest … -q → 27 passed; ruff All checks passed; git diff ADR 0003 wc -c = 0
- Open: human spot-check ADR must-language / example comments if desired; await done

## 7 — Broad strokes — spot-check comments

Session: f9d46452-4497-493f-ad88-641b8bb3c947 · Timestamp: 2026-10-16T18:45:30+03:00

- Action: Human-requested spot-check of example comments + ADR 0002 must-language vs story Always/Never
- Result: Both example comments match mandatory plan wording; ADR has must/must-not for Huang, house calibration, exp_map fail, continuous ESO, known input C; no Euler/substep recipe. Disposition: accepted as-is
- Evidence: apps/apps.yaml.example:19-23; docs/adr/0002 L7-9; story plan Always bullets
- Open: await Broad strokes done

## 8 — Broad strokes — done

Session: f9d46452-4497-493f-ad88-641b8bb3c947 · Timestamp: 2026-10-16T18:46:30+03:00

- Action: User marked Broad strokes done; advance to Config handoff
- Result: Broad strokes accepted; current block Config handoff
- Evidence: walkthrough-pr-26.md; prior Thoughts/Test/spot-check entries
- Open: none

## 9 — Config handoff — Thoughts

Session: f9d46452-4497-493f-ad88-641b8bb3c947 · Timestamp: 2026-10-16T18:47:30+03:00

- Action: Thoughts on Config handoff risks/boundaries/merge-readiness
- Result: Field+parse+preserve+example lock look correct. Findings: (1) with_omega_c hand-lists fields — preserve present; future fields same footgun; (2) no validate u_track_max sign/range — OK for unused field; defer to entry 4; (3) omit→100 locked by test_parse_bandwidth; (4) dead until guard — example comment mitigates false expectation; (5) when guard lands must read effective_ladrc (post with_omega_c) not raw config.ladrc. Disposition: accepted pending user done; (5) note for story 1.4
- Evidence: models.py with_omega_c; config.py get default; hvac_app.py:87-110; test_ladrc_tuner parse/preserve/example
- Open: await done; story 1.4 note on effective_ladrc

## 10 — Config handoff — Test

Session: f9d46452-4497-493f-ad88-641b8bb3c947 · Timestamp: 2026-10-16T18:48:30+03:00

- Action: Ran focused parse/preserve/example tests for u_track_max handoff
- Result: 4 passed (omit→100, explicit 50, with_omega_c preserve 75, apps.yaml.example). Disposition: verified green
- Evidence: pytest test_parse_bandwidth_ladrc_config, test_parse_u_track_max_explicit, test_with_omega_c_preserves_u_track_max, test_parse_apps_yaml_example
- Open: await Config handoff done

## 11 — Config handoff — done

Session: f9d46452-4497-493f-ad88-641b8bb3c947 · Timestamp: 2026-10-16T18:49:30+03:00

- Action: User marked Config handoff done; advance to CAP-3(b) boundedness
- Result: Config handoff accepted; current block CAP-3(b)
- Evidence: walkthrough-pr-26.md; Thoughts/Test entries 9–10
- Open: none

## 12 — CAP-3(b) — Thoughts

Session: f9d46452-4497-493f-ad88-641b8bb3c947 · Timestamp: 2026-10-16T18:50:30+03:00

- Action: Thoughts on CAP-3(b) vs CAP-5/spec; measured max|u_track| on locked scenario
- Result: Test matches story Always. Findings: (1) example ωc=0.053 is stricter than CAP-5 0.01 (max|u|≈36 vs ≈19) — good product lock; (2) bar <100 = CAP-5 tens-of-°C bar, margin OK; (3) shares _run_thermal_c_ticks C path with CAP-5; (4) dual source: helper numbers vs YAML — parse_apps_yaml_example bridges; (5) no Huang/guard asserts here — out of story scope (CAP-3a/c). Disposition: accepted pending done
- Evidence: tests/test_ladrc.py CAP-3(b)/helpers; measured max|u| example 36.2; spec CAP-3(b)
- Open: await done or Test

## 13 — CAP-3(b) — Test

Session: f9d46452-4497-493f-ad88-641b8bb3c947 · Timestamp: 2026-10-16T18:51:30+03:00

- Action: Ran CAP-3(b) + sibling CAP-5 continuous/exp_map tests
- Result: 3 passed (cap3b bounded, cap5 continuous bounded, cap5 exp_map diverges). Disposition: verified green
- Evidence: pytest test_cap3b_example_aligned_continuous_c_bounded + two CAP-5 neighbors
- Open: await CAP-3(b) done

## 14 — CAP-3(b) — done

Session: f9d46452-4497-493f-ad88-641b8bb3c947 · Timestamp: 2026-10-16T18:52:30+03:00

- Action: User marked CAP-3(b) done; advance to ADR 0002 must-language
- Result: CAP-3(b) accepted; current block ADR 0002
- Evidence: walkthrough-pr-26.md; Thoughts/Test entries 12–13
- Open: none

## 15 — ADR 0002 — Thoughts

Session: f9d46452-4497-493f-ad88-641b8bb3c947 · Timestamp: 2026-10-16T18:54:30+03:00

- Action: Thoughts on ADR 0002 CAP-4 amend vs old soft wording and Never-list
- Result: Soft "not copy-paste" replaced by must/must-not; all five CAP-4 bullets present; no Euler/substep recipe; ADR 0003 diff 0. Findings: (1) "need house calibration" matches plan wording (not must); (2) β1/β2 over the sample = gain form, not integrator recipe; (3) guard/u_track_max not in ADR — CAP-2/entry 4, OK. Disposition: accepted pending done
- Evidence: git diff main...HEAD ADR 0002; ADR 0003 wc 0; story Always CAP-4
- Open: await done

## 16 — ADR 0002 — done

Session: f9d46452-4497-493f-ad88-641b8bb3c947 · Timestamp: 2026-10-16T18:55:30+03:00

- Action: User marked ADR 0002 done; advance to Periphery
- Result: ADR 0002 accepted; current block Periphery
- Evidence: walkthrough-pr-26.md; Thoughts entry 15
- Open: none

## 17 — Periphery — Thoughts

Session: f9d46452-4497-493f-ad88-641b8bb3c947 · Timestamp: 2026-10-16T18:57:30+03:00

- Action: Thoughts on periphery artifacts vs merge-readiness
- Result: Story plan status built OK; memlog incidental (+5 party 1.3 lines) not load-bearing — noise in PR but matches prior PRs; CI all pass; walkthrough-pr-26 still untracked local (not in PR yet). Findings: (1) memlog in PR is optional clutter — accept as-is or strip in follow-up, not blocking; (2) story remains built not done until walkthrough close/merge; (3) CI green supports merge. Disposition: accepted pending done; note commit walkthrough after wrap
- Evidence: story plan status built; .memlog.md tail; gh pr checks 26 pass; git status ?? walkthrough-pr-26
- Open: await done / Wrap-up; commit walkthrough?

## 18 — Periphery — done

Session: f9d46452-4497-493f-ad88-641b8bb3c947 · Timestamp: 2026-10-16T18:58:30+03:00

- Action: User marked Periphery done; all narrative blocks complete
- Result: Periphery accepted; suggest Wrap-up (commit walkthrough, merge PR #26, story→done)
- Evidence: walkthrough-pr-26.md; CI pass; ?? walkthrough-pr-26/
- Open: user Wrap-up choices

## 19 — Wrap-up — started

Session: f9d46452-4497-493f-ad88-641b8bb3c947 · Timestamp: 2026-10-16T19:02:30+03:00

- Action: User chose wrap-up 1+2+delete branch+3; parent will commit walkthrough+story done, merge PR #26, delete feature branch
- Result: Narrative closed; story status set done (pending commit)
- Evidence: user instruction; PR #26 MERGEABLE
- Open: commit/push/merge/delete

## 20 — Wrap-up — commit

Session: f9d46452-4497-493f-ad88-641b8bb3c947 · Timestamp: 2026-10-16T19:03:00+03:00

- Action: Commit walkthrough-pr-26 + story status done on feature branch before merge
- Result: staged for docs commit
- Evidence: walkthrough-pr-26/; story plan status done
- Open: push, merge PR #26, delete branch
