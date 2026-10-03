# Walkthrough: HACS release train (PR #15)

Target: [PR #15](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/15) · branch `ci/conventional-commits-gate` · commit `a1a5e05`

**Current block:** Slice: PSR config (in progress)

## Blocks

- [x] **Intent** — done
- [x] **Broad strokes** — done
- [ ] **Slice: PSR config** — in progress
- [ ] **Slice: Release workflow + auth**
- [ ] **Slice: Offline matrix tests**
- [ ] **Periphery**

### Intent

Source: frozen Intent from [plan-hacs-release-automation.md](../plan-hacs-release-automation.md) (verbatim).

**Problem:** HACS install/update needs published GitHub Releases, but after the manual `v0.1.0` cut there is no CI train — version, changelog, tag, and Release can drift or be forgotten on every merge to `main`.

**Approach:** Add python-semantic-release on `push` to `main`: bump `pyproject.toml` from Conventional Commits, write back `CHANGELOG.md` + `uv.lock`, tag `v{version}`, and publish a GitHub Release with no assets, authenticated by a dedicated PAT for the existing branch-protection bypass user.

**Review notes**

- Human must create secret `SEMANTIC_RELEASE_TOKEN` (bypass actor_id 22600261) before/at merge.
- `allow_zero_version = true` is required so 0.x keeps feat→minor / fix→patch.

### Broad strokes

python-semantic-release train on `main`: config, workflow + PAT auth, offline matrix tests, README install note.

1. [`pyproject.toml`](../../pyproject.toml) — `[tool.semantic_release]` + `python-semantic-release` pin
2. [`.github/workflows/release.yaml`](../../.github/workflows/release.yaml) — push→`main` train
3. [`tests/test_release_workflow.py`](../../tests/test_release_workflow.py) — shape + matrix
4. [`README.md`](../../README.md) — install-path one-liner

### Slice: PSR config

Mechanism: `version_toml`, tag format `v{version}`, `allow_zero_version`, `chore(release)` `commit_message`, `uv.lock`-only `build_command` (no `uv build`), `upload_to_vcs_release` false, `GH_TOKEN` remote.

- [`pyproject.toml`](../../pyproject.toml) — `python-semantic-release>=10,<11` in `dev`; `[tool.semantic_release]` (`version_toml`, `tag_format`, `allow_zero_version`, `commit_message`, `build_command`)
- [`pyproject.toml`](../../pyproject.toml) — `[tool.semantic_release.remote]` (`token` ← `GH_TOKEN`) and `[tool.semantic_release.publish]` (`upload_to_vcs_release = false`)

### Slice: Release workflow + auth

Mechanism: PAT on checkout + `GH_TOKEN`, tip reset, `cancel-in-progress: false`, `semantic-release version` (noop on `workflow_dispatch`).

- [`.github/workflows/release.yaml`](../../.github/workflows/release.yaml) — `push`/`workflow_dispatch`, concurrency, `SEMANTIC_RELEASE_TOKEN` on checkout + `GH_TOKEN`, `git reset --hard`, `uv sync --frozen --group dev`, noop vs live `version`

### Slice: Offline matrix tests

Mechanism: one test per I/O matrix row + shape guards; CI-safe (no local tag dependency).

- [`tests/test_release_workflow.py`](../../tests/test_release_workflow.py) — matrix rows (releasing / non-releasing / PAT re-trigger / missing secret / already released) + workflow/config shape locks

### Periphery

- [`plan-hacs-release-automation.md`](../plan-hacs-release-automation.md) — build plan (`status: built`)
- [`deferred-work.md`](../deferred-work.md) — PSR entry still open until merge+verify
- [`README.md`](../../README.md) — install step 3 note (automated Releases after merge)
- Human secret `SEMANTIC_RELEASE_TOKEN` (bypass actor_id `22600261`) — create before/at merge
