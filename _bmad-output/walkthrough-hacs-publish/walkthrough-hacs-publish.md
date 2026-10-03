# Walkthrough: HACS custom-repo publish knobs (PR #11)

Target: [PR #11](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/11) · branch `feat/hacs-publish`

**Current block:** Wrap-up (done — PR #11 merged; Release v0.1.0 published; description/topics blocked by PAT)

## Blocks

- [x] **Intent** — done
- [x] **Broad strokes** — done
- [x] **Slice: HACS manifest + Validate** — done
- [x] **Slice: install-first README** — done
- [x] **Slice: version + packaging tests** — done
- [x] **Periphery** — done

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

**Review notes**

- Validate CI still red on license/description/topics; `hacsjson` OK; accepted as Phase B + license gap.

### Slice: install-first README

Stranger path opens the README before dual-layout/dev material. HACS download only gets `hvac/`, so wiring instructions differ from Exclusive Session.

- [`README.md`](../../README.md) — section **Install with HACS (custom repository)** leads after title/badge; custom-repo steps; `app_dir` for add-on vs HACS path; raw link to [`apps/apps.yaml.example`](../../apps/apps.yaml.example) for wiring beside downloaded `hvac/`.
- Exclusive Session later uses in-repo `cp apps/apps.yaml.example apps/apps.yaml`.
- Production / stranger `app_dir` examples kept under later `app_dir` section.

### Slice: version + packaging tests

Version bump aligns metadata with the planned first release tag; packaging tests lock HACS knobs and install-first docs.

- [`pyproject.toml`](../../pyproject.toml) — `version = "0.1.0"` (uv.lock synced).
- [`tests/test_dual_layout.py`](../../tests/test_dual_layout.py) — `test_hacs_json_name`, `test_validate_workflow_hacs_appdaemon`, `test_readme_install_first_before_exclusive_session`; dropped `public-readiness` assert.

### Periphery

- [plan-hacs-publish.md](../plan-hacs-publish.md) — Phase A/B plan artifact (status built).
- [uv.lock](../../uv.lock) — lockfile synced with pyproject version 0.1.0.
- [party-mode memlog](../party-mode/memories/installed/.memlog.md) — party greenlight note for install-first README.
- This narrative and [walkthrough-hacs-publish-log.md](./walkthrough-hacs-publish-log.md) track Phase A acceptance for PR #11.
