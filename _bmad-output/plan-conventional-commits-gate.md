---
title: 'Conventional Commits PR gate (title + commits)'
type: 'feature'
ticket: ''
created: '2026-10-03'
status: 'done'
baseline_revision: '96becceadee7a6b3d30858d2eebdfe1d73a82d68'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/forge-hacs-release-automation/forge-hacs-release-automation.md'
  - '{project-root}/.cursor/skills/git-workflow/SKILL.md'
  - '{project-root}/_bmad-output/deferred-work.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Conventional Commits are skill guidance only today, so bad PR titles or commit subjects can merge unchecked — and that will break or silently skip a future semantic-release train.

**Approach:** Add a Python/shell PR CI gate that fails when the PR title is not Conventional Commits **or** when any non-merge commit in the PR range is not, and make those checks required on the `branch-protection` ruleset. Scope is the gate only; python-semantic-release release automation is deferred.

## Boundaries & Constraints

**Always:**
- Gate **both** PR title and non-merge commits in `base…head` (covers merge commits and future squash). Ignore git merge commits when linting subjects (e.g. `Merge branch 'main' into …`).
- Types match `.cursor/skills/git-workflow/SKILL.md`: `feat|fix|docs|style|refactor|perf|test|build|ci|chore` (+ breaking `!` / `BREAKING CHANGE`).
- Checker is **Python/shell only** (stdlib or existing project Python); no Node, no `package.json`, no commitlint.
- Run on `pull_request` (`opened`, `edited`, `synchronize`, `reopened`); keep independent of lint/test/HACS validate jobs.
- After the workflow lands, add its check(s) as **required** status checks on ruleset `branch-protection` so a red gate blocks merge to `main`.
- PRs-only for human code; do not push feature work to `main`.
- Leave `hacs.json`, `validate.yaml`, and install-first README lead unchanged.

**Never:**
- python-semantic-release / release workflow / changelog write-back / tag publish in this plan (see `_bmad-output/deferred-work.md`).
- Relying on the git-workflow skill or docs alone as the gate.
- Introducing a Node/commitlint toolchain (including Action-only Node stacks) for this gate.
- commitizen (or similar) as a version calculator.
- Changing house entity IDs in local `apps/apps.yaml` without asking.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Bad PR title | Title not Conventional Commits | Title check fails; required check blocks merge | Fix title and re-run |
| Bad commit subject | ≥1 non-merge commit in PR range not CC | Commits check fails; required check blocks merge | Rewrite/fixup history |
| Good title + commits | CC title and all non-merge commits CC | Both checks green | No error expected |
| Good title, bad commit | Title OK, one non-merge commit not CC | Title green; commits fail; merge blocked | Partial green OK |
| Synced with main | PR contains a merge commit from `main` plus CC feature commits | Merge commit ignored; commits check uses remaining subjects | Do not fail on merge subjects |

</frozen-after-approval>

## Code Map

- `_bmad-output/forge-hacs-release-automation/forge-hacs-release-automation.md` — locked dual CC gate; PSR train deferred.
- `_bmad-output/deferred-work.md` — PSR release train + locked auth (PAT for existing bypass user); `source_plan` points here after rename.
- `.cursor/skills/git-workflow/SKILL.md` — soft CC type/subject rules to encode in the Python checker and note CI enforcement.
- `.github/workflows/ci.yaml` / `validate.yaml` — leave alone; do not fold the gate in; do not regress HACS packaging tests.
- `scripts/run-appdaemon` — existing repo `scripts/` home; add the checker beside it.
- `tests/test_dual_layout.py` — YAML substring pattern for workflow shape; keep green.
- GitHub ruleset `branch-protection` (id `24390720`) — today: `pull_request`, `non_fast_forward`, `deletion`; **no** `required_status_checks`. Must gain required checks for this workflow’s job name(s).

**Reuse:** `actions/checkout@v4` + `astral-sh/setup-uv@v5` + `uv run python` (same Python 3.12 as CI). Prefer one shared validator module/function for title and commit subjects.

**Do not change:** `apps/hvac/` logic; HACS knobs; Exclusive Session / dual-layout invariants.

## Tasks & Acceptance

**Execution:**
- [x] `scripts/check_conventional_commits.py` -- add a stdlib Python checker: validate one message (title or subject) against the skill type list; CLI modes for `--title` and for linting commits in a git revision range while **skipping merge commits**; non-zero exit on failure with clear stderr -- single source of CC rules
- [x] `tests/test_conventional_commits.py` -- unit-test the checker offline: valid/invalid titles, valid/invalid subjects, merge-commit skip, breaking `!` / footer acceptance as needed for the chosen regex -- prove rules without live Actions
- [x] `.github/workflows/conventional-commits.yaml` -- PR workflow with two jobs (`pr-title`, `pr-commits`): title job reads `github.event.pull_request.title` and runs the script; commits job checks out with `fetch-depth: 0` and runs the script on `base.sha…head.sha`; set minimal `permissions` (`contents: read`, and `pull-requests: read` if the title job needs the event payload only — keep least privilege); pin action versions; no Node -- dual CI gate
- [x] `tests/test_dual_layout.py` (or extend `tests/test_conventional_commits.py`) -- assert workflow exists, `on: pull_request`, job ids `pr-title` / `pr-commits`, and invokes `scripts/check_conventional_commits.py` -- lock workflow shape
- [x] Ruleset `branch-protection` -- add required status checks for both job names from `conventional-commits.yaml` (via `gh` API or Settings); verify a red check blocks merge -- make the gate enforceable
- [x] `.cursor/skills/git-workflow/SKILL.md` -- note that CI enforces CC on PR title and non-merge commits, and merge commits are ignored by the commits job -- agents treat skill + CI as aligned

**Acceptance Criteria:**
- Given a PR whose title is not Conventional Commits, when PR checks run with required checks configured, then the `pr-title` check fails and merge to `main` is blocked.
- Given a PR with any non-merge non-CC commit in `base…head`, when PR checks run with required checks configured, then the `pr-commits` check fails and merge is blocked even if the title is valid.
- Given a PR that only added a merge commit from `main` plus otherwise CC commits, when `pr-commits` runs, then the merge commit is ignored and the job passes.
- Given a PR with a CC title and all non-merge CC commits, when PR checks run, then both `pr-title` and `pr-commits` pass.
- Given offline tests run, when `uv run pytest tests/test_conventional_commits.py` executes, then valid/invalid/merge-skip cases pass without calling GitHub Actions.

## Implementation Notes

- 2026-10-03: Implemented on branch `ci/conventional-commits-gate` (not committed). Added `scripts/check_conventional_commits.py` (stdlib regex + `--title` / `--range` with `git log --no-merges`), `tests/test_conventional_commits.py` (valid/invalid/merge-skip + workflow shape), `.github/workflows/conventional-commits.yaml` (jobs `pr-title` / `pr-commits`, `permissions: contents: read`, title/range via env), and CI note in `.cursor/skills/git-workflow/SKILL.md`. Did not extend ruff `src` to `scripts/` (stdlib-only script; CI ruff still `apps tests`).
- Verified: `uv run pytest tests/test_conventional_commits.py tests/test_dual_layout.py` (35 passed); `uv run ruff check apps tests` + `ruff format --check apps tests` clean; CLI smoke `--title` good/bad exit codes.
- **Ruleset:** human added required status checks `pr-title` and `pr-commits` on `branch-protection` (id `24390720`); verified via `gh api` (`required_status_checks` present, `strict_required_status_checks_policy: true`).
- 2026-10-03 review patch: `CC_RANGE` switched to two-dot `base.sha..head.sha`; tests cover behind-main three-dot fail / two-dot pass + workflow YAML `..` lock.
- 2026-10-03: Migration deferred entry closed — workflow on `main` (PR #14), zero open PRs stuck on missing checks; plan status → `done`. PSR train deferred from this plan also closed (live `v0.2.0`).

## Plan Change Log

- 2026-10-03 plan review: ignore merge commits; require both jobs on ruleset `branch-protection` (not advisory); replace Node/commitlint with `scripts/check_conventional_commits.py` + offline unit tests; lock job ids `pr-title`/`pr-commits` and workflow path; least-privilege permissions; rename plan from `plan-hacs-release-automation.md` to `plan-conventional-commits-gate.md` and retarget deferred-work `source_plan`. Avoids false fails on sync merges, merge-block ACs that could not enforce, and a JS toolchain the forge stance rejected.

## Review Triage Log

- 2026-10-03 quick pass — verdicts: 1 high (patch), 1 medium (defer), 1 false
  - high → patch | `.github/workflows/conventional-commits.yaml` `CC_RANGE` three-dot `base...head` | Three-dot symmetric difference includes commits on `main` not in the PR when the branch is behind; `pr-commits` can fail on historical non-CC subjects (e.g. `Move HVAC package…`) and unmet “good PR passes” AC. Two-dot `base..head` is the PR-only set. Evidence: reviewer local repro + non-CC subject still on `main`.
  - medium → defer | Ruleset required checks already set while workflow not yet on `main` | True for other PRs that lack the workflow file (checks stay pending). Same-repo PR that adds the workflow still runs it from the head ref; migration risk until this PR merges — not a checker defect.
  - false | `_bmad-output/deferred-work.md` uv.lock vs forge | Forge locked pyproject + CHANGELOG write-back; `uv.lock` sync is a necessary consequence of `project.version` bump under `uv sync --frozen` in this repo, not a forbidden contradiction of forge intent.

## Design Notes

**Why both gates:** Merge / squash / rebase are all allowed. Title always matters (squash). Non-merge commit subjects matter for merge/rebase and future PSR. Sync merge commits are ignored in `pr-commits` only.

**Checker:** stdlib `re` for `^(feat|fix|docs|style|refactor|perf|test|build|ci|chore)(\([^)]+\))?(!)?: .+` — type/shape first; do not invent stricter rules than the skill (≤72 remains guidance unless already cheap).

**Workflow:** `permissions: contents: read`; jobs `pr-title` (`--title` from `github.event.pull_request.title`) and `pr-commits` (`fetch-depth: 0`, `--range base..head` two-dot — not three-dot, so main-only commits when the branch is behind are not linted); both `uv run python scripts/check_conventional_commits.py`.

**Required checks:** Add job check names `pr-title` and `pr-commits` to ruleset id `24390720` via `gh api`; if the token lacks admin, halt for the human Settings path.

## Verification

**Commands:**
- `uv run pytest tests/test_conventional_commits.py tests/test_dual_layout.py` -- checker + packaging asserts green
- `uv run ruff check apps tests` -- still clean; include `scripts` only if ruff `src` is extended for the new file

**Manual checks:**
- Ruleset required checks list includes both jobs after the ruleset task
