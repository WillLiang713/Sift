---
name: sift-route-debug
description: Validate every Sift template with a pinned Mihomo binary, diagnose RULE-SET and MetaCubeX GEOSITE/GEOIP routing decisions, and run whole-tree domain route regression. Use when checking whether configs load, investigating why a domain or IP is routed direct/proxy, checking first-match rule attribution, or testing all templates' 分流路径.
---

# sift-route-debug

Use this skill when Sift templates need authoritative Mihomo loading validation, when a domain or IP route needs attribution ("why did this go direct?", "which rule matched?"), or after routing / provider / strategy-group changes.

## Commands

### Complete check (preferred)

```bash
python .agents/skills/sift-route-debug/scripts/check.py
```

This single portable command runs pinned Mihomo loading validation for all 12 templates, refreshes and runs the complete domain route matrix, then runs `git diff --check`. Use `--quick` to reuse existing route caches.

### Validate configs only

```bash
python .agents/skills/sift-route-debug/scripts/validate_configs.py
```

This standard-library-only script discovers all 12 YAML templates, downloads the pinned official Mihomo release for Windows, Linux, or macOS, verifies the release SHA-256 digest, caches it under `.cache/`, and runs each template with an isolated home directory:

```bash
mihomo -t -d <isolated-cache> -f <template>
```

Use an existing binary or a different release only when needed:

```bash
python .agents/skills/sift-route-debug/scripts/validate_configs.py --mihomo /path/to/mihomo
python .agents/skills/sift-route-debug/scripts/validate_configs.py --version v1.19.29
```

### Single domain / IP

```bash
.agents/skills/sift-route-debug/scripts/explain_route.py rules/variants/DustinWin-full.yaml example.com
.agents/skills/sift-route-debug/scripts/explain_route.py rules/variants/MetaCubeX-core.yaml play.googleapis.com
.agents/skills/sift-route-debug/scripts/update_cache.py rules/variants/DustinWin-full.yaml
.agents/skills/sift-route-debug/scripts/update_cache.py rules/variants/MetaCubeX-full.yaml
```

### Whole-tree domain matrix (preferred after template edits)

```bash
# Refresh all rule/geodata caches, then matrix + assertions (12 templates)
bash .agents/skills/sift-route-debug/scripts/matrix_route.sh

# Or call Python directly (no auto geo bootstrap)
python .agents/skills/sift-route-debug/scripts/matrix_route.py --update-cache

# Matrix only (no FAIL/WARN expectations)
python .agents/skills/sift-route-debug/scripts/matrix_route.py --update-cache --no-assert

# Subset of templates / extra probes
python .agents/skills/sift-route-debug/scripts/matrix_route.py --update-cache \
  --templates HY-f HY-c HY-n \
  --domain googleapis.cn --domain challenges.cloudflare.com
```

`matrix_route.py` resolves MetaCubeX `geo` from PATH or downloads the official v1.1 build for the current platform into `.cache/tools/geo-bin/`. The matrix itself runs fully in-process via `RouteEngine`: provider files are indexed once (exact/suffix/keyword/regex), MetaCubeX `geo look` results are shared across MC templates and prefetched in parallel, and no per-cell Python subprocess is spawned. The shell wrapper remains a Linux convenience only.

Exit codes: `0` = all FAIL-level expectations passed (or `--no-assert`); `1` = at least one FAIL.

## Workflow

### Single diagnosis

1. Run `explain_route.py <template> <domain-or-ip>`.
2. If it reports missing cached rules, run `update_cache.py <template>` and retry.
3. Treat the target YAML as the only source of truth:
   - DustinWin and ACL4SSR templates read `rule-providers.*.url` and `behavior`.
   - MetaCubeX templates read `geox-url.geosite`, `geox-url.geoip`, and `geox-url.mmdb`.
   - do not hardcode MetaCubeX or any other upstream in scripts or reasoning.
   - binary MRS providers are decoded into a local text diagnostic cache by
     `update_cache.py`, using `mihomo convert-ruleset` when available or the bundled
     Node.js decoder (with `node:zlib` Zstandard support) otherwise; the
     template-declared MRS remains the source of truth.
4. For domain input, MetaCubeX diagnosis defaults to GeoSite only and does not resolve DNS. Mention that runtime may later hit `GEOIP` after DNS resolution.
5. For IP input, diagnose IP providers or `GEOIP` rules only.
6. If a misroute is confirmed, update `matrix_route.py` expectations when the product contract changes.

### Whole-tree regression (after multi-template routing changes)

1. Run `python .agents/skills/sift-route-debug/scripts/validate_configs.py`; every template must pass Mihomo's native parser.
2. Run `python .agents/skills/sift-route-debug/scripts/matrix_route.py --update-cache` to refresh caches and test domain routing.
3. Read the 12-column matrix and ASSERTIONS section. FAIL = product contract broken; WARN = known design variance.
4. Domain matrix is **domain-first-match only**:
   - Any `GEOIP` rules are skipped for domain probes.
   - Providers with `behavior: ipcidr` are skipped for domain probes (runtime may still match after DNS).

## Matrix labels

| Label | Template |
| --- | --- |
| `HY-f` / `HY-c` / `HY-n` | `rules/full.yaml · rules/core.yaml · rules/nano.yaml` (hybrid primary) |
| `DW-f` / `DW-c` / `DW-n` | `rules/variants/DustinWin-{full,core,nano}.yaml` |
| `MC-f` / `MC-c` / `MC-n` | `rules/variants/MetaCubeX-{full,core,nano}.yaml` |
| `AC-f` / `AC-c` / `AC-n` | `rules/variants/ACL4SSR-{full,core,nano}.yaml` |

## Built-in probes (default)

Private, advertising (`doubleclick` / `googlesyndication`), Google / `.cn` Google APIs, YouTube, CF challenge, AI, Netflix/Disney+/Spotify/TikTok/Twitch/Hulu, Apple/Microsoft/OneDrive, GitHub/social, domestic CN sites. See `DEFAULT_DOMAINS` in `scripts/matrix_route.py`.

## Built-in expectations (contract highlights)

Keep these aligned with `AGENTS.md` / `README.md` when routing design changes:

| Area | Contract (summary) |
| --- | --- |
| Advertising | `ad.doubleclick.net` / `pagead2.googlesyndication.com` → `广告拦截` on all 12 templates |
| Full Google | `www.google.com` / `googleapis.cn` → `谷歌服务` on HY/DW/MC/AC Full |
| Core/Nano Google | → `节点选择` (not broad CN direct for `googleapis.cn`) |
| CF challenge | `challenges.cloudflare.com` → `节点选择` or `漏网之鱼`, **never** `流媒体` |
| Full AI | `chatgpt.com` → `AI` |
| Full streaming | MC/AC: YouTube/Netflix → `流媒体`; AC brand packs (not ProxyMedia) |
| Full brands | icloud → `苹果服务`, office → `微软服务` |
| Core brands | full Apple/Microsoft → `全球直连` |
| Domestic | baidu/qq/taobao/bilibili → `全球直连` on all 12 |
| Private | localhost → `DIRECT` |

WARN-level examples (do not treat as hard failures unless design changes):

- DustinWin Full YouTube/Netflix often → `节点选择` (domain media light; `mediaip` is IP).
- ACL4SSR Nano may send some overseas hosts to `漏网之鱼` (narrow ProxyLite).
- DustinWin Core/Nano `gstatic.cn` may → `全球直连` via `cn-lite` `+.cn` (no Google classical list).

Edit `default_expectations()` in `matrix_route.py` when the product contract changes.

## Reading single `explain_route` results

`explain_route.py` prints the first matching template rule in Mihomo rule order. For DustinWin and ACL4SSR templates it includes the provider name, provider source, behavior, and matched provider entry. For MetaCubeX templates it includes matched GeoSite/GeoIP tags from the configured geo database and the first matching `GEOSITE`/`GEOIP` rule.

Common Sift cases to call out:

- DustinWin: `proxy` is the explicit non-CN layer after service/brand rules and before `cn-lite`; Full also has blackmatrix7 `google` → `谷歌服务` before `proxy`.
- MetaCubeX Full: `GEOSITE,google` → `谷歌服务` before `geolocation-!cn` / `cn`; Core/Nano: `google` → `节点选择` between `geolocation-!cn` and `cn`.
- ACL4SSR Full: streaming brand packs (YouTube/Netflix/NetflixIP/DisneyPlus/Spotify/TikTok) → `流媒体`; do not re-add `ProxyMedia` (CF challenge pollution).
- Core intentionally routes full Apple and Microsoft rules to `全球直连`.
- A domain that has no domain-rule match can still route by IP at runtime if DNS resolution produces an IP matched by an IP rule.

## MetaCubeX geo CLI

Geodata diagnosis uses [MetaCubeX/geo](https://github.com/MetaCubeX/geo). `matrix_route.py` bootstraps it automatically; manual installation is optional:

```bash
# optional manual install
mkdir -p .cache/tools
curl -fsSL https://github.com/MetaCubeX/geo/releases/download/v1.1/geo-linux-amd64 -o .cache/tools/geo
chmod +x .cache/tools/geo
export PATH="$PWD/.cache/tools:$PATH"
```

`matrix_route.sh` is retained as a Linux convenience wrapper; the Python command is the portable entry point.
