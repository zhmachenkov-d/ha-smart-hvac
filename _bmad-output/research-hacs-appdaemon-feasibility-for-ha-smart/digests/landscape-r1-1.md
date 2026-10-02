# Digest: landscape & maturity — round 1

**Questions:** Does HACS support AppDaemon apps as a first-class category? How mature/active is that path vs integrations? Is packaging as HACS AppDaemon the natural fit vs rewriting as a HA custom integration?

## Findings (claims)

1. {claim: "HACS documents a dedicated AppDaemon Apps publish category with explicit repository structure rules and points to ludeeus/ad-hacs as the reference template.", source: "https://www.hacs.xyz/docs/publish/appdaemon/", publisher: "HACS (hacs.xyz)", pub_date: "accessed-live-docs", accessed: "2026-10-02", confidence: high, class: landscape}
2. {claim: "AppDaemon discovery is not enabled by default in HACS because AppDaemon apps are used only by a small subset of users; users must enable 'AppDaemon apps discovery & tracking'.", source: "https://www.hacs.xyz/docs/use/repositories/type/appdaemon/", publisher: "HACS (hacs.xyz)", pub_date: "accessed-live-docs", accessed: "2026-10-02", confidence: high, class: landscape}
3. {claim: "hacs/default lists 56 default AppDaemon repositories as of raw master/appdaemon fetch.", source: "https://raw.githubusercontent.com/hacs/default/master/appdaemon", publisher: "hacs/default (GitHub)", pub_date: "2026-10-02-fetch", accessed: "2026-10-02", confidence: high, class: ecosystem-signal}
4. {claim: "HACS Action supports category value appdaemon alongside integration, plugin, template, theme, python_script.", source: "https://www.hacs.xyz/docs/publish/action/", publisher: "HACS (hacs.xyz)", pub_date: "accessed-live-docs", accessed: "2026-10-02", confidence: high, class: version/compatibility}
5. {claim: "Mature peer example xaviml/controllerx remains an active AppDaemon HACS default (374 stars; pushed_at 2026-09-28; structure apps/ + hacs.json + tests/docs).", source: "https://api.github.com/repos/xaviml/controllerx", publisher: "GitHub API / xaviml/controllerx", pub_date: "2026-09-28", accessed: "2026-10-02", confidence: high, class: ecosystem-signal}

## Leads
- Operational path mismatch between HACS download dir and AppDaemon add-on default apps dir (issue #4442) → implementation dimension.
- Default-list backlog months; AppDaemon-specific additions appear rare vs integrations.

## Not found
- No HACS docs recommending rewriting AppDaemon apps as core custom_components for store distribution; AppDaemon remains a supported category.
