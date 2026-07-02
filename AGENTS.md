# Repository Guidelines

## Project Structure & Module Organization

This repository is a compact Mihomo configuration template project.

- `Full.yaml` is the full node-free template. It carries top-level Mihomo runtime optimizations (`unified-delay: true`, `tcp-concurrent: true`) plus a top-level `dns:` block (fake-ip + DustinWin `fakeip-filter`, domestic direct rule sets returning real IP, `respect-rules`, domestic DoH policies, and overseas default DoH). It keeps AI, streaming, gaming platform, Telegram, Apple, Microsoft, OneDrive, and region node strategy groups.
- `Core.yaml` is the core whitelist template. It stays node-free, keeps the same runtime/DNS foundation as `Full.yaml`, keeps only the base selector / region / direct / fallback groups, routes full Apple and full Microsoft rule sets to `全球直连`, preserves domestic direct rule sets, and lets all other unmatched traffic fall through to `MATCH,漏网之鱼`.
- `Nano.yaml` is the nano template and should remain node-free and DNS-free; it keeps only `节点选择`, `手动切换`, `自动测速`, `全球直连`, and `漏网之鱼`. All rule sets are from DustinWin.
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
- `Core.yaml`: full `apple` and full `microsoft` route directly to `全球直连`; there are no Apple/Microsoft/OneDrive UI strategy groups. Do not re-add `apple-cn` / `microsoft-cn` unless the Core design changes back to CN-only brand supplements.
- `Nano.yaml`: uses only DustinWin `private`, `privateip`, `gfw`, `cn` (`cn-lite.list`), and `cnip`.

Regardless of source, rule-provider URLs must avoid the substrings `geosite` and `geoip` anywhere in their paths. ShellCrash scans provider URLs and treats those keywords as a signal that Geo databases (`geoip.metadb` / `geosite.dat`) are required, which triggers extra downloads and checks. Do not switch provider URLs to MetaCubeX `meta-rules-dat` paths even when rule content looks equivalent.

## Build, Test, and Development Commands

There is no package manager manifest and no generated build step. Use lightweight validation before committing:

- `bash .claude/skills/sift-check/check.sh` (or `/sift-check` in Claude Code) checks project invariants: strategy-group / rule-set referential integrity, the ShellCrash `geosite`/`geoip` URL constraint, node-free rules, DNS allowance per template, canonical group scopes, and optional `mihomo` / `yamllint` validation when installed.
- `mihomo -t -f Full.yaml`, `mihomo -t -f Core.yaml`, and `mihomo -t -f Nano.yaml` validate templates when the Mihomo binary is installed locally.
- `yamllint Full.yaml Core.yaml Nano.yaml demo/*.yaml` checks YAML formatting when `yamllint` is available.
- `git diff --check` catches trailing whitespace and common patch formatting issues.

## Coding Style & Naming Conventions

Keep YAML indentation at two spaces and group rules by routing intent, with short comments explaining each block. Preserve established strategy-group names such as `节点选择`, `手动切换`, `自动测速`, `全球直连`, and `漏网之鱼` unless a routing change requires renaming them.

Template scope rules:

- `Full.yaml` may contain the full service/scene groups: `AI`, `流媒体`, `游戏平台`, `Telegram`, `苹果服务`, `微软服务`, `OneDrive`, plus region groups.
- `Core.yaml` keeps region groups and the base selector groups, but intentionally removes service/brand UI groups. Its special case is full `apple` and full `microsoft` routed to `全球直连` to avoid App Store / Microsoft account and subscription-region issues.
- `Nano.yaml` must stay smaller than Full/Core: do not add AI, entertainment, gaming, Telegram, Apple/Microsoft/OneDrive, DNS, or region node groups unless the template goal is explicitly changed.

Keep each `rule-providers` key synchronized with the upstream rule-set file basename when practical. Deliberate exceptions:

- `cn` maps to `cn-lite.list` for routing compatibility.
- `cn-dns` maps to full `cn.list` for DNS `nameserver-policy` / `fake-ip-filter` coverage.
- blackmatrix7 service keys (`apple`, `microsoft`, `onedrive`) map to capitalized upstream paths.

Do not replace the routing `cn` provider with full `cn.list`; the full set can over-direct domains that should fall through to proxy. For overlapping rules, place the more specific or higher-intent rule first.

The `其他节点` group is the complement of the region node groups (`香港节点`, `美国节点`, `日本节点`, `新加坡节点`). It uses `include-all: true` + `exclude-filter`; its `exclude-filter` must stay the exact union of those region groups' `filter` keywords, including emoji flags and the `(?i)` case-insensitive flag.

## Testing Guidelines

No automated test suite is currently checked in. For configuration edits, validate changed templates with `sift-check`, `mihomo` when available, and manual comparison against `demo/` examples where relevant.

## Commit & Pull Request Guidelines

Recent history mostly follows Conventional Commit style with optional scopes, for example `chore(rules): ...`, `feat(config): ...`, and `refactor(config): ...`. Use concise Chinese or English summaries, and choose scopes such as `config`, `rules`, `docs`, or `scripts`.

Pull requests should describe the routing behavior changed, list validation commands run, and mention compatibility risks for existing Mihomo clients. For template changes, state whether the change affects `Full.yaml`, `Core.yaml`, `Nano.yaml`, or docs/check tooling. Include screenshots only when UI panel behavior or strategy-group ordering is relevant.

## Security & Configuration Tips

Do not commit personal proxy nodes, subscription URLs, credentials, API tokens, or generated configs containing private endpoints. Keep `Full.yaml`, `Core.yaml`, and `Nano.yaml` as reusable public templates. Do not vendor third-party icon assets or rulesets unless their license and attribution requirements are checked and documented; remote icon references currently point to `Koolson/Qure`.
