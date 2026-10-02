# Digest: integration & packaging — round 1

**Questions:** What exact structure/manifest/release rules must a HACS AppDaemon repo meet? What does HACS download? Custom repo vs default list?

## Findings (claims)

1. {claim: "Valid AppDaemon HACS repo must have exactly one directory under ROOT/apps/; all Python for that app under apps/APP_NAME/; if multiple app dirs exist only the first is managed.", source: "https://www.hacs.xyz/docs/publish/appdaemon/", publisher: "HACS (hacs.xyz)", pub_date: "accessed-live-docs", accessed: "2026-10-02", confidence: high, class: version/compatibility}
2. {claim: "OK layout is apps/awesome/awesome.py (+ README); layouts with app at repo root or without apps/ parent are Not OK.", source: "https://www.hacs.xyz/docs/publish/appdaemon/", publisher: "HACS (hacs.xyz)", pub_date: "accessed-live-docs", accessed: "2026-10-02", confidence: high, class: version/compatibility}
3. {claim: "General HACS publish requirements: public GitHub repo, description, topics, README, root hacs.json with at least name; releases preferred (tag alone insufficient — need published releases).", source: "https://www.hacs.xyz/docs/publish/start/", publisher: "HACS (hacs.xyz)", pub_date: "accessed-live-docs", accessed: "2026-10-02", confidence: high, class: version/compatibility}
4. {claim: "For AppDaemon installs, HACS downloads everything under the first directory in apps to <config_dir>/appdaemon/apps/*.", source: "https://manifest--hacs.netlify.app/faq/", publisher: "HACS FAQ (netlify mirror)", pub_date: "docs-mirror", accessed: "2026-10-02", confidence: high, class: version/compatibility}
5. {claim: "Current use docs also state AppDaemon apps download to Home Assistant configuration directory under appdaemon/apps/.", source: "https://www.hacs.xyz/docs/use/repositories/type/appdaemon/", publisher: "HACS (hacs.xyz)", pub_date: "accessed-live-docs", accessed: "2026-10-02", confidence: high, class: version/compatibility}
6. {claim: "Custom repositories can be added in HACS UI with type AppDaemon if structure matches; default inclusion requires PR to hacs/default ./appdaemon with passing HACS Action, a release, and owner/major-contributor status; review can take months.", source: "https://www.hacs.xyz/docs/faq/custom_repositories/ + https://www.hacs.xyz/docs/publish/include/", publisher: "HACS (hacs.xyz)", pub_date: "accessed-live-docs", accessed: "2026-10-02", confidence: high, class: landscape}
7. {claim: "Peer ClimateCommander ships root hacs.json {\"name\": \"Climate Commander\", \"country\": \"NO\"} plus apps/ layout.", source: "https://raw.githubusercontent.com/Pythm/ad-ClimateCommander/master/hacs.json", publisher: "Pythm/ad-ClimateCommander", pub_date: "repo-live", accessed: "2026-10-02", confidence: high, class: pattern}

## Leads
- Local monorepo using appdaemon/apps/ conflicts with ROOT/apps/ requirement.

## Not found
- No official requirement that apps.yaml be packaged inside the HACS download (config remains user-side).
