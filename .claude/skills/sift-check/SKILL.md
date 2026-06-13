---
name: sift-check
description: Validate the Sift Mihomo templates (Full.yaml / Nano.yaml) against project invariants — strategy-group & rule-set referential integrity, the ShellCrash geosite/geoip URL constraint, node-free / no-DNS rules, Nano⊆Full scope, and canonical group names. Use when asked to validate / lint / check the config, or before committing template or rule-provider edits.
---

# sift-check

Statically validates `Full.yaml` and `Nano.yaml` against the conventions in `AGENTS.md` (including the ShellCrash geo-keyword constraint). Pure bash + awk, no new dependencies; `mihomo -t` and `yamllint` are used only if those binaries are on PATH.

## Run

```bash
bash .claude/skills/sift-check/check.sh
```

It `cd`s to the repo root, so it can be invoked from anywhere. Exit `0` = PASS, `1` = at least one `[FAIL]`.

## What it checks

Project invariants that `mihomo -t` cannot catch:

- **Referential integrity** — every `proxies:` entry and every rule policy resolves to a defined group or a builtin (`DIRECT`/`REJECT`); every `RULE-SET,<x>` resolves to a defined `rule-providers` key. This is the main payoff: it catches dangling references left behind by the frequent group / rule renames in this repo's history.
- **ShellCrash constraint** — no `geosite` / `geoip` substring in any `rule-providers` URL (→ `[FAIL]`); non-DustinWin sources are flagged for review (→ `[WARN]`). See `AGENTS.md › Rule Sources & ShellCrash Compatibility`.
- **Node-free / DNS-free** — no top-level `proxies:` or `dns:` / `fake-ip`.
- **Canonical groups** — all required strategy-group names are present, and `Nano.yaml` does not contain `Full`-only groups (AI / 流媒体 / 游戏平台 / region groups).
- **Orphan providers** (`[WARN]`) and **key ≠ file basename** (`[INFO]`, e.g. `cn` → `cn-lite.mrs`, a deliberate deviation — informational only).

Toolchain (auto-skipped if not installed): `mihomo -t -f`, `yamllint -d relaxed`, `git diff --check`.

## Acting on results

- `PASS` → invariants hold; safe to commit.
- Any `[FAIL]` → read the message, fix the named file, re-run until PASS. Do **not** commit while failing.
- `[WARN]` / `[INFO]` don't fail the run but should be eyeballed.

## Keeping the contract in sync

The canonical **required** / **forbidden** group sets live at the top of `check.sh` (`FULL_REQ`, `NANO_REQ`, `NANO_FORB`). When a strategy group is intentionally added, renamed, or removed, update those lists in the same commit so the checker stays accurate.
