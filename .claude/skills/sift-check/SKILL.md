---
name: sift-check
description: Validate the Sift Mihomo templates (Full.yaml / Core.yaml / Nano.yaml) against project invariants — strategy-group & rule-set referential integrity, the ShellCrash geosite/geoip URL constraint, node-free rules, DNS allowance per template, canonical group scopes, and optional mihomo/yamllint checks. Use before committing template, rule-provider, or documentation changes.
---

# sift-check

Statically validates `Full.yaml`, `Core.yaml`, and `Nano.yaml` against the conventions in `AGENTS.md` (including the ShellCrash geo-keyword constraint). Pure bash + awk, no new dependencies; `mihomo -t` and `yamllint` are used only if those binaries are on PATH.

## Run

```bash
bash .claude/skills/sift-check/check.sh
```

It `cd`s to the repo root, so it can be invoked from anywhere. Exit `0` = PASS, `1` = at least one `[FAIL]`.

## What it checks

Project invariants that `mihomo -t` cannot catch:

- **Referential integrity** — every `proxies:` entry and every rule policy resolves to a defined group or a builtin (`DIRECT`/`REJECT`); every `RULE-SET,<x>` and DNS `rule-set:<x>` resolves to a defined `rule-providers` key.
- **ShellCrash constraint** — no `geosite` / `geoip` substring in any `rule-providers` URL (→ `[FAIL]`). See `AGENTS.md › Rule Sources & ShellCrash Compatibility`.
- **Node-free** — no top-level `proxies:` in any template.
- **DNS scope** — `Full.yaml` and `Core.yaml` may carry top-level `dns:` blocks; `Nano.yaml` must stay DNS-free. DNS `fake-ip-filter` / `nameserver-policy` rule-set refs are integrity-checked and must use `behavior: domain` providers.
- **Canonical groups** — required strategy-group names must be present; Core must not contain service/brand UI groups, region node groups, or the separate `漏网之鱼` group, and Nano must not contain its forbidden Full/Core-only groups.
- **Orphan providers** (`[WARN]`) and **key ≠ file basename** (`[INFO]`, e.g. blackmatrix7 service keys mapping to capitalized upstream paths — informational only).

Toolchain (auto-skipped if not installed): `mihomo -t -f`, `yamllint -d relaxed`, `git diff --check`.

## Acting on results

- `PASS` → invariants hold; safe to commit.
- Any `[FAIL]` → read the message, fix the named file, re-run until PASS. Do **not** commit while failing.
- `[WARN]` / `[INFO]` don't fail the run but should be eyeballed.

## Keeping the contract in sync

The canonical **required** / **forbidden** group sets live at the top of `check.sh` (`FULL_REQ`, `CORE_REQ`, `CORE_FORB`, `NANO_REQ`, `NANO_FORB`). When a strategy group is intentionally added, renamed, or removed, update those lists in the same commit so the checker stays accurate.
