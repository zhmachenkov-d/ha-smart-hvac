---
title: 'Dual layout + history hygiene (public-readiness prep)'
type: 'feature'
ticket: ''
created: '2026-10-02'
status: 'in-progress'
baseline_revision: '0f085e4d8ce25385b4691bada0fd4d7274dc1dcf'
route: 'full'
route_source: 'auto'
review: ''
review_source: ''
lenses_ran: []
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/forge-hacs-packaging-meaning/forge-hacs-packaging-meaning.md'
  - '{project-root}/_bmad-output/research-hacs-appdaemon-feasibility-for-ha-smart/research-hacs-appdaemon-feasibility-for-ha-smart.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The monorepo nests AppDaemon apps under `appdaemon/apps/hvac/` and tracks house entity IDs in `apps.yaml`, so it cannot become a public GitHub repository (and later a HACS-shaped custom repo) without a layout change and history hygiene.

**Approach:** Dual layout in this repo — canonical Python at `apps/hvac/`, Exclusive Session via `app_dir: ../apps` (no symlink), gitignore real `apps/apps.yaml` + commit placeholders example — then rewrite **every ref GitHub will serve when the repo is public** so live house wiring is absent from reachable history, and document the public flip plus concrete Production add-on vs HACS `app_dir` examples. This plan is **public-readiness prep**, not HACS publish: `hacs.json`, HACS Action, and release automation stay deferred.

## Boundaries & Constraints

**Always:**
- One monorepo; Exclusive Session and HACS-shaped layout from the same tree.
- Canonical package: `apps/hvac/`; keep `module: hvac` / `class: HvacApp` and `from hvac…` imports.
- Config stays under `appdaemon/`; relative `app_dir` resolves against `config_dir` → use `app_dir: ../apps`.
- Gitignore `apps/apps.yaml`; commit `apps/apps.yaml.example` with placeholders only; preserve the local house wiring file when untracking.
- Ask before changing house entity ID *values* in local wiring.
- Execute history rewrite/filter so live house `apps.yaml` content is absent from **all refs that would be public** (`main`, other pushed branches, tags); document public-visibility flip steps after hygiene.
- README includes **concrete** `app_dir` examples for (a) Exclusive Session, (b) Production AppDaemon add-on path, (c) stranger HACS install path under HA config — call out add-on `addon_configs` vs HACS→`<config>/appdaemon/apps` mismatch.
- Work on `feat/hacs-packaging`; never push to `main` casually. History rewrite requires explicit human confirmation of the **exact** rewrite command and **force-push target list** before execution.

**Never:**
- Extract/mirror repo; symlink bridge; HACS façade over `appdaemon/apps/hvac/`.
- Claim this plan ships HACS packaging; adding `hacs.json` / HACS Action / release publish automation (deferred).
- Ship live house entity IDs in the tracked tree after the layout change.
- Silent force-push or rewrite without human go-ahead on the exact procedure.
- Branch-only hygiene that leaves dirty history on `main`/tags GitHub would serve after a public flip.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Exclusive Session | `./scripts/run-appdaemon` + local `apps/apps.yaml` | AD loads `hvac` from repo-root `apps/` via `app_dir: ../apps` | Missing wiring → document copy from example |
| Fresh clone | No local `apps/apps.yaml` | Example present; pytest/ruff pass | No invented house IDs |
| History after rewrite | Clone of rewritten **public-facing** refs | No historical blob with live house entity IDs from old `apps.yaml` on those refs | Abort rewrite if procedure unclear; human confirms force-push targets |
| Production add-on | House AD add-on config (often under `addon_configs/…`) | README shows concrete `app_dir` pointing at where **this** house keeps apps | Do not invent house entity IDs |
| Stranger HACS | HACS downloaded app into `<HA config>/appdaemon/apps/hvac/` | README shows concrete `app_dir` (e.g. `/config/appdaemon/apps` or HA-equivalent) when add-on default dir ≠ HACS path | Call out mismatch; link research issue pattern |

**Decisions (from planning gates + party review):**
- History hygiene + public flip: **execute rewrite** that cleans what GitHub will serve public; document public flip (option B, strengthened).
- Production/stranger: **concrete** add-on vs HACS `app_dir` examples in README (not a vague note).
- Scope honesty: **rename** — this is dual-layout + history hygiene / public-readiness prep; defer `hacs.json` + HACS Action + release publish automation to `_bmad-output/deferred-work.md`.

</frozen-after-approval>

## Code Map

- `appdaemon/apps/hvac/` → `apps/hvac/` — move package intact; reuse all `from hvac…` imports.
- `appdaemon/apps/apps.yaml` → local `apps/apps.yaml` (gitignored) + `apps/apps.yaml.example` (placeholders).
- `appdaemon/appdaemon.yaml` — add `app_dir: ../apps`.
- `scripts/run-appdaemon` — keep `-c appdaemon/`; secrets under `appdaemon/`.
- `pyproject.toml`, `.github/workflows/ci.yaml`, `.pre-commit-config.yaml`, `README.md` — pytest/ruff paths → `apps`.
- `AGENTS.md` — paths + entity-ID ask rule → `apps/apps.yaml`.
- `.gitignore` — `apps/apps.yaml`; keep `_bmad/render/`.
- `README.md` — Exclusive Session dual layout; **worked** Production add-on vs HACS `app_dir` examples; public-flip notes after hygiene.
- History — filter/remove historical house `apps.yaml` (paths: `appdaemon/apps/apps.yaml` and/or `apps/apps.yaml`); force-push **named public-facing refs** after human confirms procedure.
- Do not touch: algorithm modules' logic, ADRs' Exclusive Session policy intent, deferred HACS Action/`hacs.json`.

## Tasks & Acceptance

**Execution:**
- [x] `apps/hvac/` -- `git mv` from `appdaemon/apps/hvac/`; clear empty `appdaemon/apps/` nest -- HACS-canonical package path
- [x] `apps/apps.yaml` + `apps/apps.yaml.example` + `.gitignore` -- untrack house file (keep working copy); commit placeholders -- no live IDs in tree
- [x] `appdaemon/appdaemon.yaml` -- `app_dir: ../apps` -- Exclusive Session without symlink
- [x] `pyproject.toml`, CI, pre-commit, `README.md` -- retarget pytest/ruff to `apps` -- tooling follows move
- [x] `AGENTS.md` -- update package/wiring paths -- agent policy matches layout
- [x] `README.md` -- Exclusive Session + **concrete** Production add-on vs HACS `app_dir` examples -- ops docs
- [ ] History rewrite -- draft exact filter command + force-push target list (`main`, other remote branches/tags that would be public); human confirms; execute; verify; document public flip -- hygiene gate for GitHub-served history

**Acceptance Criteria:**
- Given `app_dir: ../apps` and local wiring, when Exclusive Session starts with `-c appdaemon/`, then AppDaemon uses repo-root `apps/` with no symlink under `appdaemon/apps`.
- Given a clean tree, when `uv run pytest` and ruff run against `apps` + `tests`, then both succeed.
- Given the git index after layout tasks, when inspecting tracked `apps/` files, then only placeholder entity IDs appear (no live house IDs).
- Given history rewrite completed and force-pushed to agreed refs, when searching those refs' reachable history for former live `apps.yaml` entity IDs, then they are absent.
- Given README after this plan, when a Production operator and a stranger HACS installer each follow the matching `app_dir` example, then add-on config path vs `<HA config>/appdaemon/apps` mismatch is explicit and actionable.
- Given plan/README language, when a reader skims the title and intent, then they understand this is public-readiness prep — not a claim that HACS install works yet.

## Implementation Notes

### History rewrite — draft for human confirmation (DO NOT RUN until confirmed)

**Survey (2026-10-03):** Remote refs that would be public today: `origin/main` only. No tags. `feat/hacs-packaging` is local-only until pushed. Historical live wiring path: `appdaemon/apps/apps.yaml` (present in commits from bootstrap through current `main`).

**Prerequisites:** layout commit(s) landed on `feat/hacs-packaging` (and ideally merged or applied so the rewrite base includes the dual layout). Install `git-filter-repo` if missing.

**Exact filter command (proposed):**

```bash
# From repo root, on a clean working tree after layout commits.
# Rewrites ALL local refs; backup remote is strongly recommended first.
git filter-repo \
  --path appdaemon/apps/apps.yaml \
  --path apps/apps.yaml \
  --invert-paths \
  --force
```

**Force-push target list (proposed):**

| Ref | Why |
|-----|-----|
| `main` | Default branch GitHub serves; contains historical live `apps.yaml` |
| (none other today) | No remote feature branches or tags at survey time — re-check `git ls-remote --heads --tags origin` immediately before push |

```bash
# Only after human confirms THIS command + target list in chat/PR:
git push --force-with-lease origin main
# If feat/hacs-packaging (or other branches) were pushed before rewrite, force-push those too
# after re-applying/rebasing onto rewritten history — do not leave dirty history on any public ref.
```

**Verify (expect zero hits on filtered paths):**

```bash
git log -S'sensor.indoor_outdoor_meter_794a' --all -- appdaemon/apps/apps.yaml apps/apps.yaml
git rev-list --all | git grep -h 'sensor.indoor_outdoor_meter_794a' --and -- '**/apps.yaml' || true
# Also spot-check another known live ID, e.g. switch.opentherm_bridge_ch_enabled
```

**Public flip (human, after verify):** GitHub → Settings → Change repository visibility → Public. Do not flip before force-push verification passes. HACS publish (`hacs.json`, Action, releases) remains deferred — see `_bmad-output/deferred-work.md`.

## Plan Change Log

- 2026-10-03 party review: renamed scope to dual layout + history hygiene (public-readiness prep); README requires concrete add-on vs HACS `app_dir` examples; history rewrite must clean refs GitHub will serve public (not branch-only).
- 2026-10-03 implement: dual layout + tooling/docs landed on `feat/hacs-packaging`; history rewrite drafted above — awaiting human confirm of exact command + force-push targets before execute.

## Review Triage Log

## Design Notes

AppDaemon 4.5.13 resolves relative `app_dir` against `config_dir`. With `-c appdaemon/`, `app_dir: ../apps` → `<repo>/apps`.

**README `app_dir` examples (minimum content):**
1. **Exclusive Session (this repo):** `app_dir: ../apps` under `appdaemon/appdaemon.yaml` with `-c appdaemon/`.
2. **Production AppDaemon add-on (house):** show that add-on config often lives under `addon_configs/…` and `app_dir` must point at wherever *this* deployment keeps apps (document the house’s actual pattern without leaking entity IDs).
3. **Stranger HACS install:** HACS drops the app into `<HA config>/appdaemon/apps/hvac/`; if the add-on default app directory is `addon_configs/…` instead, set `app_dir` to the HA config apps path (e.g. `/config/appdaemon/apps` or the HA-equivalent path on that install) so AD loads the HACS download. Cite the known mismatch pattern (add-on v0.15+ vs HACS path).

**History rewrite procedure (explicit; execute only after human confirms the pasted command + targets):**
1. After layout commit(s) on `feat/hacs-packaging`, identify paths that ever held live wiring: `appdaemon/apps/apps.yaml`, `apps/apps.yaml`.
2. Draft a filter (e.g. `git filter-repo` path removal or equivalent) that strips those blobs from history.
3. List **force-push targets**: at minimum `main` plus any other remote branches/tags that would be visible after a public flip (agree the list with human — typically all refs that currently contain the dirty file).
4. Human confirms the exact command string and target list in chat/PR.
5. Execute rewrite locally; verify with agreed search (e.g. `git log -S'<known-entity-id>' --all` / `git rev-list --all | git grep` against known live IDs) — expect zero hits on filtered paths.
6. Force-push only the confirmed targets; document that a public-visibility change must not happen until verification passes on those refs.
7. Public flip itself remains a separate human action after hygiene — documented steps, not automated in this plan.

## Verification

**Commands:**
- `uv run pytest` -- expected: pass with `pythonpath = ["apps"]`
- `uv run ruff check apps tests && uv run ruff format --check apps tests` -- expected: clean
- History search after rewrite on force-pushed refs (exact command agreed with human) -- expected: no live house entity ID hits in historical `apps.yaml`

**Manual checks:**
- Local `apps/apps.yaml` still present after untrack; example is placeholders only.
- No `appdaemon/apps/hvac/` leftover; no symlink bridge.
- README shows three concrete `app_dir` examples (Exclusive Session, Production add-on, stranger HACS).
- Plan title/intent do not claim HACS packaging is complete.
