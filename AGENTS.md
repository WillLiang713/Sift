# Repository Guidelines

## Project Structure & Module Organization

This repository is a compact Mihomo configuration template project.

- **Default hybrid templates** (MRS-first, not locked to one upstream):
  - `rules/full.yaml` — Full scene groups + region groups + DNS/sniffer. DustinWin MRS skeleton (`ads`, `proxy`, `cn-lite`, scene sets) + MetaCubeX geosite MRS brands (`google`, `apple`, `microsoft`, `onedrive`, `github`) and DNS-only `cn.mrs`. Hard order: `github` and `onedrive` before `microsoft` (MetaCubeX microsoft is broad); `google`/`proxy` before `cn-lite`.
  - `rules/core.yaml` — 5-group Core; Apple/Microsoft → `全球直连`; `github`/`onedrive` → `节点选择` before microsoft; `MATCH,节点选择`.
  - `rules/nano.yaml` — 6-group Nano; DustinWin MRS only; DNS-free / sniffer-free.
  - Full/Core share runtime hardenings: `prefer-h3: false`, sniffer `skip-domain`, url-test `timeout: 3000`, info-node `exclude-filter`, rule-provider `proxy: DIRECT`. Full/Core use overseas-default DNS for domains not matched by `nameserver-policy`; explicit `cn,private` policy and direct lookups remain on domestic DoH. They do not use concurrent DNS `fallback`, preventing unclassified queries from being sent to domestic resolvers. GeoIP data remains pinned to MetaCubeX `geoip.metadb` in MMDB mode with 24-hour auto-update.
- **Optional single-source variants** under `rules/variants/` (original formats kept; same runtime hardenings; **not** force-MRS):
  - `rules/variants/DustinWin-*.yaml` — text `.list` + blackmatrix7 classical brands.
  - `rules/variants/MetaCubeX-*.yaml` — pure `GEOSITE`/`GEOIP`, `geox-url`, no routing `rule-providers`.
  - `rules/variants/ACL4SSR-*.yaml` — ACL Clash `.list`; DNS-only DustinWin `proxy`; UnBan+Ban ads; Full streaming split lists.
- `demo/` stores example Mihomo YAML files used for reference and manual comparison.
- `docs/` stores rule-source notes, DNS/fake-ip notes, icon references, and other supporting documentation.
- `README.md` documents user-facing behavior and must be updated when routing logic, template selection, visible strategy groups, or rule-provider sets change.
- `LICENSE` covers this repository's own template content; remotely referenced icons, demo rules, and third-party rules remain under their upstream terms.

## Rule Sources

**Hybrid main templates** prefer MRS (`format: mrs`): DustinWin `mihomo-ruleset/*.mrs` for domain/ipcidr sets; MetaCubeX `meta/geo/geosite/*.mrs` for brand/github/DNS `cn`. blackmatrix7 classical `.list` is not used on the hybrid path (classical cannot encode into MRS).

**variants** keep prior formats and do not force MRS. Variant DustinWin/ACL4SSR sets come from [DustinWin/ruleset_geodata](https://github.com/DustinWin/ruleset_geodata) as `format: text` `.list` (and blackmatrix7 classical where needed). Full/Core fake-IP whitelist mode makes unlisted private, CN, Tracker, and compatibility domains return real IP naturally. DustinWin/ACL4SSR retain MetaCubeX `cn.mrs` only for domestic `nameserver-policy`; ACL4SSR additionally uses DustinWin `proxy` as a DNS-only domain whitelist.

Do not re-add `trackerslist` to Full/Core `dns.fake-ip-filter`: under whitelist mode, Tracker domains already receive real IP because they are absent from the proxy whitelist. Never add a routing `RULE-SET,trackerslist,...` rule.

The exceptions are the complete Google/Apple/Microsoft/OneDrive sets from [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script), because DustinWin publishes no equivalent complete brand sets. They are wired as `classical`/`text` `.list` providers:

- `google` ← `rule/Clash/Google/Google.list` (Full only → `谷歌服务`; also used by ACL4SSR Full)
- `apple` ← `rule/Clash/Apple/Apple.list`
- `microsoft` ← `rule/Clash/Microsoft/Microsoft.list`
- `onedrive` ← `rule/Clash/OneDrive/OneDrive.list`

Google, Microsoft, and OneDrive require `classical`: their lists include important keyword, IP, or process rules that domain-only formats cannot store.

All three DustinWin templates also use DustinWin `proxy` (domain/text, `geolocation-!cn` + gfwlist) as the explicit non-CN proxy layer, placed like MetaCubeX `GEOSITE,geolocation-!cn`: after service/brand direct-or-group rules and before `cn-lite`.

Template-specific usage:

- `rules/variants/DustinWin-full.yaml`: `ads` routes to `广告拦截` immediately after private rules; `apple-cn` / `microsoft-cn` / `games-cn` are domestic direct supplements; full `apple`, `microsoft`, `onedrive`, and blackmatrix7 `google` route to dedicated service groups (`谷歌服务` for Google); `proxy` routes to `节点选择` after those service/scene rules and before `cn-lite`. Keep `onedrive` before `microsoft`, because OneDrive domains also appear in Microsoft's broad list. Keep `google` before `proxy` / `cn-lite` so `googleapis.cn` is not mis-directed. DNS-only `cn` is MetaCubeX `cn.mrs` (not DustinWin `cn.list` / not routing).
- `rules/variants/DustinWin-core.yaml`: full `apple` and full `microsoft` route to `全球直连`; blackmatrix7 `onedrive` routes to `节点选择` immediately before `microsoft` (same ordering as Full; no OneDrive UI group). `proxy` routes to `节点选择` after those direct-service rules and before `cn-lite`. Core's `全球直连` contains `DIRECT`, `节点选择`, and `自动测速`, with `DIRECT` first. There are no Google/Apple/Microsoft/OneDrive UI strategy groups or region node strategy groups. Do not re-add CN-only Google/Apple/Microsoft brand supplements unless the Core design changes back to CN-only brand supplements. Same DNS-only MetaCubeX `cn.mrs` as Full.
- `rules/variants/DustinWin-nano.yaml`: uses DustinWin `private`, `privateip`, `ads`, `proxy`, `cn-lite`, and `cnip` only; `ads` precedes `proxy`, which remains the sole explicit non-CN proxy layer before `cn-lite`.

This project does **not** work around ShellCrash heuristics that treat `geosite`/`geoip` URL substrings as “must download Geo databases”. MetaCubeX `meta-rules-dat` paths (including `.../geosite/cn.mrs`) are allowed when they are the correct source. ShellCrash-side false positives are out of scope.

The `rules/variants/MetaCubeX-*.yaml` templates intentionally use MetaCubeX `meta-rules-dat` via top-level `geox-url`. Keep routing rules as `GEOSITE,...` / `GEOIP,...` only and do not define `rule-providers`; Full/Core fake-IP whitelist and domestic DNS policy use geosite selectors directly. Public filenames are `rules/variants/MetaCubeX-full.yaml`, `rules/variants/MetaCubeX-core.yaml`, and `rules/variants/MetaCubeX-nano.yaml`.

## Build, Test, and Development Commands

There is no package manager manifest and no generated build step. Use lightweight validation before committing:

- `mihomo -t -f rules/full.yaml` (also `core`/`nano` and `rules/variants/*.yaml`) validate templates when the Mihomo binary is installed locally.
- `yamllint rules/*.yaml rules/variants/*.yaml demo/*.yaml` checks YAML formatting when `yamllint` is available.
- `git diff --check` catches trailing whitespace and common patch formatting issues.

## Coding Style & Naming Conventions

Keep YAML indentation at two spaces and group rules by routing intent, with short comments explaining each block. Preserve established strategy-group names such as `节点选择`, `手动切换`, `自动测速`, `全球直连`, and `漏网之鱼` unless a routing change requires renaming them.

Template scope rules:

- All templates keep the common `广告拦截` select group with `REJECT` first, followed by `DIRECT` and `节点选择`, so blocking is enabled by default and can be temporarily bypassed from the UI when a false positive occurs.
- Full templates may contain the full service/scene groups: `AI`, `流媒体`, `游戏平台`, `Telegram`, `苹果服务`, `谷歌服务`, `微软服务`, `OneDrive`, plus region groups and the common `广告拦截` group.
- Core templates keep only the base selector groups, `全球直连`, and `广告拦截`, and intentionally remove service/brand UI groups, region node groups, and the separate `漏网之鱼` fallback group. Their special case is full `apple` and full `microsoft` routed to `全球直连`, while OneDrive is split out ahead of Microsoft and routes to `节点选择` (no OneDrive UI group; keeps Store/Xbox-style Microsoft downloads direct-capable while OneDrive can use the proxy). Core's `全球直连` is `DIRECT` first, then `节点选择` and `自动测速`, and final fallback is `MATCH,节点选择`.
- Nano templates must stay DNS-free and rule-light: they may keep the single common advertising layer (`ads`, `category-ads-all`, or ACL4SSR `UnBan` + `BanAD` / `BanProgramAD` according to source family); DustinWin Nano may use the `proxy` provider as the explicit non-CN proxy layer (MetaCubeX uses `geolocation-!cn`, ACL4SSR uses `ProxyLite`), but do not add Google UI groups, AI, entertainment, gaming, Telegram, Apple/Microsoft/OneDrive, DNS, or region node groups unless the template goal is explicitly changed.
- `rules/variants/MetaCubeX-full.yaml` mirrors Full's visible groups but uses MetaCubeX geosite categories. Keep `GEOSITE,category-ads-all,广告拦截` immediately after private rules, then `GEOSITE,github,节点选择`, because MetaCubeX's Microsoft and scenario categories include GitHub / Copilot-related domains that should keep using the proxy path. Route full `GEOSITE,apple` to `苹果服务` before entertainment scenarios; `apple@cn` remains a domestic direct supplement. Keep game rules (`category-game-platforms-download`, `category-games`) before `category-entertainment`, because the entertainment category overlaps games and would otherwise capture gaming-platform traffic too early. Route full `GEOSITE,microsoft` to `微软服务`; `microsoft@cn` remains a domestic direct supplement. Route `GEOSITE,google` to `谷歌服务` after scene/brand groups and before `geolocation-!cn` / `cn`, so Google (including `googleapis.cn`) is selectable while YouTube can still hit `category-entertainment` first.
- `rules/variants/MetaCubeX-core.yaml` keeps the 5-group Core contract and routes full `GEOSITE,apple` and full `GEOSITE,microsoft` to `全球直连`; keep `GEOSITE,category-ads-all,广告拦截` immediately after private rules and `GEOSITE,github,节点选择` after the advertising layer. Keep `GEOSITE,onedrive,节点选择` immediately before `GEOSITE,microsoft` (no OneDrive UI group). Keep `GEOSITE,geolocation-!cn,节点选择` after the explicit Core direct-service rules and before `GEOSITE,cn,全球直连`. Final fallback remains `MATCH,节点选择`.
- MetaCubeX Core/Nano keep a routing-only `GEOSITE,google,节点选择` immediately after `geolocation-!cn` and before `GEOSITE,cn` (no Google UI group). MetaCubeX Full routes the same tag to the `谷歌服务` strategy group before `geolocation-!cn`. MetaCubeX `geolocation-!cn` does not cover some global Google services on `.cn` (notably `googleapis.cn` / `gstatic.cn`), which otherwise match the broad `cn` / `tld-cn` sets and would be sent direct. Do not re-add `GEOSITE,google@cn,全球直连` by default: Android / Google Play download and connectivity domains can be captured by that tag and fail when sent direct on domestic networks.

Keep each `rule-providers` key synchronized with the upstream rule-set file basename when practical. Use `cn-lite` for DustinWin **routing** domain fallback. Full/Core DNS uses fake-IP whitelist mode: DustinWin uses `rule-set:proxy`, ACL4SSR uses a DNS-only DustinWin `proxy`, and MetaCubeX uses `geosite:geolocation-!cn` plus `geosite:google`. Unlisted private, CN, Tracker, and compatibility domains return real IP. `nameserver-policy` has two layers: `proxy` (DustinWin/ACL4SSR) or `geolocation-!cn,google` (MetaCubeX) forced to overseas DoH; `cn,private` forced to domestic DoH (DustinWin/ACL4SSR: `rule-set:cn,private`; MetaCubeX: `geosite:cn,private`). Domains unmatched by policy use overseas `nameserver` only; do not add DNS `fallback` / `fallback-filter`, because concurrent domestic queries expose unclassified domains even when their final traffic uses a proxy. All DNS-enabled Full/Core templates must explicitly manage GeoIP data with `geodata-mode: false`, MetaCubeX `geoip.metadb` as `geox-url.mmdb`, `geo-auto-update: true`, and a 24-hour interval. This prevents `.cn` proxy domains like `googleapis.cn` from receiving polluted or CDN-locked Chinese DNS answers via the `cn` policy. Do **not** put DNS MetaCubeX `cn` into DustinWin routing in place of `cn-lite`. Broader non-matching DIRECT traffic still uses `respect-rules` + `direct-nameserver`. Deliberate exceptions:

- blackmatrix7 service keys (`google`, `apple`, `microsoft`, `onedrive`) map to capitalized upstream paths.
- DustinWin / ACL4SSR Full/Core define MetaCubeX `cn` as a nameserver-policy-only MRS provider; ACL4SSR also defines DustinWin `proxy` as a DNS-only fake-IP whitelist (routing stays `cn-lite` / `ChinaDomain`).

Do not replace the routing `cn-lite` provider with full DustinWin `cn.list` or MetaCubeX DNS `cn`; the broader set can over-direct domains that should fall through to proxy. For overlapping rules, place the more specific or higher-intent rule first.

In full templates, the `其他节点` group is the complement of the region node groups (`香港节点`, `美国节点`, `日本节点`, `新加坡节点`). It uses `include-all: true` + `exclude-filter`; its `exclude-filter` must stay the exact union of those region groups' `filter` keywords, including emoji flags and the `(?i)` case-insensitive flag.

## Testing Guidelines

No automated test suite is currently checked in. For configuration edits, validate changed templates with `mihomo` and `yamllint` when available, plus manual comparison against `demo/` examples where relevant. When editing MetaCubeX templates, additionally check that routing rules stay `GEOSITE`/`GEOIP` only and that no `rule-providers:` block is present.

## Commit & Pull Request Guidelines

Recent history mostly follows Conventional Commit style with optional scopes, for example `chore(rules): ...`, `feat(config): ...`, and `refactor(config): ...`. Use concise Chinese or English summaries, and choose scopes such as `config`, `rules`, `docs`, or `scripts`.

Pull requests should describe the routing behavior changed, list validation commands run, and mention compatibility risks for existing Mihomo clients. For template changes, state whether the change affects DustinWin, MetaCubeX, ACL4SSR, or docs/check tooling. Include screenshots only when UI panel behavior or strategy-group ordering is relevant.

## Security & Configuration Tips

Do not commit personal proxy nodes, subscription URLs, credentials, API tokens, or generated configs containing private endpoints. Keep `rules/*.yaml` as reusable public templates. Do not vendor third-party icon assets or rulesets unless their license and attribution requirements are checked and documented; remote icon references currently point to `Koolson/Qure`.
