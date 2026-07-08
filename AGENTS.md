# Repository Guidelines

## Project Structure & Module Organization

This repository is a compact Mihomo configuration template project.

- `Full.yaml` is the full node-free template. It carries top-level Mihomo runtime optimizations (`unified-delay: true`, `tcp-concurrent: true`) plus top-level `profile:` (persisting selected strategy groups and fake-ip mappings), `dns:` (fake-ip + DustinWin `fakeip-filter`, domestic direct rule sets returning real IP, `respect-rules`, domestic DoH policies, and overseas default DoH), and `sniffer:` blocks (HTTP/TLS/QUIC domain sniffing for TUN/redir-host accuracy). It keeps AI, streaming, gaming platform, Telegram, Apple, Microsoft, OneDrive, and region node strategy groups.
- `Core.yaml` is the core whitelist template. It stays node-free, keeps the same runtime/profile/DNS/sniffer foundation as `Full.yaml`, keeps only the base selector / `全球直连` groups, routes full Apple and full Microsoft rule sets plus domestic whitelist rules to `全球直连`, and Core's `全球直连` contains only `DIRECT` then `节点选择`; all other unmatched traffic falls through directly to `MATCH,节点选择`.
- `Nano.yaml` is the nano template and should remain node-free and DNS-free; it keeps only `节点选择`, `手动切换`, `自动测速`, `全球直连`, and `漏网之鱼`. All rule sets are from DustinWin.
- `geodata/` stores the public GEOSITE/GEOIP routing variants: `geodata/Full.yaml`, `geodata/Core.yaml`, and `geodata/Nano.yaml`. These templates use MetaCubeX `meta-rules-dat` and define `geox-url`; their routing `rules` must remain pure `GEOSITE`/`GEOIP` with no routing `RULE-SET`. `geodata/Full.yaml` and `geodata/Core.yaml` may define the single DNS-only `fakeip-filter` provider for `dns.fake-ip-filter`.
- `demo/` stores example Mihomo YAML files used for reference and manual comparison.
- `docs/` stores rule-source notes, DNS/fake-ip notes, icon references, and other supporting documentation.
- `README.md` documents user-facing behavior and must be updated when routing logic, template selection, visible strategy groups, or rule-provider sets change.
- `LICENSE` covers this repository's own template content; remotely referenced icons, demo rules, and third-party rules remain under their upstream terms.

## Rule Sources & ShellCrash Compatibility

Remote rule sets come from [DustinWin/ruleset_geodata](https://github.com/DustinWin/ruleset_geodata) by default and are wired as `format: text` `.list` providers for compatibility; keep their `behavior` as `domain` or `ipcidr` according to the source set.

The exceptions are the overseas Apple/Microsoft/OneDrive sets from [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script), because DustinWin publishes no equivalent complete brand sets. They are wired as `classical`/`text` `.list` providers:

- `apple` ← `rule/Clash/Apple/Apple.list`
- `microsoft` ← `rule/Clash/Microsoft/Microsoft.list`
- `onedrive` ← `rule/Clash/OneDrive/OneDrive.list`

Microsoft and OneDrive require `classical`: their lists include important `DOMAIN-KEYWORD` and `PROCESS-NAME` rules that domain-only formats cannot store. All blackmatrix7 paths used here are free of `geosite`/`geoip`.

Template-specific usage:

- `Full.yaml`: `apple-cn` / `microsoft-cn` / `games-cn` are domestic direct supplements; full `apple`, `microsoft`, and `onedrive` route to dedicated service groups. Keep `onedrive` before `microsoft`, because OneDrive domains also appear in Microsoft's broad list.
- `Core.yaml`: full `apple` and full `microsoft` route to `全球直连`; Core's `全球直连` contains only `DIRECT` and `节点选择`, with `DIRECT` first. There are no Apple/Microsoft/OneDrive UI strategy groups or region node strategy groups. Do not re-add `apple-cn` / `microsoft-cn` unless the Core design changes back to CN-only brand supplements.
- `Nano.yaml`: uses only DustinWin `private`, `privateip`, `gfw`, `cn-lite`, and `cnip`.

Regardless of source, root-template rule-provider URLs must avoid the substrings `geosite` and `geoip` anywhere in their paths. ShellCrash scans provider URLs and treats those keywords as a signal that Geo databases (`geoip.metadb` / `geosite.dat`) are required, which triggers extra downloads and checks. Do not switch root-template provider URLs to MetaCubeX `meta-rules-dat` paths even when rule content looks equivalent.

The `geodata/` templates are the explicit exception: they intentionally use MetaCubeX `meta-rules-dat` via top-level `geox-url`. Keep routing rules as `GEOSITE,...` / `GEOIP,...` only; the only permitted `rule-providers` entry is the DNS-only `fakeip-filter` provider used by `dns.fake-ip-filter` in geodata Full/Core. Current public naming is `geodata/Full.yaml`, `geodata/Core.yaml`, and `geodata/Nano.yaml`; avoid adding names that expose `mihomo` unless the user asks.

## Build, Test, and Development Commands

There is no package manager manifest and no generated build step. Use lightweight validation before committing:

- `bash .claude/skills/sift-check/check.sh` (or `/sift-check` in Claude Code) checks project invariants: strategy-group / rule-set referential integrity, the ShellCrash `geosite`/`geoip` URL constraint for root rule-providers, node-free rules, DNS allowance per template, canonical group scopes, geodata routing purity plus the DNS-only fakeip-filter exception, and optional `mihomo` / `yamllint` validation when installed.
- `mihomo -t -f Full.yaml`, `mihomo -t -f Core.yaml`, `mihomo -t -f Nano.yaml`, and the corresponding `geodata/*.yaml` files validate templates when the Mihomo binary is installed locally.
- `yamllint Full.yaml Core.yaml Nano.yaml geodata/*.yaml demo/*.yaml` checks YAML formatting when `yamllint` is available.
- `git diff --check` catches trailing whitespace and common patch formatting issues.

## Coding Style & Naming Conventions

Keep YAML indentation at two spaces and group rules by routing intent, with short comments explaining each block. Preserve established strategy-group names such as `节点选择`, `手动切换`, `自动测速`, `全球直连`, and `漏网之鱼` unless a routing change requires renaming them.

Template scope rules:

- `Full.yaml` may contain the full service/scene groups: `AI`, `流媒体`, `游戏平台`, `Telegram`, `苹果服务`, `微软服务`, `OneDrive`, plus region groups.
- `Core.yaml` keeps only the base selector groups and `全球直连`, and intentionally removes service/brand UI groups, region node groups, and the separate `漏网之鱼` fallback group. Its special case is full `apple` and full `microsoft` routed to `全球直连`; Core's `全球直连` is `DIRECT` first, then `节点选择`, and final fallback is `MATCH,节点选择`.
- `Nano.yaml` and `geodata/Nano.yaml` must stay DNS-free and rule-light: do not add AI, entertainment, gaming, Telegram, Apple/Microsoft/OneDrive, DNS, or region node groups unless the template goal is explicitly changed.
- `geodata/Full.yaml` mirrors Full's visible groups but uses MetaCubeX geosite categories. Keep game rules (`category-game-platforms-download`, `category-games`) before `category-entertainment`, because the entertainment category overlaps games and would otherwise capture gaming-platform traffic too early. Keep `GEOSITE,google,节点选择` after the high-priority category/service rules but before `GEOSITE,geolocation-!cn` / `GEOSITE,cn` so Google Play is protected without stealing YouTube/AI from their scenario groups.
- `geodata/Core.yaml` keeps the same 4-group Core contract and routes full `GEOSITE,apple` / `GEOSITE,microsoft` to `全球直连`; `GEOSITE,google,节点选择` must stay before `GEOSITE,cn,全球直连` so Google Play / `googleapis.cn` traffic is not captured by the domestic fallback; final fallback remains `MATCH,节点选择`.
- Do not re-add `GEOSITE,google@cn,全球直连` to geodata Full/Core by default: Android / Google Play download and connectivity domains can be captured by that tag and fail when sent direct on domestic networks.

Keep each `rule-providers` key synchronized with the upstream rule-set file basename when practical. Use `cn-lite` for routing-domain fallback and full `cn` only for DNS `nameserver-policy` / `fake-ip-filter` coverage. Deliberate exceptions:

- blackmatrix7 service keys (`apple`, `microsoft`, `onedrive`) map to capitalized upstream paths.

Do not replace the routing `cn-lite` provider with full `cn.list`; the full set can over-direct domains that should fall through to proxy. For overlapping rules, place the more specific or higher-intent rule first.

In `Full.yaml`, the `其他节点` group is the complement of the region node groups (`香港节点`, `美国节点`, `日本节点`, `新加坡节点`). It uses `include-all: true` + `exclude-filter`; its `exclude-filter` must stay the exact union of those region groups' `filter` keywords, including emoji flags and the `(?i)` case-insensitive flag.

## Testing Guidelines

No automated test suite is currently checked in. For configuration edits, validate changed templates with `sift-check`, `mihomo` when available, and manual comparison against `demo/` examples where relevant. When editing geodata templates, additionally check that routing rules stay `GEOSITE`/`GEOIP` only and that the only allowed `rule-providers:` entry is DNS-only `fakeip-filter`.

## Commit & Pull Request Guidelines

Recent history mostly follows Conventional Commit style with optional scopes, for example `chore(rules): ...`, `feat(config): ...`, and `refactor(config): ...`. Use concise Chinese or English summaries, and choose scopes such as `config`, `rules`, `docs`, or `scripts`.

Pull requests should describe the routing behavior changed, list validation commands run, and mention compatibility risks for existing Mihomo clients. For template changes, state whether the change affects `Full.yaml`, `Core.yaml`, `Nano.yaml`, or docs/check tooling. Include screenshots only when UI panel behavior or strategy-group ordering is relevant.

## Security & Configuration Tips

Do not commit personal proxy nodes, subscription URLs, credentials, API tokens, or generated configs containing private endpoints. Keep `Full.yaml`, `Core.yaml`, and `Nano.yaml` as reusable public templates. Do not vendor third-party icon assets or rulesets unless their license and attribution requirements are checked and documented; remote icon references currently point to `Koolson/Qure`.
