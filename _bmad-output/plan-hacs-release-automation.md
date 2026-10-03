---
title: 'HACS release train (python-semantic-release)'
type: 'feature'
ticket: ''
created: '2026-10-03'
status: 'built'
baseline_revision: 'deee8a22e2b33be03cd283711f1e2a890ee01f4e'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/forge-hacs-release-automation/forge-hacs-release-automation.md'
  - '{project-root}/_bmad-output/deferred-work.md'
  - '{project-root}/.cursor/skills/git-workflow/SKILL.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** HACS install/update needs published GitHub Releases, but after the manual `v0.1.0` cut there is no CI train — version, changelog, tag, and Release can drift or be forgotten on every merge to `main`.

**Approach:** Add python-semantic-release on `push` to `main`: bump `pyproject.toml` from Conventional Commits, write back `CHANGELOG.md` + `uv.lock`, tag `v{version}`, and publish a GitHub Release with no assets, authenticated by a dedicated PAT for the existing branch-protection bypass user.

## Boundaries & Constraints

**Always:**
- Ceiling stays public HACS **custom repository**; publish **GitHub Releases** (not tags alone).
- Tooling: **python-semantic-release** only (semantic-release family); version source `pyproject.toml`; tag format `v{version}`; baseline tag `v0.1.0` already exists.
- Bump policy = Conventional Commits / PSR defaults: `feat`→minor, `fix`→patch, breaking→major; `docs` / `ci` / `chore` (and other non-release types under PSR defaults) → no release.
- Write-back commit on `main` includes `pyproject.toml`, `CHANGELOG.md`, and `uv.lock` (lock refresh after version bump so `uv sync --frozen` stays valid). Write-back commit subject must be non-releasing (`chore`/`ci` under PSR defaults) so the PAT-driven second `push` no-ops.
- Auth: repo secret `SEMANTIC_RELEASE_TOKEN` = fine-grained or classic **PAT for the existing `branch-protection` bypass user** (ruleset id `24390720`; bypass `actor_id` `22600261`) — not bare `GITHUB_TOKEN`, not a new GitHub App. Workflow must pass that secret to **both** `actions/checkout` `token:` (persist credentials) **and** `GH_TOKEN` for the PSR CLI.
- Trigger: `push` to `main` only (plus optional `workflow_dispatch` for dry-run if cheap). Human feature work stays PRs-only; bot write-back is the explicit exception. Do not cancel in-flight release runs on newer pushes (`cancel-in-progress: false`); after checkout, `git reset --hard ${{ github.sha }}` so the evaluated tip matches the triggering SHA.
- Leave `ci.yaml`, `validate.yaml`, Conventional Commits gate, `hacs.json`, and install-first README lead behavior intact (README may note that releases are automated after merge).
- `build_command` refreshes/stages `uv.lock` only — **do not** run `uv build` or upload Release assets.

**Never:**
- release-please, JS `semantic-release`, commitizen (or a second version calculator), binary Release assets, PyPI publish, or `uv build` in the release path.
- Relying on `GITHUB_TOKEN` alone for protected-`main` write-back / tag / Release.
- Changing house entity IDs in local `apps/apps.yaml` without asking.
- Folding the release job into the PR CI / Validate / CC workflows.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Releasing merge | Push to `main` with ≥1 `feat`/`fix`/breaking since last release | Version bump + CHANGELOG + `uv.lock` write-back, `v*` tag, published GH Release (no assets) | Job fails closed on error; if write-back/tag/Release diverge mid-flight, human recovers (create missing Release or delete orphan tag) before re-running |
| Non-releasing merge | Push with only `docs`/`ci`/`chore` (etc.) commits | Workflow runs; PSR exits 0 without bump/tag/Release | No error expected |
| PAT write-back re-trigger | Bot pushes non-releasing write-back to `main` | Second workflow run starts; PSR no-ops (already released tip / no releasing commits) | Do not suppress the re-run; exit 0 with no second bump |
| Missing/invalid secret | `SEMANTIC_RELEASE_TOKEN` absent or lacks bypass/write | Job fails; prefer no successful Release without matching write-back on `main` | Human fixes secret/PAT; re-run; reconcile any orphan tag/Release |
| Already released tip | Tip of `main` already tagged for current version | No new release | No error expected |

</frozen-after-approval>

## Code Map

- `_bmad-output/forge-hacs-release-automation/forge-hacs-release-automation.md` — locked train, rejects, `v` prefix, PAT-not-GITHUB_TOKEN.
- `_bmad-output/deferred-work.md` — PSR entry + `uv.lock` write-back + PAT for existing bypass user.
- `pyproject.toml` — `project.version = "0.1.0"` today; add `[tool.semantic_release]` (`version_toml`, `tag_format = "v{version}"`, changelog on, GitHub Release on, assets off, `commit_message` non-releasing, `build_command` = `uv lock --upgrade-package "$PACKAGE_NAME"` + `git add uv.lock` only — **never** `uv build`). Pin `python-semantic-release` via uv so the workflow can `uv run`/`uvx` it — prefer runner+uv over the PSR Docker Action.
- `uv.lock` — virtual package `ha-smart-hvac` version must track `pyproject.toml` after each bump.
- `.github/workflows/release.yaml` (new) — `on.push.branches: [main]`; concurrency without canceling in-progress; `actions/checkout@v4` with `fetch-depth: 0`, `token: ${{ secrets.SEMANTIC_RELEASE_TOKEN }}`, persist credentials; `git reset --hard ${{ github.sha }}`; `astral-sh/setup-uv@v5` + Python 3.12; `env.GH_TOKEN: ${{ secrets.SEMANTIC_RELEASE_TOKEN }}`; run PSR publish; no asset upload.
- `.github/workflows/ci.yaml`, `validate.yaml`, `conventional-commits.yaml` — do not regress; CC gate remains the human-PR quality bar for bump-driving subjects.
- `tests/test_release_workflow.py` (new) — assert workflow path, `push`→`main`, checkout uses `SEMANTIC_RELEASE_TOKEN`, `GH_TOKEN` wiring, PSR invocation, no asset upload, `build_command` has no `uv build`.
- `tests/test_dual_layout.py` / `tests/test_conventional_commits.py` — keep green; do not weaken HACS/CC asserts.
- `README.md` — optional one-liner that post-`v0.1.0` releases are cut by CI on `main` (do not bury the install-first lead).
- GitHub repo secret `SEMANTIC_RELEASE_TOKEN` + ruleset `branch-protection` (id `24390720`, bypass actor `22600261`) — human configures PAT; agent does not invent a new App.

**Reuse:** `actions/checkout@v4` + `astral-sh/setup-uv@v5` + Python 3.12; PSR docs for uv lock write-back and PAT checkout.

**Do not change:** `apps/hvac/` control logic; Exclusive Session / dual-layout invariants; CC checker rules.

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml` (+ `uv.lock` via `uv lock`/`uv add`) -- add python-semantic-release and `[tool.semantic_release]` for `version_toml`, `tag_format`, changelog on, GitHub Release on, assets off, non-releasing write-back `commit_message`, and `build_command` that refreshes/stages `uv.lock` only (**no** `uv build` / PyPI/wheel) -- single version SoT + lock sync
- [x] `.github/workflows/release.yaml` -- `push` to `main` (+ optional `workflow_dispatch`); concurrency `cancel-in-progress: false`; checkout with PAT token + full history + `git reset --hard ${{ github.sha }}`; setup-uv 3.12; `GH_TOKEN` from `secrets.SEMANTIC_RELEASE_TOKEN`; run PSR; no asset upload -- release train
- [x] `tests/test_release_workflow.py` -- lock workflow shape (trigger, checkout token, `GH_TOKEN`, PSR invocation, no assets) and assert `build_command` contains no `uv build` -- prove shape without live Actions
- [x] `README.md` -- brief note that releases after `v0.1.0` are automated on merge to `main`, without disturbing install-first HACS lead -- operators know Releases keep coming
- [ ] Repo secret + PAT (human) -- create `SEMANTIC_RELEASE_TOKEN` owned by bypass user `actor_id` `22600261` (ruleset `24390720`); fine-grained: Contents Read/Write, Metadata Read (plus whatever PSR needs for Releases); classic: `repo` scope; verify workflow can authenticate -- make write-back enforceable
- [ ] `_bmad-output/deferred-work.md` -- mark the PSR deferred entry done when the train is merged and verified -- close the split from the CC gate plan

**Acceptance Criteria:**
- Given `main` receives a merge whose commits since the last release include a `feat` or `fix` (or breaking), when the release workflow finishes successfully, then `pyproject.toml` / `CHANGELOG.md` / `uv.lock` are updated on `main`, a `v*` tag exists, and `gh release view` shows a published Release with no binary assets.
- Given `main` receives only non-releasing commits (`docs`/`ci`/`chore` etc. under PSR defaults), when the workflow finishes, then no new version, tag, or Release is created.
- Given a successful releasing run whose write-back push re-triggers the workflow, when the second run finishes, then it exits successfully with no additional bump/tag/Release.
- Given `SEMANTIC_RELEASE_TOKEN` is missing or cannot bypass/write, when the workflow runs on a releasing push, then the job fails; if tag/Release and write-back diverge, recover manually before retrying.
- Given offline tests run, when `uv run pytest tests/test_release_workflow.py` (and existing packaging/CC tests) execute, then workflow-shape and no-`uv build` asserts pass without calling GitHub Actions.

## Implementation Notes

- 2026-10-03 agent: Added `python-semantic-release` (dev group), `[tool.semantic_release]` (version_toml, `v{version}`, changelog defaults, non-releasing `chore(release)` commit_message, uv.lock-only `build_command`, `upload_to_vcs_release = false`), `.github/workflows/release.yaml` (push→main + workflow_dispatch dry-run/`--noop`, PAT checkout + `GH_TOKEN`, `git checkout -B ${{ github.ref_name }}` then `git reset --hard`, cancel-in-progress false), `tests/test_release_workflow.py`, README one-liner after install step 3. Left human PAT/`SEMANTIC_RELEASE_TOKEN` and deferred-work “done” mark for after merge/verify. Invokes `semantic-release version` (creates VCS Release); not `publish` (asset upload path). Offline verify: pytest release/CC/dual-layout + ruff clean.
- 2026-10-03 agent: Extended `tests/test_release_workflow.py` with one offline test per frozen I/O matrix row (releasing / non-releasing / PAT re-trigger / missing secret / already-released tip). No live Actions/secrets; already-released tip asserts tag↔version via `--print-last-released*` plus `version` invocation as the no-op path.

## Plan Change Log

- 2026-10-03 plan review (pre-approve): checkout must use PAT `token:` + `GH_TOKEN` (not env-only / not GITHUB_TOKEN-or); soften partial-publish AC to fail-closed + recovery; add PAT re-trigger no-op edge case and non-releasing write-back subject; add `git reset --hard ${{ github.sha }}` + non-canceling concurrency; forbid `uv build` in `build_command` and lock it in tests; thicken human PAT checklist (scopes + bypass `actor_id` 22600261). Avoids protected-branch push failures, false “atomic publish” promises, surprise second bumps, tip races, and wheel/asset footguns.

## Review Triage Log

- 2026-10-03 quick pass — verdicts: 2 high (patch)
  - high → patch | `pyproject.toml` `[tool.semantic_release]` missing `allow_zero_version = true` | PSR v10 default `allow_zero_version=false` maps patch/minor/major from `0.1.0` all to `1.0.0`, violating frozen feat→minor / fix→patch against baseline `v0.1.0`. Evidence: `_increment_version` with defaults.
  - high → patch | `tests/test_release_workflow.py` `test_matrix_already_released_tip_*` requires local `v0.1.0` tag + PSR last-released stdout | CI `ci.yaml` uses default shallow checkout (no `fetch-tags` / `fetch-depth: 0`); tag absent → assert / IndexError; offline AC fails in Actions. Leave `ci.yaml` unchanged per plan; fix the test.

## Design Notes

**Why PAT + bypass user:** Ruleset `branch-protection` blocks ordinary `GITHUB_TOKEN` write-back to `main`. Forge/deferred locked a PAT for the *existing* bypass actor as a repo secret — not a new App.

**Why runner + uv, not PSR Docker Action:** Lock sync needs `uv`; existing CI already uses `setup-uv`. Pin PSR through the project/tool env and invoke with `uv run`/`uvx`.

**Why PAT re-trigger is OK:** Unlike `GITHUB_TOKEN`, a PAT push re-fires `push`→`main`. That second run must no-op because the write-back commit is non-releasing and the tip is already tagged.

**Branch:** Implementation continues on current branch `ci/conventional-commits-gate` per human choice (CC gate may land in the same lineage). Do not push release commits to `main` from the agent; open/update a PR.

**Golden `build_command` shape** (adapt to pinned PSR docs; do **not** append `uv build`):

```toml
build_command = """
uv lock --upgrade-package \"$PACKAGE_NAME\"
git add uv.lock
"""
```

## Verification

**Commands:**
- `uv run pytest tests/test_release_workflow.py tests/test_conventional_commits.py tests/test_dual_layout.py` -- shape + packaging/CC green
- `uv run ruff check apps tests` -- still clean

**Manual checks:**
- Repo secret `SEMANTIC_RELEASE_TOKEN` present; PAT owner is bypass `actor_id` `22600261` on ruleset `24390720`
- After merge to `main` (or dry-run): Actions log shows PSR; on a releasing change, `gh release list` / `git ls-remote --tags` show the new `v*` Release; follow-up bot-push run no-ops
