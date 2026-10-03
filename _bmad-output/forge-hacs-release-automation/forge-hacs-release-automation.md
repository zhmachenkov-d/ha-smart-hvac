---
title: Automate HACS releases for ha-smart-hvac
status: hardened
created: 2026-10-03
---

# Automate HACS releases

## Locked

- Ceiling unchanged: public HACS **custom repository** only; need published GitHub Releases (not tags alone).
- Release train: **python-semantic-release** on merge/`push` to `main` — version + changelog + GitHub Release (semantic-release family, not release-please).
- Version source: `pyproject.toml`; bump policy = Conventional Commits / PSR defaults (`feat`→minor, `fix`→patch, breaking→major; `docs`/`ci`/`chore` no release).
- Write-back to `main`: bot commits `pyproject.toml` + `CHANGELOG.md`, then tag `v{version}` + GitHub Release (no binary assets).
- Auth: dedicated token in repo secrets (ruleset `branch-protection` present; do not rely on `GITHUB_TOKEN` alone).
- CI-gate Conventional Commits on **both** PR title and PR commits (skill alone insufficient).
- Baseline already exists: `v0.1.0`; keep `v` tag prefix.

## Rejected

- Release-please (Release PR) model — chose CI publish after merge to `main`.
- JS `semantic-release` — avoid Node-only toolchain; stack is Python/uv.
- Version-only / agent checklist without Release CI — full train chosen.
- Rare/manual release signal beyond Conventional Commits.
- Second version calculator (e.g. commitizen as parallel source of truth) — PSR only.
- Binary release assets — HACS uses repo tree at the Release/tag.
- Prior `plan-hacs-publish` Never (no tag→Release CI; agent-only `gh release create` as sole path) — superseded for future releases (`v0.1.0` already cut manually).

## Why (load-bearing)

- HACS install/update path depends on published Releases; automating only the version number leaves the publish step as the failure mode.
- PRs-only for human code stays; bot write-back is the explicit exception so file version and tag cannot drift.
- Dual CC gate covers both current merge-commit history and a future squash policy.
