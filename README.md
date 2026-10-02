# ha-smart-hvac

[![CI](https://github.com/zhmachenkov-d/ha-smart-hvac/actions/workflows/ci.yaml/badge.svg)](https://github.com/zhmachenkov-d/ha-smart-hvac/actions/workflows/ci.yaml)

AppDaemon Apps that control multi-zone OpenTherm HVAC through Home Assistant.

This repository uses a **dual layout** for public-readiness prep (not a finished HACS publish): canonical Python lives at repo-root `apps/hvac/`; Exclusive Session config stays under `appdaemon/` and points at that tree via `app_dir`. HACS knobs (`hacs.json`, HACS Action, release automation) are deferred.

## Layout

| Path | Role |
|------|------|
| `apps/hvac/` | HVAC App package (`module: hvac`, `class: HvacApp`) |
| `apps/apps.yaml` | Local house entity wiring (**gitignored** — copy from example) |
| `apps/apps.yaml.example` | Placeholder entity IDs only |
| `appdaemon/` | Exclusive Session AppDaemon config (`appdaemon.yaml`, secrets) |

Fresh clone without wiring:

```bash
cp apps/apps.yaml.example apps/apps.yaml
# then replace YOUR_* placeholders with your house entity IDs
```

## Dev Container (Exclusive Session)

1. Copy env and fill HA credentials (plus optional `GH_TOKEN` on the **host** for `gh`):

   ```bash
   cp .env.example .env
   ```

2. Open the folder in a Dev Container (**Dev Containers: Reopen in Container**).
   Python 3.12 and dependencies install via `uv sync --group dev` in `postCreateCommand`.

3. Ensure local wiring exists (`apps/apps.yaml` — see above).

4. **Exclusive Session:** stop or disable the Production AppDaemon add-on in Home Assistant.

5. Start AppDaemon:

   ```bash
   ./scripts/run-appdaemon
   ```

   The script regenerates `appdaemon/secrets.yaml` from `.env`, then runs
   `appdaemon -c appdaemon/`. With `app_dir: ../apps` in `appdaemon/appdaemon.yaml`,
   AppDaemon loads the package from repo-root `apps/` (no symlink under `appdaemon/apps`).

6. When finished: stop AppDaemon (Ctrl+C), then start the Production Add-on again.

`HA_URL` must be a LAN address reachable from inside the container (not
`localhost` unless HA shares that network namespace).

Location fields in `appdaemon/appdaemon.yaml` are placeholders (`UTC` / `0,0`);
set them before relying on time or sun helpers.

## `app_dir` examples

AppDaemon resolves a relative `app_dir` against its config directory. Absolute paths are common on HAOS.

### 1. Exclusive Session (this repo)

In `appdaemon/appdaemon.yaml`, with `./scripts/run-appdaemon` → `appdaemon -c appdaemon/`:

```yaml
appdaemon:
  app_dir: ../apps
```

That resolves to `<repo>/apps`, where `hvac/` and your local `apps.yaml` live.

### 2. Production AppDaemon add-on (this house)

Per the [AppDaemon add-on Paths](https://appdaemon.readthedocs.io/en/latest/ADDON.html#paths) table, add-on config is `/config` inside the container (Samba/host: `addon_configs/a0d7b954_appdaemon`). AppDaemon’s default apps directory is `./apps` under that config — i.e. `/config/apps` in the container. You can omit `app_dir` or set it explicitly; keep house wiring on the HA host only (not in this git tree).

```yaml
appdaemon:
  # Explicit form of the add-on default (./apps under /config)
  app_dir: /config/apps
```


### 3. Stranger HACS install (after a future public custom-repo publish)

HACS downloads AppDaemon apps into the HA configuration directory under `appdaemon/apps/` (e.g. `/config/appdaemon/apps/hvac/` on many HAOS installs). After AppDaemon add-on v0.15+, the add-on’s **default** app directory often sits under `addon_configs/…` instead — HACS cannot write there ([hacs/integration#4442](https://github.com/hacs/integration/issues/4442)). If those paths differ, set the add-on’s `app_dir` to the HACS download path so AppDaemon loads the installed package:

```yaml
appdaemon:
  # HAOS / Supervised typical HA config mount; adjust if your install differs
  app_dir: /config/appdaemon/apps
```

Then add your own `apps.yaml` next to the downloaded `hvac/` package (placeholders from `apps/apps.yaml.example` in this repo). This layout prep does **not** yet ship `hacs.json` or claim HACS install works end-to-end.

## Public-visibility flip (after history hygiene)

Making the GitHub repository public is a **separate human action**. Do not flip visibility until:

1. Layout changes are on the agreed branch.
2. History rewrite has removed live house `apps.yaml` blobs from **every ref GitHub would serve** (`main`, other pushed branches, tags) — see the draft procedure in `_bmad-output/plan-hacs-packaging.md` (human must confirm the exact filter command and force-push target list before execution).
3. Verification search for known former live entity IDs on those refs returns no hits on historical `apps.yaml` paths.

Only then: GitHub → repository settings → change visibility to public (custom-repo HACS publish still needs deferred `hacs.json` / Action / releases work).

## Quality checks

```bash
uv sync --group dev        # install runtime + dev deps
uv run pytest              # run tests
uv run ruff check apps tests
uv run ruff format --check apps tests
pre-commit install         # optional: run hooks on commit
pre-commit run --all-files # run hooks manually
```
