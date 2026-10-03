---
title: 'HACS custom-repo publish knobs'
type: 'feature'
ticket: ''
created: '2026-10-03'
status: 'built'
baseline_revision: 'cd324c728efac3563e7e42989a18a88e5d475d20'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/forge-hacs-packaging-meaning/forge-hacs-packaging-meaning.md'
  - '{project-root}/_bmad-output/research-hacs-appdaemon-feasibility-for-ha-smart/research-hacs-appdaemon-feasibility-for-ha-smart.md'
  - '{project-root}/_bmad-output/deferred-work.md'
  - '{project-root}/_bmad-output/plan-hacs-packaging.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Dual layout and public GitHub are done, but the repo still lacks HACS publish knobs (`hacs.json`, HACS Action, release/custom-repo guidance, GitHub metadata), so strangers cannot install via HACS custom repository.

**Approach:** Phase A on `feat/hacs-publish` (manifest, Validate workflow, README, tests, version bump, PR merge); Phase B after merge to `main` (set GitHub description/topics; agent publishes Release `v0.1.0` via `gh`). Ceiling remains public custom repository (not `hacs/default`).

## Boundaries & Constraints

**Always:**
- Keep dual layout: canonical package `apps/hvac/`; Exclusive Session via `app_dir: ../apps`; no symlink bridge.
- Root `hacs.json` is exactly `{"name": "ha-smart-hvac"}` (no extra fields required).
- HACS Action workflow uses `hacs/action@main` with `category: appdaemon`; include `actions/checkout` before the action; do not ignore structure/`hacsjson` checks.
- Ship placeholders only in tracked wiring (`apps/apps.yaml.example`); never commit live house entity IDs or secrets.
- README is **install-first**: after the title/badge, the lead opens with how a stranger adds this repo as a HACS AppDaemon custom repository and gets a working install (release + `app_dir` + `apps.yaml` from example). Dual-layout / Exclusive Session / Production operator material comes after that path — not as the opening frame. Retire “visibility flip still needed” / “hacs.json deferred” / unfinished “public-readiness prep” framing (repo is already public).
- Work Phase A on `feat/hacs-publish`; PRs only — never push commits to `main` casually.
- Bump `pyproject.toml` `version` to `0.1.0` in Phase A.
- Phase B (after PR merge to default branch `main`): set GitHub repo **description** to `AppDaemon apps for multi-zone OpenTherm HVAC control via Home Assistant` and **topics** to `home-assistant`, `appdaemon`, `hacs`, `hvac`, `opentherm`; then the build agent publishes the first GitHub Release with `gh release create v0.1.0 --target main` (published, not draft; generate or short notes OK).

**Never:**
- PR to `hacs/default` or claim default-store inclusion.
- Extract/mirror packaging repo; move package back under `appdaemon/apps/`.
- Rewrite as a Home Assistant `custom_components/` integration.
- Ignore HACS Action checks without a documented reason.
- Change live house entity ID values in local `apps/apps.yaml` without asking.
- Add a tag→Release CI workflow (rejected B); “automatic” means agent `gh release create` in Phase B, not Actions-on-tag.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| HACS Action on PR/push (Phase A) | `validate.yaml` runs on feature branch | `hacs/action@main` with `category: appdaemon` validates branch (no release yet) | Fail the job; do not ignore structure/`hacsjson` |
| Fresh HACS custom-repo install (after Phase B) | Public repo + `v0.1.0` release + metadata + `apps/hvac/` | HACS can add category AppDaemon; downloads `hvac/` under HA `appdaemon/apps/` | README covers `app_dir` when add-on default ≠ HACS path |
| Fresh clone / Exclusive Session | Local `apps/apps.yaml` from example | Unchanged dual-layout load path | Missing wiring → copy from example |
| Packaging tests after Phase A | Tracked tree on feature branch | Asserts `hacs.json` name, validate workflow, updated README; no `public-readiness` / deferred claims | CI red until tests updated |
| Phase B release | Knobs merged to `main` | `gh release view v0.1.0` shows published release; description/topics set | Halt Phase B if merge SHA missing or `gh` auth fails; do not invent a tag on the feature branch |

</frozen-after-approval>

## Code Map

- `hacs.json` (new) — exactly `{"name": "ha-smart-hvac"}`.
- `.github/workflows/validate.yaml` (new) — Validate workflow: checkout then `hacs/action@main`, `category: appdaemon`; triggers push/PR/schedule/`workflow_dispatch`; separate from `ci.yaml`.
- `.github/workflows/ci.yaml` — leave lint/test unchanged.
- `README.md` — **install-first lead**: title/badge → short product one-liner → HACS custom-repo install (add repo as AppDaemon, need a published release, `app_dir` when add-on path ≠ HACS path, copy `apps.yaml.example`). Then layout / Exclusive Session / Production `app_dir` / quality checks. Drop deferred/public-readiness-prep framing and the old “Public-visibility flip” blocker section.
- `pyproject.toml` — `version = "0.1.0"`.
- `tests/test_dual_layout.py` — remove `assert "public-readiness" in readme`; assert root `hacs.json` parses with `name == "ha-smart-hvac"`; assert validate workflow contains `category: appdaemon` (and `hacs/action`); assert Production/HACS `app_dir` examples remain; assert install-first ordering (custom-repo / HACS install guidance appears before Exclusive Session / `./scripts/run-appdaemon`); do not require the literal string `hacs.json` in README prose if the file assert covers the manifest.
- GitHub metadata (Phase B, via `gh`) — description + topics as locked in frozen Always.
- First Release (Phase B) — `gh release create v0.1.0 --target main` after merge; no release-on-tag workflow.
- `_bmad-output/deferred-work.md` — after Phase B, append a done note or leave a completed marker for the HACS knobs entry (do not delete prior evidence text).
- Do not touch: ADRs, HVAC algorithm modules, secrets/`.env`, live `apps/apps.yaml` values.

## Tasks & Acceptance

**Execution — Phase A (PR on `feat/hacs-publish`):**
- [x] `hacs.json` -- write `{"name": "ha-smart-hvac"}` -- HACS manifest
- [x] `.github/workflows/validate.yaml` -- checkout + `hacs/action@main` `category: appdaemon` -- HACS validation CI
- [x] `pyproject.toml` -- set `version = "0.1.0"` -- match release tag
- [x] `README.md` -- install-first lead (HACS custom-repo path before dual-layout/dev); remove deferred/public-flip blocker language -- stranger sees install before philosophy
- [x] `tests/test_dual_layout.py` -- drop `public-readiness`; add `hacs.json` + validate workflow + install-first README ordering asserts -- packaging invariants
- [ ] Open PR, merge to `main` (human/CI green) -- knobs on default branch before Phase B

**Execution — Phase B (after merge to `main`, agent via `gh`):**
- [ ] GitHub description + topics -- set locked strings via `gh repo edit` -- HACS general publish metadata
- [ ] First GitHub Release -- `gh release create v0.1.0 --target main` (published, not draft) -- HACS prefers releases; decision C + version A + agent publish
- [ ] `_bmad-output/deferred-work.md` -- note HACS knobs entry completed -- close the deferred loop

**Acceptance Criteria:**
- Given Phase A on the feature branch, when Validate runs, then `hacs/action@main` uses `category: appdaemon` without ignoring `hacsjson`/structure checks.
- Given the tracked tree after Phase A, when inspecting the root, then `hacs.json` equals `{"name": "ha-smart-hvac"}` and `pyproject.toml` has `version = "0.1.0"`.
- Given README after Phase A, when a stranger reads from the top, then the first substantive section is HACS custom-repo install (before Exclusive Session / dual-layout deep-dive), and following it they can add the repo as AppDaemon and wire from `apps/apps.yaml.example` without any `hacs/default` claim.
- Given `uv run pytest` and ruff on `apps` + `tests` after Phase A, when packaging tests run, then they pass and do not require `public-readiness` or “HACS deferred” wording.
- Given Phase A merged to `main`, when Phase B runs, then repo description/topics match the locked values and `gh release view v0.1.0` shows a published release targeting `main`.

## Implementation Notes

- 2026-10-03 Phase A file work on `feat/hacs-publish` (no push / no remote ops):
  - Added root `hacs.json` (`{"name": "ha-smart-hvac"}`).
  - Added `.github/workflows/validate.yaml` per Design Notes (`actions/checkout@v4` then `hacs/action@main`, `category: appdaemon`; no ignore flags).
  - Bumped `pyproject.toml` `version` to `0.1.0`.
  - Rewrote `README.md` install-first: HACS custom-repo path before Layout / Exclusive Session; removed public-readiness / deferred-hacs / Public-visibility flip blocker framing.
  - Updated `tests/test_dual_layout.py`: dropped `public-readiness` / README `hacs.json` prose asserts; added `hacs.json` parse, validate-workflow, and install-before-Exclusive-Session ordering asserts.
  - Verified locally: `uv run pytest` (42 passed); `uv run ruff check apps tests && uv run ruff format --check apps tests` clean.
  - Left incomplete: Phase A PR open/merge; all Phase B (`gh repo edit`, `gh release create v0.1.0`, deferred-work closeout). Validate workflow green only after push/PR.

## Plan Change Log

- 2026-10-03 plan review: split Phase A (PR) vs Phase B (post-merge); lock `hacs.json` name `ha-smart-hvac`; lock `hacs/action@main` + checkout; include GitHub description/topics; agent `gh release create` (not tag→Release workflow); spell test assertion flips; section-based README tasks; deferred-work closeout.
- 2026-10-03 party: human required install-first README lead before greenlight — stranger HACS custom-repo path opens the doc; dual-layout/Exclusive Session follows.

## Review Triage Log

| Finding | Verdict | Route | Evidence |
|---------|---------|-------|----------|
| README Install §5 `cp apps/apps.yaml.example` invalid after HACS download (only `hvac/` lands under `appdaemon/apps/`) | medium | patch | Verified: HACS downloads first `apps/` dir contents only; example is sibling of `hvac/`, not inside package. Stranger following Install §5 cannot copy that path on HA. |
| Exclusive Session step 3 points at HACS-framed Install §5 (“next to downloaded `hvac/`”) | medium | patch | Same root cause as above — conflated clone vs HACS wiring paths. Exclusive Session needs in-repo `cp apps/apps.yaml.example apps/apps.yaml`. |
| `_bmad/custom/config.toml` / commit `a8760fe` in diff vs baseline | medium | patch | Verified: unrelated BMAD pin on `feat/hacs-publish` ahead of `main` at baseline; not in Phase A Code Map. Drop from this change’s branch tip. |
| Phase A PR/Validate not green yet | false | — | Expected under step-03 no-remote; Implementation Notes already track. Not a code defect in the staged knobs. |

## Design Notes

Validate workflow shape:

```yaml
name: Validate
on:
  push:
  pull_request:
  schedule:
    - cron: "0 0 * * *"
  workflow_dispatch:
permissions: {}
jobs:
  validate-hacs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hacs/action@main
        with:
          category: appdaemon
```

**Phase B release runbook** (agent, after merge commit is on `origin/main`):

```bash
gh repo edit --description "AppDaemon apps for multi-zone OpenTherm HVAC control via Home Assistant" \
  --add-topic home-assistant --add-topic appdaemon --add-topic hacs --add-topic hvac --add-topic opentherm
gh release create v0.1.0 --target main --title "v0.1.0" --generate-notes
gh release view v0.1.0
```

Do not tag from `feat/hacs-publish`. If Validate after the first release starts checking the release artifact, re-run or confirm it stays green on `main`.

## Verification

**Commands (Phase A):**
- `uv run pytest` -- expected: pass
- `uv run ruff check apps tests && uv run ruff format --check apps tests` -- expected: clean
- After push: Validate workflow green on the PR branch

**Commands (Phase B):**
- `gh repo view --json description,repositoryTopics` -- expected: locked description + topics
- `gh release view v0.1.0` -- expected: published release

**Manual checks:**
- Sole app package under `apps/` is `hvac/`.
- No live house IDs in tracked files; no `hacs/default` deliverable.
- README has custom-repo steps; no deferred/public-flip-as-blocker leftovers.
