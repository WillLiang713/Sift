#!/usr/bin/env python3
"""Regression matrix: first-match domain routes for all Sift templates under rules/.

Uses template-declared providers only (via explain_route helpers).
Domain-only diagnosis: providers with behavior ipcidr are
skipped for domain input.

Exit 0 if all FAIL-level expectations pass; exit 1 on any FAIL.
"""

from __future__ import annotations

import argparse
import os
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
UPDATE_CACHE = SCRIPTS / "update_cache.py"


def utf8_python_env() -> Dict[str, str]:
    """Return an environment that makes child Python output UTF-8 on Windows."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


WHITELIST = "Sift"
GFWLIST = "Sift-GFW"
FULL = "Sift-Full"

TEMPLATES: Dict[str, str] = {
    WHITELIST: "rules/core.yaml",
    GFWLIST: "rules/gfwlist.yaml",
    FULL: "rules/full.yaml",
}

# Canonical probe domains for whole-tree regression after routing design changes.
DEFAULT_DOMAINS: List[str] = [
    "localhost",
    "ad.doubleclick.net",
    "pagead2.googlesyndication.com",
    "googleapis.cn",
    "gstatic.cn",
    "www.google.com",
    "play.googleapis.com",
    "xn--ngstr-lra8j.com",
    "recaptcha.net",
    "cm.steampowered.com",
    "steamcontent.com",
    "steamserver.net",
    "steamcdn-a.akamaihd.net",
    "st.dl.eccdnx.com",
    "store.steampowered.com",
    "steamcommunity.com",
    "cmp1-hkg1.steamserver.net",
    "45.121.184.5",
    "198.41.192.1",
    "apps.apple.com",
    "download.windowsupdate.com",
    "metacubex.github.io",
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
    "iq.com",
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
    "adobe.com",
    "pool.ntp.org",
    "services.googleapis.cn",
    "192.168.1.1",
    "223.5.5.5",
    "8.8.8.8",
    "149.154.167.50",
    "unlisted-sift-probe-73921.com",
]

SHORT = {
    "节点选择": "节点",
    "全球直连": "直连",
    "漏网之鱼": "漏网",
    "游戏平台": "游戏",
    "流媒体": "流媒",
    "Telegram": "TG",
    "DIRECT": "DIR",
    "AI": "AI",
}

Expectation = Tuple[str, Sequence[str], Set[str], str]


def default_expectations() -> Sequence[Expectation]:
    """Per-template product contract.

    ``Sift`` is the mainland whitelist: private / custom-direct-domain /
    custom-direct-ip / games-cn / cn / cnip / steam-cdn-ip and mainland IPs go
    direct, telegram domain and ``proxy`` go to 节点选择 (telegram before cn),
    AI fall through to 节点选择, everything else is proxied. ``Sift-GFW`` proxies
    ``telegram`` + ``gfw``, everything else goes direct. ``Sift-Full`` uses
    DustinWin service sets plus custom-direct-domain / custom-direct-ip and
    steam-cdn-ip: Custom Direct wins over service groups, CN
    Apple/Microsoft/Google/games go to 全球直连, AI/media/games/Telegram(+IP) to
    theirs, ``proxy`` to 节点选择, MATCH to 漏网之鱼.
    """
    whitelist_direct = ("localhost", "metacubex.github.io", "www.baidu.com", "www.qq.com",
                        "www.taobao.com", "www.bilibili.com", "192.168.1.1", "223.5.5.5",
                        "cm.steampowered.com", "steamcontent.com", "st.dl.eccdnx.com",
                        "cmp1-hkg1.steamserver.net", "45.121.184.5", "198.41.192.1",
                        "adobe.com", "pool.ntp.org", "steamcdn-a.akamaihd.net")
    whitelist_proxy = ("play.googleapis.com", "googleapis.cn", "services.googleapis.cn",
                       "xn--ngstr-lra8j.com", "github.com", "8.8.8.8", "149.154.167.50",
                       "unlisted-sift-probe-73921.com",
                       "store.steampowered.com", "steamcommunity.com", "web.telegram.org")
    whitelist_ai = ("chatgpt.com", "openai.com", "claude.ai")
    gfwlist_direct = ("localhost", "www.baidu.com", "www.qq.com", "www.taobao.com",
                      "www.bilibili.com", "192.168.1.1", "223.5.5.5", "8.8.8.8",
                      "googleapis.cn", "services.googleapis.cn",
                      "unlisted-sift-probe-73921.com",
                      "cm.steampowered.com", "steamcontent.com", "steamserver.net")
    gfwlist_proxy = ("www.google.com", "play.googleapis.com", "github.com", "chatgpt.com",
                     "openai.com", "www.youtube.com", "x.com", "discord.com",
                     "149.154.167.50", "store.steampowered.com", "steamcommunity.com", "web.telegram.org")
    full_groups = (
        ("localhost", "DIRECT"),
        ("www.baidu.com", "全球直连"),
        ("www.qq.com", "全球直连"),
        ("www.bilibili.com", "全球直连"),
        ("223.5.5.5", "全球直连"),
        ("apps.apple.com", "全球直连"),
        ("www.apple.com", "全球直连"),
        ("www.microsoft.com", "全球直连"),
        ("download.windowsupdate.com", "全球直连"),
        ("cmp1-hkg1.steamserver.net", "全球直连"),
        ("45.121.184.5", "全球直连"),
        ("198.41.192.1", "全球直连"),
        ("googleapis.cn", "节点选择"),
        ("www.google.com", "节点选择"),
        ("services.googleapis.cn", "节点选择"),
        ("xn--ngstr-lra8j.com", "节点选择"),
        ("gstatic.cn", "全球直连"),
        ("www.youtube.com", "流媒体"),
        ("iq.com", "全球直连"),
        ("chatgpt.com", "AI"),
        ("github.com", "节点选择"),
        ("web.telegram.org", "Telegram"),
        ("149.154.167.50", "Telegram"),
        ("icloud.com", "节点选择"),
        ("office.com", "节点选择"),
        ("x.com", "节点选择"),
        ("discord.com", "节点选择"),
        ("8.8.8.8", "漏网之鱼"),
        ("unlisted-sift-probe-73921.com", "漏网之鱼"),
        ("adobe.com", "全球直连"),
        ("pool.ntp.org", "全球直连"),
        ("steamcdn-a.akamaihd.net", "全球直连"),
    )
    return ([(d, [WHITELIST], {"DIRECT"}, "FAIL") for d in whitelist_direct]
            + [(d, [WHITELIST], {"节点选择"}, "FAIL") for d in whitelist_proxy]
            + [(d, [WHITELIST], {"节点选择"}, "FAIL") for d in whitelist_ai]
            + [(d, [GFWLIST], {"DIRECT"}, "FAIL") for d in gfwlist_direct]
            + [(d, [GFWLIST], {"节点选择"}, "FAIL") for d in gfwlist_proxy]
            + [(d, [FULL], {policy}, "FAIL") for d, policy in full_groups])


def update_all_caches(cache_dir: Path, labels: Sequence[str]) -> bool:
    """Refresh rule caches once for all selected templates (URL-deduped, parallel)."""
    templates = [str(REPO_ROOT / TEMPLATES[label]) for label in labels]
    if not templates:
        return True
    proc = subprocess.run(
        [
            sys.executable,
            str(UPDATE_CACHE),
            *templates,
            "--cache-dir",
            str(cache_dir),
        ],
        cwd=str(REPO_ROOT),
        env=utf8_python_env(),
    )
    if proc.returncode != 0:
        print(
            f"  [FAIL] update_cache exited {proc.returncode} for {len(templates)} template(s)",
            file=sys.stderr,
        )
        return False
    return True


def run_matrix(
    engine: er.RouteEngine,
    labels: Sequence[str],
    domains: Sequence[str],
) -> Dict[str, Dict[str, Dict[str, Optional[str]]]]:
    """Evaluate every domain/template cell in-process with shared indexes."""
    results: Dict[str, Dict[str, Dict[str, Optional[str]]]] = {}
    template_paths = {label: (REPO_ROOT / TEMPLATES[label]) for label in labels}

    # Warm templates and domain provider indexes once so lookups stay O(suffixes).
    for path in template_paths.values():
        template = engine.load_template(path)
        for provider in template.providers.values():
            if provider.behavior.lower() == "ipcidr":
                continue
            provider_file = er.resolve_provider_file(provider, engine.cache_dir)
            if provider_file is not None:
                engine.domain_index_for(provider_file)

    for domain in domains:
        row: Dict[str, Dict[str, Optional[str]]] = {}
        for label in labels:
            row[label] = engine.diagnose(template_paths[label], domain)
        results[domain] = row
    return results


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
            continue
        for lab in labs:
            if lab not in results[domain]:
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
        help="Run update_cache.py for selected templates before testing",
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
        help="Subset of template labels (default: every Sift template)",
    )
    args = parser.parse_args()

    cache_dir = args.cache_dir
    if not cache_dir.is_absolute():
        cache_dir = REPO_ROOT / cache_dir

    labels = args.templates or list(TEMPLATES.keys())
    domains = args.domains or list(DEFAULT_DOMAINS)

    if args.update_cache and not update_all_caches(cache_dir, labels):
        print("FAIL")
        return 1

    engine = er.RouteEngine(cache_dir)
    results = run_matrix(engine, labels, domains)

    print("=" * 130)
    print(f"{'domain':<28}" + "".join(f"{lab:<10}" for lab in labels))
    print("-" * 130)
    for domain in domains:
        cells = []
        for lab in labels:
            pol = results[domain][lab].get("policy") or "?"
            cells.append(f"{SHORT.get(pol, (pol or '?')[:8]):<10}")
        print(f"{domain:<28}" + "".join(cells))

    if args.no_assert:
        return 0

    expectations = default_expectations()
    fails, warns = run_expectations(results, expectations)

    print()
    print("=" * 130)
    print(f"SUMMARY: {fails} FAIL, {warns} WARN")
    print("Notes:")
    print("  - Domain-only diagnosis; pure IP providers skipped for domain probes.")
    print("  - Sift is the mainland whitelist: private / custom-direct / games-cn / cn / cnip / steam-cdn-ip direct, telegram+proxy before cn, rest proxied.")
    print("  - Sift-GFW is the GFWlist: only the gfw set is proxied, everything else direct.")
    print("  - Sift-Full uses DustinWin service sets plus custom-direct-domain and steam-cdn-ip; CN Apple/Microsoft/Google/games go to 全球直连, Telegram domain before proxy, MATCH to 漏网之鱼.")
    print("  - Steam download path: cm.steampowered.com / steamserver.net pick the region, steamcontent.com carries the payload.")
    print("  - In-process RouteEngine reuses provider indexes across all probes.")
    if fails:
        print("FAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
