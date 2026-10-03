# Walkthrough: HACS custom-repo publish knobs (PR #11)

Target: [PR #11](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/11) · branch `feat/hacs-publish`

**Current block:** Slice: HACS manifest + Validate

## Blocks

- [x] **Intent** — done
- [x] **Broad strokes** — done
- [ ] **Slice: HACS manifest + Validate** — in progress (current)
- [ ] **Slice: install-first README** — unvisited
- [ ] **Slice: version + packaging tests** — unvisited
- [ ] **Periphery** — unvisited

### Intent

Source: frozen Intent from [plan-hacs-publish.md](../plan-hacs-publish.md) (verbatim).

**Problem:** Dual layout and public GitHub are done, but the repo still lacks HACS publish knobs (`hacs.json`, HACS Action, release/custom-repo guidance, GitHub metadata), so strangers cannot install via HACS custom repository.

**Approach:** Phase A on `feat/hacs-publish` (manifest, Validate workflow, README, tests, version bump, PR merge); Phase B after merge to `main` (set GitHub description/topics; agent publishes Release `v0.1.0` via `gh`). Ceiling remains public custom repository (not `hacs/default`).

**Review notes**

- This walkthrough covers Phase A in PR #11; Phase B (gh description/topics + Release v0.1.0) is after merge.
- Install-first README was required at party greenlight.

### Broad strokes

HACS custom-repo publish knobs: minimal manifest, CI validation, stranger install path in docs, version bump, tests lock packaging shape.

1. [`hacs.json`](../../hacs.json) — HACS name manifest.
2. [`.github/workflows/validate.yaml`](../../.github/workflows/validate.yaml) — HACS Action `category: appdaemon`.
3. [`README.md`](../../README.md) — install-first HACS custom-repo lead.
4. [`pyproject.toml`](../../pyproject.toml) — version `0.1.0`.
5. [`tests/test_dual_layout.py`](../../tests/test_dual_layout.py) — packaging asserts.

### Slice: HACS manifest + Validate

HACS needs a root name manifest and a Validate workflow that runs the same checks HACS uses. This PR adds both without folding them into the lint/test CI job.

- [`hacs.json`](../../hacs.json) — exactly `{"name": "ha-smart-hvac"}`.
- [`.github/workflows/validate.yaml`](../../.github/workflows/validate.yaml) — `actions/checkout@v4` then `hacs/action@main` with `category: appdaemon`; triggers push/PR/schedule/`workflow_dispatch`; no `ignore` flags.

### Slice: install-first README

*(filled when visited)*

### Slice: version + packaging tests

*(filled when visited)*

### Periphery

*(filled when visited)*
