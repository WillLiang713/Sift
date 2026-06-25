# Repository Guidelines

## Project Structure & Module Organization

This repository is a compact Mihomo configuration template project.

- `Full.yaml` is the full template and should remain node-free; it now also carries a top-level `dns:` block (fake-ip + DustinWin `fakeip-filter` and domestic direct rule sets returning real IP, with DustinWin-style leak-prevention: `respect-rules` + DoH `nameserver`). It keeps AI, streaming, gaming platform, Apple, Microsoft, OneDrive, and region node strategy groups. Rule sets come from [DustinWin/ruleset_geodata](https://github.com/DustinWin/ruleset_geodata), except the overseas Apple/Microsoft/OneDrive sets, which come from [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) (DustinWin publishes none) — all wired as `classical`/`text` `.list` providers for consistency: `apple` ← `rule/Clash/Apple/Apple.list`, `microsoft` ← `rule/Clash/Microsoft/Microsoft.list`, `onedrive` ← `rule/Clash/OneDrive/OneDrive.list`. URL paths are free of `geosite`/`geoip`.
- `Nano.yaml` is the nano template and should remain node-free and DNS-free; it keeps only `手动切换`, `自动测速`, `全球直连`, and `漏网之鱼`. All rule sets are from DustinWin.
- `scripts/convert.js` contains the JavaScript operator for creating chained proxy nodes from `relay` and `landing` arguments.
- `demo/` stores example Mihomo YAML files used for reference and manual comparison, including legacy ACL4SSR-based configurations.
- `ruleset/` stores remotely cached rule-set files (mainly DustinWin MRS, plus the blackmatrix7 overseas Apple/Microsoft/OneDrive sets, all classical `.list`).
- `README.md` documents user-facing behavior and should be updated when routing logic or template selection changes.
- `LICENSE` covers this repository's own template and script content; remotely referenced icons, demo rules, and other third-party resources remain under their upstream terms.

## Rule Sources & ShellCrash Compatibility

Remote rule sets come from [DustinWin/ruleset_geodata](https://github.com/DustinWin/ruleset_geodata) by default; the exceptions are the overseas Apple/Microsoft/OneDrive sets, taken from [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) because DustinWin publishes none. All are wired as `classical`/`text` `.list` providers (`apple` ← `rule/Clash/Apple/Apple.list`, `microsoft` ← `rule/Clash/Microsoft/Microsoft.list`, `onedrive` ← `rule/Clash/OneDrive/OneDrive.list`) for a single consistent pattern. Microsoft and OneDrive *require* classical: their lists cover flagship domains (`microsoft.com`, `1drv.ms`, …) only via `DOMAIN-KEYWORD`, and the MRS `domain` format cannot store keyword rules, so the MRS builds would silently drop them. Apple could have used its MRS build (`Apple_domain.mrs` — flagship `apple.com` is an explicit `DOMAIN-SUFFIX`) but is unified to `.list` to match; the classical lists also bring Apple's `IP-CIDR,…,no-resolve` ranges and OneDrive's `PROCESS-NAME` rules. All blackmatrix7 paths are free of `geosite`/`geoip`. Regardless of source, rule-provider URLs must avoid the substrings `geosite` and `geoip` anywhere in their paths. Rule order matters: the OneDrive rule must precede the Microsoft rule (OneDrive domains also live in Microsoft's list), and the Microsoft rule must sit after AI (its broad `microsoft` keyword would otherwise swallow `copilot.microsoft.com`). ShellCrash scans rule-provider URLs and treats those keywords as a signal that the Geo databases (`geoip.metadb` / `geosite.dat`) are required, which triggers extra Geo-data downloads and checks that slow down or disrupt startup. DustinWin's MRS paths do not contain those keywords, so startup stays clean; MetaCubeX `meta-rules-dat` URLs (for example `.../geo/geosite/...` or `.../geoip/...`) do contain them and trigger the misdetection. Do not switch rule-provider URLs to MetaCubeX even when the rule content is equivalent — keep DustinWin, or another source whose URL path is free of those keywords. The `fakeip-filter` provider (DustinWin, `domain`/`mrs`) is the lone provider referenced only by `dns.fake-ip-filter` (not by any `rules` entry); domestic direct providers may be referenced by both `rules` and `dns.fake-ip-filter`. sift-check counts a `rule-set:` reference inside the `dns:` block as usage, so DNS-only providers are not flagged as orphans.

## Build, Test, and Development Commands

There is no package manager manifest and no generated build step. Use lightweight validation before committing:

- `bash .claude/skills/sift-check/check.sh` (or `/sift-check` in Claude Code) checks project invariants — strategy-group / rule-set referential integrity, the ShellCrash `geosite`/`geoip` URL constraint, node-free rules (Full may carry a top-level `dns:`, validated for `fake-ip-filter` rule-set integrity; Nano must stay DNS-free), and `Nano` ⊆ `Full` scope — and folds in `mihomo -t` / `yamllint` when those are installed. Run it before committing template or rule-provider edits.
- `node --check scripts/convert.js` verifies JavaScript syntax without executing the operator.
- `mihomo -t -f Full.yaml` and `mihomo -t -f Nano.yaml` validate the templates when the Mihomo binary is installed locally.
- `yamllint Full.yaml Nano.yaml demo/*.yaml` checks YAML formatting when `yamllint` is available.
- `git diff --check` catches trailing whitespace and common patch formatting issues.

## Coding Style & Naming Conventions

Keep YAML indentation at two spaces and group rules by routing intent, with short comments explaining each block. Preserve established Chinese strategy-group names such as `手动切换`, `自动测速`, `漏网之鱼`, `节点选择`, `AI`, `流媒体`, and `游戏平台` unless a routing change requires renaming them. Keep `Nano.yaml` intentionally smaller than `Full.yaml`; do not add AI, entertainment, gaming, or region node groups there unless the template goal is explicitly changed. Keep each `rule-providers` key synchronized with the upstream rule-set file basename, for example use `google-cn` for `google-cn.mrs` and `ai` for `ai.mrs` instead of display-style names; `cn` is the deliberate exception and maps to `cn-lite.mrs` to preserve existing `RULE-SET,cn` references while using the lighter domestic set. For overlapping rules, place the more specific or higher-intent rule first. Top-level scenario `select` groups should keep a consistent candidate order and use `include-all: true` so each scenario can directly select a concrete node without adding one-off duplicate groups such as `开发自建节点`. In JavaScript, use two-space indentation, semicolons, `const`/`let`, and small helper functions as shown in `scripts/convert.js`. Prefer descriptive argument aliases and avoid changing existing aliases unless backward compatibility is intentionally broken.

## Testing Guidelines

No automated test suite is currently checked in. For configuration edits, validate changed templates with Mihomo and manually compare behavior against `demo/` examples where relevant. For `scripts/convert.js`, run `node --check` and test the operator in the target subscription-conversion environment with both required arguments:

```text
relay=<中转节点名>&landing=<落地节点名>&name=<自定义名称>
```

## Commit & Pull Request Guidelines

Recent history mostly follows Conventional Commit style with optional scopes, for example `chore(rules): ...`, `feat(config): ...`, and `refactor(config): ...`. Use concise Chinese or English summaries, and choose scopes such as `config`, `rules`, `docs`, or `scripts`.

Pull requests should describe the routing or script behavior changed, list validation commands run, and mention compatibility risks for existing Mihomo clients. For template changes, state whether the change affects `Full.yaml`, `Nano.yaml`, or both. Include screenshots only when UI panel behavior or strategy-group ordering is relevant.

## Security & Configuration Tips

Do not commit personal proxy nodes, subscription URLs, credentials, API tokens, or generated configs containing private endpoints. Keep `Full.yaml` and `Nano.yaml` as reusable public templates. Do not vendor third-party icon assets or rulesets unless their license and attribution requirements are checked and documented; remote icon references currently point mainly to `Koolson/Qure` and `Orz-3/mini`.
