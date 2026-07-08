# ha-smart-hvac

[![CI](https://github.com/zhmachenkov-d/ha-smart-hvac/actions/workflows/ci.yaml/badge.svg)](https://github.com/zhmachenkov-d/ha-smart-hvac/actions/workflows/ci.yaml)

AppDaemon HVAC Apps for Home Assistant (OpenTherm multi-zone control — Apps come later).

## Dev Container (milestone: HA connect)

1. Copy env and fill HA credentials (plus optional `GH_TOKEN` on the **host** for `gh`):

   ```bash
   cp .env.example .env
   ```

2. Open the folder in a Dev Container (**Dev Containers: Reopen in Container**).
   Python 3.12 and dependencies install via `uv sync --group dev` in `postCreateCommand`.

3. **Exclusive Session:** stop or disable the Production AppDaemon add-on in Home Assistant.

4. Start AppDaemon:

   ```bash
   ./scripts/run-appdaemon
   ```

   The script regenerates `appdaemon/secrets.yaml` from `.env`, then runs
   `appdaemon -c appdaemon/`. Confirm in the logs that the HASS plugin
   connected. No Apps are registered yet.

5. When finished: stop AppDaemon (Ctrl+C), then start the Production Add-on again.

`HA_URL` must be a LAN address reachable from inside the container (not
`localhost` unless HA shares that network namespace).

Location fields in `appdaemon/appdaemon.yaml` are placeholders (`UTC` / `0,0`);
set them before relying on time or sun helpers.

## Quality checks

```bash
uv sync --group dev        # install runtime + dev deps
uv run pytest              # run tests
uv run ruff check appdaemon tests
uv run ruff format --check appdaemon tests
pre-commit install         # optional: run hooks on commit
pre-commit run --all-files # run hooks manually
```
