---
title: HACS packaging meaning for ha-smart-hvac
status: hardened
created: 2026-10-02
---

# HACS packaging meaning

## Locked

- Same monorepo dual layout — Exclusive Session and HACS from one tree (not extract/mirror).
- Canonical Python: repo-root `apps/hvac/` (HACS-native); Exclusive Session adapts.
- Exclusive Session: `appdaemon -c appdaemon/` + `app_dir` → repo-root `apps/` (not symlink).
- Config stays under `appdaemon/` (`appdaemon.yaml`, secrets from `.env`).
- House wiring: gitignore real `apps/apps.yaml`; commit `apps.yaml.example` only.
- Publish surface in scope: `hacs.json`, HACS Action (`category: appdaemon`), GitHub releases, stranger `app_dir` docs.
- Publish vehicle: this repo, made public.
- Public flip gated on history hygiene (rewrite/filter house wiring out of history) — gitignore alone insufficient.
- Ceiling: public custom repository only.

## Rejected

- Extract / packaging mirror repo — keep one tree.
- Canonical under `appdaemon/apps/hvac/` with HACS façade — wrong direction of adaptation.
- Symlink bridge — chose `app_dir` instead.
- Layout-only “packaging” — publish knobs included.
- Accept past house IDs in public history — hygiene required first.
- `hacs/default` inclusion — out of scope.

## Why (load-bearing)

- HACS installs repo-root `apps/<name>/`; current `appdaemon/apps/` nesting does not match.
- AppDaemon loads `apps.yaml` from `app_dir` — under `app_dir`→`apps/`, house file shares that tree → must be example + gitignore, not live IDs.
- Repo is private today; HACS custom repos need public GitHub — visibility change is part of the meaning, gated on history.
