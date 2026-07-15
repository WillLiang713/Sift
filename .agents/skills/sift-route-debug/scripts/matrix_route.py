#!/usr/bin/env python3
"""Regression matrix: first-match domain routes for all Sift templates under rules/.

Uses template-declared providers / geox-url only (via explain_route helpers).
Domain-only diagnosis: ACL4SSR GEOIP rules are skipped; IP providers with
behavior ipcidr are skipped for domain input.

Exit 0 if all FAIL-level expectations pass; exit 1 on any FAIL.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

# scripts/ -> sift-route-debug -> skills -> .agents -> repo root
REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import explain_route as er  # noqa: E402

DEFAULT_CACHE = REPO_ROOT / ".cache" / "sift-route-debug"
EXPLAIN = SCRIPTS / "explain_route.py"
UPDATE_CACHE = SCRIPTS / "update_cache.py"

TEMPLATES: Dict[str, str] = {
    "DW-f": "rules/DustinWin-full.yaml",
    "DW-c": "rules/DustinWin-core.yaml",
    "DW-n": "rules/DustinWin-nano.yaml",
    "MC-f": "rules/MetaCubeX-full.yaml",
    "MC-c": "rules/MetaCubeX-core.yaml",
    "MC-n": "rules/MetaCubeX-nano.yaml",
    "AC-f": "rules/ACL4SSR-full.yaml",
    "AC-c": "rules/ACL4SSR-core.yaml",
    "AC-n": "rules/ACL4SSR-nano.yaml",
}

# Canonical probe domains for whole-tree regression after routing design changes.
DEFAULT_DOMAINS: List[str] = [
    "localhost",
    "googleapis.cn",
    "gstatic.cn",
    "www.google.com",
    "play.googleapis.com",
    "www.youtube.com",
    "scholar.google.com",
    "challenges.cloudflare.com",
    "www.cloudflare.com",
    "chatgpt.com",
    "openai.com",
    "claude.ai",
    "www.netflix.com",
    "www.disneyplus.com",
    "open.spotify.com",
    "www.tiktok.com",
    "www.twitch.tv",
    "www.hulu.com",
    "www.apple.com",
    "icloud.com",
    "www.microsoft.com",
    "office.com",
    "onedrive.live.com",
    "github.com",
    "x.com",
    "discord.com",
    "web.telegram.org",
    "reddit.com",
    "www.baidu.com",
    "www.qq.com",
    "www.taobao.com",
    "www.bilibili.com",
]

SHORT = {
    "节点选择": "节点",
    "全球直连": "直连",
    "漏网之鱼": "漏网",
    "苹果服务": "苹果",
    "微软服务": "微软",
    "谷歌服务": "谷歌",
    "游戏平台": "游戏",
    "流媒体": "流媒",
    "OneDrive": "OD",
    "Telegram": "TG",
    "DIRECT": "DIR",
    "AI": "AI",
}

ALL = list(TEMPLATES.keys())
FULLS = ["DW-f", "MC-f", "AC-f"]
CORES = ["DW-c", "MC-c", "AC-c"]
NANOS = ["DW-n", "MC-n", "AC-n"]

# (domain, template_labels, allowed_policies, level)
# level: "FAIL" fails the run; "WARN" is informational only.
Expectation = Tuple[str, Sequence[str], Set[str], str]


def default_expectations() -> List[Expectation]:
    """Product-contract expectations for the current Sift routing design."""
    exp: List[Expectation] = []

    exp.append(("localhost", ALL, {"DIRECT"}, "FAIL"))

    # Google .cn global services must not fall through to broad CN direct on Full.
    exp.append(("googleapis.cn", ["DW-f", "MC-f", "AC-f"], {"谷歌服务"}, "FAIL"))
    exp.append(("googleapis.cn", ["DW-c", "DW-n", "MC-c", "MC-n", "AC-c", "AC-n"], {"节点选择"}, "FAIL"))

    exp.append(("www.google.com", FULLS, {"谷歌服务"}, "FAIL"))
    exp.append(("www.google.com", CORES + NANOS, {"节点选择"}, "FAIL"))

    exp.append(("www.youtube.com", ["MC-f", "AC-f"], {"流媒体"}, "FAIL"))
    # DustinWin Full streaming is IP-heavy (mediaip); YouTube domain often hits proxy.
    exp.append(("www.youtube.com", ["DW-f"], {"谷歌服务", "节点选择", "流媒体"}, "WARN"))
    exp.append(
        ("www.youtube.com", ["DW-c", "DW-n", "MC-c", "MC-n", "AC-c", "AC-n"], {"节点选择", "漏网之鱼"}, "FAIL")
    )

    # CF challenge must not bind to 流媒体 (ACL Full uses brand packs, not ProxyMedia).
    exp.append(("challenges.cloudflare.com", ALL, {"节点选择", "漏网之鱼"}, "FAIL"))

    exp.append(("chatgpt.com", FULLS, {"AI"}, "FAIL"))
    exp.append(("chatgpt.com", CORES, {"节点选择"}, "FAIL"))
    exp.append(("chatgpt.com", ["DW-n", "MC-n"], {"节点选择"}, "FAIL"))
    exp.append(("chatgpt.com", ["AC-n"], {"节点选择", "漏网之鱼"}, "WARN"))

    exp.append(("www.netflix.com", ["AC-f", "MC-f"], {"流媒体"}, "FAIL"))
    exp.append(("www.netflix.com", ["DW-f"], {"节点选择", "流媒体", "漏网之鱼"}, "WARN"))

    for media in ("www.disneyplus.com", "open.spotify.com", "www.tiktok.com"):
        exp.append((media, ["AC-f"], {"流媒体"}, "FAIL"))

    for domestic in ("www.baidu.com", "www.qq.com", "www.taobao.com", "www.bilibili.com"):
        exp.append((domestic, ALL, {"全球直连"}, "FAIL"))

    exp.append(("github.com", ALL, {"节点选择", "漏网之鱼"}, "FAIL"))

    exp.append(("icloud.com", CORES, {"全球直连"}, "FAIL"))
    exp.append(("office.com", CORES, {"全球直连"}, "FAIL"))
    exp.append(("icloud.com", FULLS, {"苹果服务"}, "FAIL"))
    exp.append(("office.com", FULLS, {"微软服务"}, "FAIL"))

    return exp


def explain_ruleset_domain(
    template: str, domain: str, cache_dir: Path
) -> Dict[str, Optional[str]]:
    """Domain first-match for RULE-SET templates; skip GEOIP and ipcidr providers."""
    path = REPO_ROOT / template
    t = er.parse_template(path)
    for rule in t.rules:
        if not rule.parts:
            continue
        kind = rule.parts[0].upper()
        if kind == "MATCH":
            return {
                "policy": er.policy_from_rule(rule.parts),
                "rule": rule.raw,
            }
        if kind == "GEOIP":
            continue
        if kind != "RULE-SET" or len(rule.parts) < 3:
            continue
        provider = t.providers.get(rule.parts[1])
        if not provider:
            continue
        if provider.behavior.lower() == "ipcidr":
            continue
        provider_file = er.resolve_provider_file(provider, cache_dir)
        if not provider_file:
            continue
        for _, entry in er.iter_provider_lines(provider_file):
            matched = er.match_domain_entry(domain, entry)
            if matched:
                return {
                    "policy": er.policy_from_rule(rule.parts),
                    "rule": rule.raw,
                    "match": matched,
                }
    return {"policy": None, "rule": None}


def explain_one(
    template: str, domain: str, cache_dir: Path, geo_bin: str
) -> Dict[str, Optional[str]]:
    cmd = [
        sys.executable,
        str(EXPLAIN),
        str(REPO_ROOT / template),
        domain,
        "--cache-dir",
        str(cache_dir),
        "--geo-bin",
        geo_bin,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    out = proc.stdout + proc.stderr
    if "mixed RULE-SET" in out:
        return explain_ruleset_domain(template, domain, cache_dir)
    policy = re.search(r"^\s*policy:\s*(.+)$", out, re.M)
    rule = re.search(r"^\s*template rule:\s*(.+)$", out, re.M)
    return {
        "policy": policy.group(1).strip() if policy else None,
        "rule": rule.group(1).strip() if rule else None,
        "raw": out[:400] if proc.returncode != 0 else None,
    }


def update_all_caches(cache_dir: Path) -> None:
    for rel in TEMPLATES.values():
        print(f"== update_cache {rel} ==")
        proc = subprocess.run(
            [
                sys.executable,
                str(UPDATE_CACHE),
                str(REPO_ROOT / rel),
                "--cache-dir",
                str(cache_dir),
            ],
            cwd=str(REPO_ROOT),
        )
        if proc.returncode != 0:
            print(f"  [WARN] update_cache exited {proc.returncode} for {rel}", file=sys.stderr)


def ensure_geo_bin(preferred: str) -> str:
    """Return a usable geo binary path; try PATH then repo .cache/tools/geo."""
    if preferred != "geo":
        return preferred
    which = subprocess.run(["bash", "-lc", "command -v geo"], capture_output=True, text=True)
    if which.returncode == 0 and which.stdout.strip():
        return which.stdout.strip()
    local = REPO_ROOT / ".cache" / "tools" / "geo"
    if local.is_file() and os.access(local, os.X_OK):
        return str(local)
    return preferred


# late import for ensure_geo
import os  # noqa: E402


def run_expectations(
    results: Dict[str, Dict[str, Dict[str, Optional[str]]]],
    expectations: Sequence[Expectation],
) -> Tuple[int, int]:
    fails = 0
    warns = 0
    print()
    print("=" * 130)
    print("ASSERTIONS")
    print("-" * 130)
    for domain, labs, allowed, level in expectations:
        if domain not in results:
            print(f"  [WARN] skip expectation for missing probe domain {domain}")
            warns += 1
            continue
        for lab in labs:
            if lab not in results[domain]:
                print(f"  [WARN] skip {domain} @ {lab}: template not run")
                warns += 1
                continue
            pol = results[domain][lab].get("policy")
            if pol not in allowed:
                tag = level
                if level == "FAIL":
                    fails += 1
                else:
                    warns += 1
                print(f"  [{tag}] {domain} @ {lab}: got {pol!r}, want {sorted(allowed)}")
                detail = results[domain][lab]
                if detail.get("rule"):
                    print(f"         rule={detail.get('rule')}")
            else:
                print(f"  [OK] {domain} @ {lab}: {pol}")
    return fails, warns


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=DEFAULT_CACHE,
        help="Route-debug cache directory",
    )
    parser.add_argument(
        "--update-cache",
        action="store_true",
        help="Run update_cache.py for every template before testing",
    )
    parser.add_argument(
        "--geo-bin",
        default="geo",
        help="Geo CLI for MetaCubeX templates (default: geo on PATH or .cache/tools/geo)",
    )
    parser.add_argument(
        "--domain",
        action="append",
        dest="domains",
        help="Probe domain (repeatable). Default: built-in regression set",
    )
    parser.add_argument(
        "--no-assert",
        action="store_true",
        help="Only print the matrix; do not evaluate expectations",
    )
    parser.add_argument(
        "--templates",
        nargs="*",
        choices=list(TEMPLATES.keys()),
        help="Subset of template labels (default: all nine)",
    )
    args = parser.parse_args()

    cache_dir = args.cache_dir
    if not cache_dir.is_absolute():
        cache_dir = REPO_ROOT / cache_dir

    geo_bin = ensure_geo_bin(args.geo_bin)
    labels = args.templates or list(TEMPLATES.keys())
    domains = args.domains or list(DEFAULT_DOMAINS)

    if args.update_cache:
        update_all_caches(cache_dir)

    results: Dict[str, Dict[str, Dict[str, Optional[str]]]] = {}
    for domain in domains:
        results[domain] = {}
        for lab in labels:
            rel = TEMPLATES[lab]
            results[domain][lab] = explain_one(rel, domain, cache_dir, geo_bin)

    print("=" * 130)
    print(f"{'domain':<28}" + "".join(f"{lab:<8}" for lab in labels))
    print("-" * 130)
    for domain in domains:
        cells = []
        for lab in labels:
            pol = results[domain][lab].get("policy") or "?"
            cells.append(f"{SHORT.get(pol, (pol or '?')[:6]):<8}")
        print(f"{domain:<28}" + "".join(cells))

    if args.no_assert:
        return 0

    expectations = default_expectations()
    fails, warns = run_expectations(results, expectations)

    print()
    print("=" * 130)
    print(f"SUMMARY: {fails} FAIL, {warns} WARN")
    print("Notes:")
    print("  - Domain-only diagnosis; GEOIP / pure IP providers skipped for domain probes.")
    print("  - MetaCubeX requires geo CLI (PATH or .cache/tools/geo).")
    print(f"  - geo-bin={geo_bin}")
    if fails:
        print("FAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
