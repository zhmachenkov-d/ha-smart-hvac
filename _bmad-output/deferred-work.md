# Deferred work

- source_plan: `/workspaces/ha-smart-hvac/_bmad-output/plan-hacs-packaging.md`
  summary: Add HACS publish knobs — root `hacs.json`, HACS Action workflow (`category: appdaemon`), and release/custom-repo publish checklist automation.
  evidence: Split from dual-layout + history-hygiene (public-readiness prep) plan to keep that plan honest about scope; land layout, GitHub-served history hygiene, and concrete Production/stranger `app_dir` examples first.
  status: done (2026-10-03) — Phase A merged via PR #11 (`hacs.json`, Validate, install-first README, `0.1.0`); Phase B published Release `v0.1.0` on `main`. Remaining outside this entry: GitHub description/topics still empty (`gh repo edit` 403 — PAT lacks Administration); Validate may stay red until description/topics + a license exist.

- source_plan: `/workspaces/ha-smart-hvac/_bmad-output/plan-conventional-commits-gate.md`
  summary: Automate HACS releases with python-semantic-release on push to `main` (version + CHANGELOG + `uv.lock` write-back, `v*` tag, GitHub Release, no assets).
  evidence: Split from dual Conventional Commits PR gate so the gate can ship as its own PR; PSR train follows once CC enforcement is live. Locked auth for later: fine-grained/classic PAT for the existing `branch-protection` bypass user as repo secret (not bare `GITHUB_TOKEN`; not a new GitHub App).

- source_plan: `/workspaces/ha-smart-hvac/_bmad-output/plan-conventional-commits-gate.md`
  summary: After merging the Conventional Commits workflow, expect unrelated open PRs without that workflow file to stay pending on required checks `pr-title`/`pr-commits` until they rebase onto `main` (or the workflow lands).
  evidence: Ruleset required checks were enabled before the workflow existed on `main`; same-repo PR that introduces the workflow still runs it from the head ref, but other branches without the file cannot emit those check names.

