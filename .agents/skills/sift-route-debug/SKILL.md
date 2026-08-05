---
name: sift-route-debug
description: Validate every Sift template with a pinned Mihomo binary, diagnose RULE-SET routing decisions, and run whole-tree domain route regression. Use when checking whether configs load, investigating why a domain or IP is routed direct/proxy, checking first-match rule attribution, or testing all templates' 分流路径.
---

# sift-route-debug

Use this skill when Sift templates need authoritative Mihomo loading validation, when a domain or IP route needs attribution ("why did this go direct?", "which rule matched?"), or after routing / provider / strategy-group changes.

## Commands

### Complete check (preferred)

```bash
python3 .agents/skills/sift-route-debug/scripts/check.py
```

This single portable command runs pinned Mihomo loading validation for all three templates, refreshes and runs the complete domain route matrix, then runs `git diff --check`. Use `--quick` to reuse existing route caches.

### Validate configs only

```bash
python3 .agents/skills/sift-route-debug/scripts/validate_configs.py
```

This standard-library-only script discovers all three YAML templates, downloads the pinned official Mihomo release for Windows, Linux, or macOS, verifies the release SHA-256 digest, caches it under `.cache/`, and runs each template with an isolated home directory. On amd64 it prefers the portable `compatible`/`v1` build and automatically refreshes a cached binary that cannot run on the current CPU:

```bash
mihomo -t -d <isolated-cache> -f <template>
```

Use an existing binary or a different release only when needed:

```bash
python3 .agents/skills/sift-route-debug/scripts/validate_configs.py --mihomo /path/to/mihomo
python3 .agents/skills/sift-route-debug/scripts/validate_configs.py --version v1.19.29
```

### Single domain / IP

```bash
.agents/skills/sift-route-debug/scripts/explain_route.py rules/full.yaml example.com
.agents/skills/sift-route-debug/scripts/explain_route.py rules/core.yaml play.googleapis.com
.agents/skills/sift-route-debug/scripts/update_cache.py rules/full.yaml
.agents/skills/sift-route-debug/scripts/update_cache.py rules/core.yaml
```

### Whole-tree domain matrix (preferred after template edits)

```bash
# Refresh all rule caches, then matrix + assertions (3 templates)
bash .agents/skills/sift-route-debug/scripts/matrix_route.sh

# Or call Python directly (no auto geo bootstrap)
python3 .agents/skills/sift-route-debug/scripts/matrix_route.py --update-cache

# Matrix only (no FAIL/WARN expectations)
python3 .agents/skills/sift-route-debug/scripts/matrix_route.py --update-cache --no-assert

# Subset of templates / extra probes
python3 .agents/skills/sift-route-debug/scripts/matrix_route.py --update-cache \
  --templates HY-f HY-c HY-n \
  --domain googleapis.cn --domain challenges.cloudflare.com
```

The matrix runs fully in-process via `RouteEngine`: provider files are indexed once (exact/suffix/keyword/regex), and no per-cell Python subprocess is spawned. Cache refresh (`--update-cache` / `update_cache.py`) deduplicates URLs across templates and downloads/decodes MRS in parallel (`--jobs N`, default 12). The shell wrapper remains a Linux convenience only.

Exit codes: `0` = all FAIL-level expectations passed (or `--no-assert`); `1` = at least one FAIL.

## Workflow

### Single diagnosis

1. Run `explain_route.py <template> <domain-or-ip>`.
2. If it reports missing cached rules, run `update_cache.py <template>` and retry.
3. Treat the target YAML as the only source of truth:
   - read `rule-providers.*.url` and `behavior` from the selected template.
   - do not hardcode an upstream in scripts or reasoning.
   - binary MRS providers are decoded into a local text diagnostic cache by
     `update_cache.py`, using `mihomo convert-ruleset` when available or the bundled
     Node.js decoder (with `node:zlib` Zstandard support) otherwise; the
     template-declared MRS remains the source of truth.
4. Domain diagnosis does not resolve DNS. Mention that runtime may later hit an IP provider after DNS resolution.
5. For IP input, diagnose IP providers only.
6. If a misroute is confirmed, update `matrix_route.py` expectations when the product contract changes.

### Whole-tree regression (after multi-template routing changes)

1. Run `python3 .agents/skills/sift-route-debug/scripts/validate_configs.py`; every template must pass Mihomo's native parser.
2. Run `python3 .agents/skills/sift-route-debug/scripts/matrix_route.py --update-cache` to refresh caches and test domain routing.
3. Read the 3-column matrix and ASSERTIONS section. FAIL = product contract broken; WARN = known design variance.
4. Domain matrix is **domain-first-match only**:
   - Any `GEOIP` rules are skipped for domain probes.
   - Providers with `behavior: ipcidr` are skipped for domain probes (runtime may still match after DNS).

## Matrix labels

| Label | Template |
| --- | --- |
| `HY-f` / `HY-c` / `HY-n` | `rules/full.yaml · rules/core.yaml · rules/nano.yaml` |

## Built-in probes (default)

Private, Google / `.cn` Google APIs, YouTube, CF challenge, AI, Netflix/Disney+/Spotify/TikTok/Twitch/Hulu, Apple/Microsoft/OneDrive, GitHub/social, domestic CN sites. See `DEFAULT_DOMAINS` in `scripts/matrix_route.py`.

## Built-in expectations (contract highlights)

Keep these aligned with `AGENTS.md` / `README.md` when routing design changes:

| Area | Contract (summary) |
| --- | --- |
| **Google/Play anchors** | **`googleapis.cn`** + **`play.googleapis.com`**: Full → `谷歌服务`; Core/Nano → `节点选择`. Must not fall through to broad CN direct. DNS half of the same contract is Full/Core `rule-set:proxy` fake-IP whitelist. |
| Other Google | `www.google.com` same policy split as anchors (Full `谷歌服务` / Core-Nano `节点选择`) |
| CF challenge | Full binds `challenges.cloudflare.com` to `流媒体` via the DustinWin `media` set. |
| Full AI | `chatgpt.com` → `AI` |
| Full streaming | YouTube and the DustinWin `media` set → `流媒体` |
| Full brands | icloud → `苹果服务`, office → `微软服务` |
| Core brands | Apple → `苹果服务`, Microsoft → `微软服务` (default `直连`) |
| GitHub | Dedicated `GitHub` group on Full/Core (default `节点选择`); Nano → `节点选择`/`漏网之鱼` |
| OneDrive | Dedicated `OneDrive` group on Full/Core (default `节点选择`); Nano → `节点选择` |
| Domestic | baidu/qq/taobao/bilibili → `直连` on all three |
| Private | localhost → `DIRECT` |

Display-only (not FAIL/WARN):

- `gstatic.cn` may → `直连` through `cn-lite`; it is **not** a Play/API contract anchor.

Edit `default_expectations()` in `matrix_route.py` when the product contract changes.

## Reading single `explain_route` results

`explain_route.py` prints the first matching template rule in Mihomo rule order, including the provider name, provider source, behavior, and matched provider entry.

Common Sift cases to call out:

- `proxy` is the explicit non-CN layer after service/brand rules and before `cn-lite`; Full also has `google` → `谷歌服务` before `proxy`.
- Full's DustinWin `media` domain set intentionally binds `+.challenges.cloudflare.com` to `流媒体` — CF verification traffic rides the streaming group.
- Core routes Apple and Microsoft rules to separately controllable service groups, both defaulting to `直连`; Full/Core also have dedicated `GitHub` and `OneDrive` groups (default `节点选择`).
- A domain that has no domain-rule match can still route by IP at runtime if DNS resolution produces an IP matched by an IP rule.

`matrix_route.sh` is retained as a Linux convenience wrapper; the Python command is the portable entry point.
