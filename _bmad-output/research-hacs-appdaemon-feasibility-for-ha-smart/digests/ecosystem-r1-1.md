# Digest: ecosystem health — round 1

**Questions:** Is the AppDaemon HACS category still maintained? Default-list vitality? Five-year regret risk of choosing AppDaemon HACS vs native integration?

## Findings (claims)

1. {claim: "hacs/default appdaemon list still exists and is maintained at least for removals (commit 2026-01-07 'Remove archived repository' touching appdaemon path).", source: "https://api.github.com/repos/hacs/default/commits?path=appdaemon&per_page=5", publisher: "GitHub API / hacs/default", pub_date: "2026-01-07", accessed: "2026-10-02", confidence: high, class: ecosystem-signal}
2. {claim: "Default AppDaemon catalog size is 56 repositories (master appdaemon JSON).", source: "https://raw.githubusercontent.com/hacs/default/master/appdaemon", publisher: "hacs/default", pub_date: "2026-10-02-fetch", accessed: "2026-10-02", confidence: high, class: ecosystem-signal}
3. {claim: "HACS docs explicitly frame AppDaemon as a small-subset category (discovery off by default).", source: "https://www.hacs.xyz/docs/use/repositories/type/appdaemon/", publisher: "HACS (hacs.xyz)", pub_date: "accessed-live-docs", accessed: "2026-10-02", confidence: high, class: landscape}
4. {claim: "Default-store inclusion review backlog is described as taking months despite daily new repositories.", source: "https://www.hacs.xyz/docs/publish/include/", publisher: "HACS (hacs.xyz)", pub_date: "accessed-live-docs", accessed: "2026-10-02", confidence: medium, class: ecosystem-signal}
5. {claim: "Recent GitHub search of hacs/default PRs mentioning appdaemon shows maintenance/removal activity and at least one draft AppDaemon add (m-zenker/kermi-ha-bridge, #7571, closed draft 2026-08-01) — far fewer AppDaemon adds than integration PRs in the same window.", source: "https://api.github.com/search/issues?q=repo:hacs/default+appdaemon+is:pr", publisher: "GitHub Search API", pub_date: "2026-10-02-fetch", accessed: "2026-10-02", confidence: medium, class: ecosystem-signal}
6. {claim: "Flagship AppDaemon default controllerx still shows active maintenance through 2026 (updated/pushed 2026).", source: "https://api.github.com/repos/xaviml/controllerx", publisher: "GitHub API", pub_date: "2026-09-28", accessed: "2026-10-02", confidence: high, class: ecosystem-signal}

## Leads
- None load-bearing beyond: custom-repo path avoids months-long default backlog.

## Not found
- No HACS announcement deprecating the AppDaemon category (as of docs accessed 2026-10-02).
- Exact count of AppDaemon default additions in 2025–2026 not fully enumerated beyond sparse PR search.
