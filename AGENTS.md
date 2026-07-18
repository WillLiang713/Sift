# Repository Guidelines

## Project Structure & Module Organization

This repository is a compact Mihomo configuration template project.

- `rules/DustinWin-full.yaml` is the full node-free DustinWin-based template. It carries top-level Mihomo runtime controls (`ipv6: true`, `unified-delay: true`, `tcp-concurrent: true`) plus top-level `profile:` (persisting selected strategy groups and fake-ip mappings), `dns:` (fake-ip, `ipv6: true` for AAAA answers, DustinWin `fakeip-filter`, domestic direct rule sets returning real IP, `respect-rules`, domestic DoH policies, and overseas default DoH), and `sniffer:` blocks (HTTP/TLS/QUIC domain sniffing for TUN/redir-host accuracy). Keep both IPv6 settings in all Full/Core templates: the top-level switch allows IPv6 connections, while `dns.ipv6: true` returns AAAA answers. To disable IPv6 for leak hardening, set both to `false`. It keeps AI, streaming, gaming platform, Telegram, Apple, Microsoft, OneDrive, and region node strategy groups, and routes DustinWin `proxy` (explicit non-CN domains) to `节点选择` after service/scene groups and before `cn-lite`, aligning with MetaCubeX `GEOSITE,geolocation-!cn` placement.
- `rules/DustinWin-core.yaml` is the core whitelist DustinWin-based template. It stays node-free, keeps the same runtime/profile/DNS/sniffer foundation as the full template, keeps only the base selector / `全球直连` groups, routes full Apple and full Microsoft rule sets plus domestic whitelist rules to `全球直连`, routes blackmatrix7 `onedrive` to `节点选择` immediately before `microsoft` (no OneDrive UI group; OneDrive domains also appear in Microsoft's broad list), routes DustinWin `proxy` to `节点选择` after those direct-service rules and before `cn-lite`, and Core's `全球直连` contains `DIRECT`, `节点选择`, and `自动测速` with `DIRECT` first; all other unmatched traffic falls through directly to `MATCH,节点选择`.
- `rules/DustinWin-nano.yaml` is the nano DustinWin-based template and should remain node-free and DNS-free; it keeps only `节点选择`, `手动切换`, `自动测速`, `全球直连`, and `漏网之鱼`, with DustinWin `proxy` as the sole explicit non-CN proxy layer before domestic fallbacks (aligned with MetaCubeX `geolocation-!cn` / ACL4SSR `ProxyLite`).
- `rules/MetaCubeX-*.yaml` stores the public GEOSITE/GEOIP routing variants. These templates use MetaCubeX `meta-rules-dat` and define `geox-url`; their routing `rules` must remain pure `GEOSITE`/`GEOIP` with no routing `RULE-SET`. `rules/MetaCubeX-full.yaml` and `rules/MetaCubeX-core.yaml` may define the single DNS-only `fakeip-filter` provider for `dns.fake-ip-filter`.
- `rules/ACL4SSR-*.yaml` stores the ACL4SSR Clash `.list` variants. Full/Core align DNS rule-set providers with DustinWin templates by using DustinWin `fakeip-filter`, `private`, and `cn`; ACL4SSR classical lists stay routing-only. Keep `ProxyLite` before `ChinaDomain` in all ACL4SSR variants that define both, because `ChinaDomain` contains the broad `DOMAIN-SUFFIX,cn` rule while `ProxyLite` explicitly classifies exceptions such as `googleapis.cn` for `节点选择`. ACL4SSR Full routes streaming via ACL brand packs (`YouTube`, `Netflix`, `NetflixIP`, `DisneyPlus`, `Spotify`, `TikTok`) to `流媒体` before `Google`/`ProxyLite`; do not re-add aggregate `ProxyMedia` (it pulls non-content hosts such as `challenges.cloudflare.com` into the media group).
- `demo/` stores example Mihomo YAML files used for reference and manual comparison.
- `docs/` stores rule-source notes, DNS/fake-ip notes, icon references, and other supporting documentation.
- `README.md` documents user-facing behavior and must be updated when routing logic, template selection, visible strategy groups, or rule-provider sets change.
- `LICENSE` covers this repository's own template content; remotely referenced icons, demo rules, and third-party rules remain under their upstream terms.

## Rule Sources & ShellCrash Compatibility

Remote rule sets come from [DustinWin/ruleset_geodata](https://github.com/DustinWin/ruleset_geodata) by default and are wired as `format: text` `.list` providers for compatibility; keep their `behavior` as `domain` or `ipcidr` according to the source set.

`rules/DustinWin-full.yaml` also uses `trackerslist` from [DustinWin/domain-list-custom](https://github.com/DustinWin/domain-list-custom) as a BT tracker direct supplement. It is a Clash rule-line `.list`, so keep it as `behavior: classical` and `format: text`.

The exceptions are the complete Google/Apple/Microsoft/OneDrive sets from [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script), because DustinWin publishes no equivalent complete brand sets. They are wired as `classical`/`text` `.list` providers:

- `google` ← `rule/Clash/Google/Google.list` (Full only → `谷歌服务`; also used by ACL4SSR Full)
- `apple` ← `rule/Clash/Apple/Apple.list`
- `microsoft` ← `rule/Clash/Microsoft/Microsoft.list`
- `onedrive` ← `rule/Clash/OneDrive/OneDrive.list`

Google, Microsoft, and OneDrive require `classical`: their lists include important keyword, IP, or process rules that domain-only formats cannot store. All blackmatrix7 paths used here are free of `geosite`/`geoip`.

All three DustinWin templates also use DustinWin `proxy` (domain/text, `geolocation-!cn` + gfwlist) as the explicit non-CN proxy layer, placed like MetaCubeX `GEOSITE,geolocation-!cn`: after service/brand direct-or-group rules and before `cn-lite`.

Template-specific usage:

- `rules/DustinWin-full.yaml`: `apple-cn` / `microsoft-cn` / `games-cn` are domestic direct supplements; full `apple`, `microsoft`, `onedrive`, and blackmatrix7 `google` route to dedicated service groups (`谷歌服务` for Google); `proxy` routes to `节点选择` after those service/scene rules and before `cn-lite`. Keep `onedrive` before `microsoft`, because OneDrive domains also appear in Microsoft's broad list. Keep `google` before `proxy` / `cn-lite` so `googleapis.cn` is not mis-directed.
- `rules/DustinWin-core.yaml`: full `apple` and full `microsoft` route to `全球直连`; blackmatrix7 `onedrive` routes to `节点选择` immediately before `microsoft` (same ordering as Full; no OneDrive UI group). `proxy` routes to `节点选择` after those direct-service rules and before `cn-lite`. Core's `全球直连` contains `DIRECT`, `节点选择`, and `自动测速`, with `DIRECT` first. There are no Google/Apple/Microsoft/OneDrive UI strategy groups or region node strategy groups. Do not re-add CN-only Google/Apple/Microsoft brand supplements unless the Core design changes back to CN-only brand supplements.
- `rules/DustinWin-nano.yaml`: uses DustinWin `private`, `privateip`, `proxy`, `cn-lite`, and `cnip` only; `proxy` is the sole explicit non-CN proxy layer before `cn-lite`.

Regardless of source, root-template rule-provider URLs must avoid the substrings `geosite` and `geoip` anywhere in their paths. ShellCrash scans provider URLs and treats those keywords as a signal that Geo databases (`geoip.metadb` / `geosite.dat`) are required, which triggers extra downloads and checks. Do not switch root-template provider URLs to MetaCubeX `meta-rules-dat` paths even when rule content looks equivalent.

The `rules/MetaCubeX-*.yaml` templates are the explicit exception: they intentionally use MetaCubeX `meta-rules-dat` via top-level `geox-url`. Keep routing rules as `GEOSITE,...` / `GEOIP,...` only; the only permitted `rule-providers` entry is the DNS-only `fakeip-filter` provider used by `dns.fake-ip-filter` in MetaCubeX Full/Core. Public filenames are `rules/MetaCubeX-full.yaml`, `rules/MetaCubeX-core.yaml`, and `rules/MetaCubeX-nano.yaml`.

## Build, Test, and Development Commands

There is no package manager manifest and no generated build step. Use lightweight validation before committing:

- `bash .claude/skills/sift-check/check.sh` (or `/sift-check` in Claude Code) checks project invariants: strategy-group / rule-set referential integrity, the ShellCrash `geosite`/`geoip` URL constraint for root rule-providers, node-free rules, DNS allowance per template, canonical group scopes, geodata routing purity plus the DNS-only fakeip-filter exception, and optional `mihomo` / `yamllint` validation when installed.
- `mihomo -t -f rules/DustinWin-full.yaml` and the corresponding `rules/*.yaml` files validate templates when the Mihomo binary is installed locally.
- `yamllint rules/*.yaml demo/*.yaml` checks YAML formatting when `yamllint` is available.
- `git diff --check` catches trailing whitespace and common patch formatting issues.

## Coding Style & Naming Conventions

Keep YAML indentation at two spaces and group rules by routing intent, with short comments explaining each block. Preserve established strategy-group names such as `节点选择`, `手动切换`, `自动测速`, `全球直连`, and `漏网之鱼` unless a routing change requires renaming them.

Template scope rules:

- Full templates may contain the full service/scene groups: `AI`, `流媒体`, `游戏平台`, `Telegram`, `苹果服务`, `谷歌服务`, `微软服务`, `OneDrive`, plus region groups.
- Core templates keep only the base selector groups and `全球直连`, and intentionally remove service/brand UI groups, region node groups, and the separate `漏网之鱼` fallback group. Their special case is full `apple` and full `microsoft` routed to `全球直连`, while OneDrive is split out ahead of Microsoft and routes to `节点选择` (no OneDrive UI group; keeps Store/Xbox-style Microsoft downloads direct-capable while OneDrive can use the proxy). Core's `全球直连` is `DIRECT` first, then `节点选择` and `自动测速`, and final fallback is `MATCH,节点选择`.
- Nano templates must stay DNS-free and rule-light: DustinWin Nano may use the `proxy` provider as the explicit non-CN proxy layer (MetaCubeX uses `geolocation-!cn`, ACL4SSR uses `ProxyLite`), but do not add Google UI groups, AI, entertainment, gaming, Telegram, Apple/Microsoft/OneDrive, DNS, or region node groups unless the template goal is explicitly changed.
- `rules/MetaCubeX-full.yaml` mirrors Full's visible groups but uses MetaCubeX geosite categories. Keep `GEOSITE,github,节点选择` immediately after private rules because MetaCubeX's Microsoft and scenario categories include GitHub / Copilot-related domains that should keep using the proxy path. Route full `GEOSITE,apple` to `苹果服务` before entertainment scenarios; `apple@cn` remains a domestic direct supplement. Keep game rules (`category-game-platforms-download`, `category-games`) before `category-entertainment`, because the entertainment category overlaps games and would otherwise capture gaming-platform traffic too early. Route full `GEOSITE,microsoft` to `微软服务`; `microsoft@cn` remains a domestic direct supplement. Route `GEOSITE,google` to `谷歌服务` after scene/brand groups and before `geolocation-!cn` / `cn`, so Google (including `googleapis.cn`) is selectable while YouTube can still hit `category-entertainment` first.
- `rules/MetaCubeX-core.yaml` keeps the same 4-group Core contract and routes full `GEOSITE,apple` and full `GEOSITE,microsoft` to `全球直连`; keep `GEOSITE,onedrive,节点选择` immediately before `GEOSITE,microsoft` (no OneDrive UI group). `GEOSITE,github,节点选择` must stay immediately after private rules. Keep `GEOSITE,geolocation-!cn,节点选择` after the explicit Core direct-service rules and before `GEOSITE,cn,全球直连`. Final fallback remains `MATCH,节点选择`.
- MetaCubeX Core/Nano keep a routing-only `GEOSITE,google,节点选择` immediately after `geolocation-!cn` and before `GEOSITE,cn` (no Google UI group). MetaCubeX Full routes the same tag to the `谷歌服务` strategy group before `geolocation-!cn`. MetaCubeX `geolocation-!cn` does not cover some global Google services on `.cn` (notably `googleapis.cn` / `gstatic.cn`), which otherwise match the broad `cn` / `tld-cn` sets and would be sent direct. Do not re-add `GEOSITE,google@cn,全球直连` by default: Android / Google Play download and connectivity domains can be captured by that tag and fail when sent direct on domestic networks.

Keep each `rule-providers` key synchronized with the upstream rule-set file basename when practical. Use `cn-lite` for routing-domain fallback and full `cn` only for DNS `nameserver-policy` / `fake-ip-filter` coverage. Deliberate exceptions:

- blackmatrix7 service keys (`google`, `apple`, `microsoft`, `onedrive`) map to capitalized upstream paths.

Do not replace the routing `cn-lite` provider with full `cn.list`; the full set can over-direct domains that should fall through to proxy. For overlapping rules, place the more specific or higher-intent rule first.

In full templates, the `其他节点` group is the complement of the region node groups (`香港节点`, `美国节点`, `日本节点`, `新加坡节点`). It uses `include-all: true` + `exclude-filter`; its `exclude-filter` must stay the exact union of those region groups' `filter` keywords, including emoji flags and the `(?i)` case-insensitive flag.

## Testing Guidelines

No automated test suite is currently checked in. For configuration edits, validate changed templates with `sift-check`, `mihomo` when available, and manual comparison against `demo/` examples where relevant. When editing MetaCubeX templates, additionally check that routing rules stay `GEOSITE`/`GEOIP` only and that the only allowed `rule-providers:` entry is DNS-only `fakeip-filter`.

## Commit & Pull Request Guidelines

Recent history mostly follows Conventional Commit style with optional scopes, for example `chore(rules): ...`, `feat(config): ...`, and `refactor(config): ...`. Use concise Chinese or English summaries, and choose scopes such as `config`, `rules`, `docs`, or `scripts`.

Pull requests should describe the routing behavior changed, list validation commands run, and mention compatibility risks for existing Mihomo clients. For template changes, state whether the change affects DustinWin, MetaCubeX, ACL4SSR, or docs/check tooling. Include screenshots only when UI panel behavior or strategy-group ordering is relevant.

## Security & Configuration Tips

Do not commit personal proxy nodes, subscription URLs, credentials, API tokens, or generated configs containing private endpoints. Keep `rules/*.yaml` as reusable public templates. Do not vendor third-party icon assets or rulesets unless their license and attribution requirements are checked and documented; remote icon references currently point to `Koolson/Qure`.
