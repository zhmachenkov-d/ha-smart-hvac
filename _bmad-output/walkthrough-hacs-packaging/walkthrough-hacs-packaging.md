# Walkthrough: dual-layout public-readiness (PR #8)

Target: [PR #9](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/9) · branch `feat/public-readiness-prep`

**Current block:** Broad strokes

## Blocks

- [x] **Intent** — done
- [ ] **Broad strokes** — in progress (current)
- [ ] **Slice: package move** — unvisited
- [ ] **Slice: wiring + gitignore** — unvisited
- [ ] **Slice: app_dir docs** — unvisited
- [ ] **Slice: tooling + layout tests** — unvisited
- [ ] **Periphery** — unvisited

### Intent

Source: frozen Intent from [`_bmad-output/plan-hacs-packaging.md`](../plan-hacs-packaging.md) (verbatim).

**Problem:** The monorepo nests AppDaemon apps under [`appdaemon/apps/hvac/`](../../appdaemon/apps/hvac/) and tracks house entity IDs in [`apps.yaml`](../../apps/apps.yaml), so it cannot become a public GitHub repository (and later a HACS-shaped custom repo) without a layout change and history hygiene.

**Approach:** Dual layout in this repo — canonical Python at [`apps/hvac/`](../../apps/hvac/), Exclusive Session via `app_dir: ../apps` (no symlink), gitignore real [`apps/apps.yaml`](../../apps/apps.yaml) + commit placeholders example — then rewrite **every ref GitHub will serve when the repo is public** so live house wiring is absent from reachable history, and document the public flip plus concrete Production add-on vs HACS `app_dir` examples. This plan is **public-readiness prep**, not HACS publish: [`hacs.json`](../../hacs.json), HACS Action, and release automation stay deferred.

**Review notes**

- History hygiene: treated as already done on rewritten `main` (out of PR #8 diff).
- Production `app_dir`: aligned with AppDaemon add-on docs (`/config/apps`; Samba `addon_configs/a0d7b954_appdaemon`).
- Branch renamed to `feat/public-readiness-prep` (was `feat/hacs-packaging`).

### Broad strokes

Dual layout: package at repo-root apps/, Exclusive Session config under appdaemon/ points there; house wiring stays local; tooling follows the move.

1. [`apps/hvac/`](../../apps/hvac/) — canonical HVAC App package (`module: hvac` / `from hvac…` unchanged).
2. [`appdaemon/appdaemon.yaml`](../../appdaemon/appdaemon.yaml) — `app_dir: ../apps` so Exclusive Session loads that tree (no symlink).
3. [`apps/apps.yaml.example`](../../apps/apps.yaml.example) + gitignore of [`apps/apps.yaml`](../../apps/apps.yaml) — placeholders only in git; live wiring local.
4. [`README.md`](../../README.md) (`app_dir` examples) — Exclusive Session / Production add-on / stranger HACS paths.
5. [`pyproject.toml`](../../pyproject.toml) (+ CI/pre-commit) — pytest/ruff `pythonpath`/`src` → `apps`.

### Slice: package move

*(filled when visited)*

### Slice: wiring + gitignore

*(filled when visited)*

### Slice: app_dir docs

*(filled when visited)*

### Slice: tooling + layout tests

*(filled when visited)*

### Periphery

*(filled when visited)*
