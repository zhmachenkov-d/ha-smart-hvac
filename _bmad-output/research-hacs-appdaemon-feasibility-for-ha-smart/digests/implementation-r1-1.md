# Digest: implementation reality — round 1

**Questions:** What operational burdens and packaging frictions do AppDaemon HACS publishers/users hit? What would a house-specific HVAC AppDaemon need to change to ship?

## Findings (claims)

1. {claim: "HACS downloads AppDaemon apps to HA config appdaemon/apps/, but AppDaemon add-on v0.15+ defaulted apps to addon_configs/.../apps; HACS maintainers state HACS cannot write addon_configs — users must point app_dir back to /homeassistant/appdaemon/apps (or equivalent).", source: "https://github.com/hacs/integration/issues/4442", publisher: "hacs/integration GitHub issue", pub_date: "issue-thread", accessed: "2026-10-02", confidence: high, class: operational}
2. {claim: "Official template and peer climate/HVAC-adjacent AppDaemon HACS repos (ludeeus/ad-hacs, kprestel/appdaemon-climate, Pythm/ad-ClimateCommander, xaviml/controllerx) all expose apps/ at repository root, not nested under an appdaemon/ config tree.", source: "GitHub contents API for those repos", publisher: "GitHub / respective owners", pub_date: "2026-10-02-fetch", accessed: "2026-10-02", confidence: high, class: pattern}
3. {claim: "ControllerX demonstrates a full-featured AppDaemon HACS package can coexist with tests, docs, poetry/pyproject, and CI while keeping apps/ at root for HACS.", source: "https://api.github.com/repos/xaviml/controllerx/contents/", publisher: "GitHub API / xaviml/controllerx", pub_date: "2026-10-02-fetch", accessed: "2026-10-02", confidence: high, class: pattern}
4. {claim: "HACS Action category appdaemon validates with the same checker HACS uses; ignorable checks include hacsjson, description, topics, issues, information.", source: "https://www.hacs.xyz/docs/publish/action/", publisher: "HACS (hacs.xyz)", pub_date: "accessed-live-docs", accessed: "2026-10-02", confidence: high, class: version/compatibility}

## Project-gap notes (decision framing — not evidence)
Observed locally for ha-smart-hvac (lead inspection, not a web claim): code lives at `appdaemon/apps/hvac/` (nested under AppDaemon config dir); no `hacs.json`; `apps.yaml` embeds house entity IDs; secrets via `.env` → regenerated `secrets.yaml`. These are packaging blockers relative to claims 1–3 above.

## Leads
- Two packaging strategies: reshape monorepo to ROOT/apps/hvac (like ControllerX) vs publish a slim packaging repo/subtree.

## Not found
- No documented HACS path that installs nested `appdaemon/apps/` trees without restructuring.
