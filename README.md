# ha-smart-hvac

AppDaemon HVAC Apps for Home Assistant (OpenTherm multi-zone control — Apps come later).

## Dev Container (milestone: HA connect)

1. Copy env and fill HA credentials (plus optional `GH_TOKEN` on the **host** for `gh`):

   ```bash
   cp .env.example .env
   ```

2. Open the folder in a Dev Container (**Dev Containers: Reopen in Container**).
   Python 3.12 and AppDaemon (`requirements.txt`) install via `postCreateCommand`.

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
