---
title: 'technical research: HACS AppDaemon feasibility for ha-smart-hvac'
type: 'technical'
topic: 'HACS AppDaemon feasibility for ha-smart-hvac'
decision: 'Can ha-smart-hvac be packaged/distributed as a HACS AppDaemon extension, and what would that require?'
source: 'native-run'
status: complete
preset: 'standard-straightforward'
validation: 'normal'
created: '2026-10-02'
updated: '2026-10-02'
verified_claims: 6
unverified_claims: 2
---

# technical research: HACS AppDaemon feasibility for ha-smart-hvac

**Decision this research serves:** Can ha-smart-hvac be packaged/distributed as a HACS AppDaemon extension, and what would that require?

## Executive summary

**Yes — as a HACS AppDaemon app, not as a Home Assistant custom integration, and not with the repo layout as it stands today.**

HACS has a first-class AppDaemon category with clear publish rules [1][4]. The load-bearing gap is structural: HACS requires `apps/<name>/` at the **repository root** and downloads that package into `<config>/appdaemon/apps/` [1][5][6]. This project currently nests code under `appdaemon/apps/hvac/` (AppDaemon config tree), and ships house entity IDs in `apps.yaml` — both incompatible with a shareable HACS package without packaging work.

Practical path: reshape (or extract) so `apps/hvac/` sits at repo root, add `hacs.json`, document sample `apps.yaml` (no house IDs), validate with `hacs/action` `category: appdaemon`, then distribute first as a **custom repository**; default-store inclusion is optional and slow [8][9]. Biggest caveat: AppDaemon discovery is opt-in and niche [2], and users of the AppDaemon add-on may need `app_dir` pointed at the HACS download path [10].

## Landscape & maturity

HACS treats AppDaemon apps as a supported repository type with dedicated publish docs and an official sample (`ludeeus/ad-hacs`) [1][3]. The category is intentionally **not** on by default — HACS documents that AppDaemon users are a small subset and discovery must be enabled in HACS options [2].

That niche framing is real, but the path is not abandoned: `hacs/default` still ships an `appdaemon` list (56 entries) [7], the HACS Action accepts `category: appdaemon` [4], and mature defaults such as ControllerX remain actively maintained into 2026 [11]. Climate-adjacent AppDaemon defaults already exist (e.g. `kprestel/appdaemon-climate`, `Pythm/ad-ClimateCommander`) [7].

**Implication for the decision:** packaging this project as a **HACS AppDaemon app** matches what the project already is. Rewriting as a `custom_components/` integration would be a different product (HA lifecycle, config flow, no AppDaemon) — not required for HACS distribution.

## Integration & packaging requirements

Hard requirements from HACS docs:

| Requirement | Source |
|---|---|
| Public GitHub repository | [8] |
| Repo description, topics, README | [8] |
| Root `hacs.json` with at least `name` | [8] |
| Exactly one app directory under **repo-root** `apps/` | [1] |
| All app Python under `apps/APP_NAME/` | [1] |
| GitHub **releases** preferred (tags alone insufficient); else default branch | [1][8] |
| Optional: HACS Action CI with `category: appdaemon` | [4] |

Install behavior: HACS downloads everything under the first directory in `apps` into `<config_dir>/appdaemon/apps/*` [5][6]. It does **not** install a nested `appdaemon/` config tree from the repo. User wiring (`apps.yaml`, entity IDs, secrets) stays outside the HACS package — peers document sample YAML in README / `info.md` rather than shipping house-specific config [3].

**Distribution tiers:**

1. **Custom repository** — add GitHub URL in HACS UI, category AppDaemon, if structure matches [12].
2. **Default store** — PR to `hacs/default` `./appdaemon`, pass HACS Action without ignores, publish a release, owner/major-contributor only; review can take months [9].

## Implementation reality (gap vs this repo)

Evidence from peers: successful AppDaemon HACS packages keep `apps/` at repository root even when they also carry tests, docs, and Python tooling (ControllerX pattern) [11]. The official template is the same shape [3].

**Observed project gaps** (local inspection for the decision — not web evidence):

- Code path is `appdaemon/apps/hvac/`, not `apps/hvac/` → fails HACS structure checks as-is [1].
- No `hacs.json`.
- `appdaemon/apps/apps.yaml` contains house-specific entity IDs → must not be the installable artifact; ship examples only.
- Local Exclusive Session runtime (`appdaemon -c appdaemon/`) expects apps under the config directory; reshaping for HACS needs a deliberate dual-layout (symlink, `app_dir`, or packaging subtree) so local and HACS layouts stay coherent.

**Operational friction for end users:** after AppDaemon add-on v0.15 moved defaults under `addon_configs/`, HACS still installs to HA config `appdaemon/apps/`; maintainers note HACS cannot write `addon_configs`, so users often set `app_dir` to the HACS path [10]. Any README for this project should document that.

**Minimal packaging checklist:**

1. Expose `apps/hvac/` at repo root (reshape monorepo or publish a packaging repo).
2. Add root `hacs.json` (`name` required).
3. Add `.github/workflows` HACS Action (`category: appdaemon`).
4. Publish GitHub releases for versioned updates.
5. Document sample `apps.yaml` with placeholders; keep secrets out of the package.
6. Optional later: PR to `hacs/default`.

## Ecosystem health

The AppDaemon default list is small (56) and quieter than integrations, but still curated (e.g. archived removal Jan 2026) [7][13]. HACS has not documented deprecation of the category [2][4]. Flagship AppDaemon packages continue shipping [11]. Default inclusion is slow by policy [9]; **custom repository is the realistic first publish step**.

**Regret risk:** choosing AppDaemon HACS keeps algorithmic control logic in AppDaemon (aligned with this codebase). Regret would come from wanting Core UI config flows / no AppDaemon dependency — that is an integration rewrite, not a packaging tweak.

## Cross-dimension insights

- **Technically feasible + niche distribution:** packaging is straightforward once layout matches; reach is capped by opt-in discovery and AppDaemon adoption [2][7].
- **Structure is the only hard blocker; productization is the soft one:** HACS will install Python packages; making OpenTherm multi-zone HVAC safe for strangers (entity schema, defaults, docs) is project work beyond HACS rules.
- **Custom repo first avoids the default backlog** without waiting on ecosystem gatekeeping [9][12].

## Recommendations

1. **Treat HACS AppDaemon packaging as feasible** — confidence high on category support and install mechanics [1][4][5].
2. **Do not attempt as-is publishing** — confidence high that `appdaemon/apps/` nesting fails the documented structure [1]; verify with `hacs/action` after a layout change.
3. **Prefer reshape-or-extract over rewriting as a HA integration** unless the goal is to drop AppDaemon — confidence high that peers succeed with AppDaemon+HACS [3][11].
4. **Ship custom repository first; defer `hacs/default`** until releases, docs, and a generic config example exist — confidence medium on timeline (months) [9].
5. **Document AppDaemon `app_dir` alignment** for HAOS users — confidence high this bites real installs [10].

## Open questions

| Question | What would answer it |
|---|---|
| Exact `hacs/action` failure modes on the current tree | Run the action against a branch (or a throwaway fork with only path moved) |
| Whether to reshape this monorepo vs maintain a packaging mirror | Product preference: one repo vs two; local Exclusive Session ergonomics |
| Willingness to generalize entity wiring / remove house IDs from published examples | Owner decision (repo policy already asks before changing house entity IDs) |
| Count of AppDaemon default additions in last 12–24 months | Deeper PR audit of `hacs/default` (sparse search only this run) |

## Source appendix

| Ref | Supports | Publisher | Pub date | Accessed | Confidence |
|---|---|---|---|---|---|
| [1] | AppDaemon structure rules; one app under `apps/` | [HACS publish — AppDaemon](https://www.hacs.xyz/docs/publish/appdaemon/) | live docs | 2026-10-02 | high |
| [2] | Discovery off by default; small-subset framing | [HACS use — AppDaemon](https://www.hacs.xyz/docs/use/repositories/type/appdaemon/) | live docs | 2026-10-02 | high |
| [3] | Official template `ludeeus/ad-hacs` layout | [ludeeus/ad-hacs](https://github.com/ludeeus/ad-hacs/) | repo live | 2026-10-02 | high |
| [4] | HACS Action `category: appdaemon` | [HACS publish — Action](https://www.hacs.xyz/docs/publish/action/) | live docs | 2026-10-02 | high |
| [5] | Downloads first `apps/` dir to `<config>/appdaemon/apps/*` | [HACS FAQ (mirror)](https://manifest--hacs.netlify.app/faq/) | docs mirror | 2026-10-02 | high |
| [6] | Download location under HA config `appdaemon/apps/` | [HACS use — AppDaemon](https://www.hacs.xyz/docs/use/repositories/type/appdaemon/) | live docs | 2026-10-02 | high |
| [7] | 56 default AppDaemon repos | [hacs/default `appdaemon`](https://raw.githubusercontent.com/hacs/default/master/appdaemon) | 2026-10-02 fetch | 2026-10-02 | high |
| [8] | General requirements incl. `hacs.json`, releases | [HACS publish — General](https://www.hacs.xyz/docs/publish/start/) | live docs | 2026-10-02 | high |
| [9] | Default inclusion process; months backlog | [HACS publish — Include](https://www.hacs.xyz/docs/publish/include/) | live docs | 2026-10-02 | medium |
| [10] | Add-on path vs HACS path; `app_dir` workaround | [hacs/integration#4442](https://github.com/hacs/integration/issues/4442) | issue thread | 2026-10-02 | high |
| [11] | ControllerX active AppDaemon HACS package pattern | [xaviml/controllerx](https://github.com/xaviml/controllerx) | 2026-09-28 push | 2026-10-02 | high |
| [12] | Custom repositories FAQ | [HACS FAQ — Custom repositories](https://www.hacs.xyz/docs/faq/custom_repositories/) | live docs | 2026-10-02 | high |
| [13] | appdaemon list still maintained (archived removals) | [hacs/default commits `path=appdaemon`](https://api.github.com/repos/hacs/default/commits?path=appdaemon&per_page=5) | 2026-01-07 | 2026-10-02 | high |

## Staleness map

| Claim class | Freshness window | Earliest re-check |
|---|---|---|
| Version / compatibility (structure, Action category, download path) | ≤ 1 month | **2026-11-01** |
| Ecosystem signals (default list size, ControllerX activity, backlog language) | ≤ 6 months | **2027-04-01** |
| Landscape (category existence, opt-in discovery) | ≤ 12 months | **2027-10-01** |
| Patterns (peer repo layouts) | ≤ 2 years | **2028-10-01** |

**Earliest Refresh trigger:** version/compatibility claims — **2026-11-01** (re-check hacs.xyz publish/appdaemon + Action docs).
