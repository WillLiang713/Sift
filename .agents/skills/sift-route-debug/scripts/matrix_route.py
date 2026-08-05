#!/usr/bin/env python3
"""Regression matrix: first-match domain routes for all Sift templates under rules/.

Uses template-declared providers / geox-url only (via explain_route helpers).
Domain-only diagnosis: GEOIP rules and providers with behavior ipcidr are
skipped for domain input.

Exit 0 if all FAIL-level expectations pass; exit 1 on any FAIL.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple
from urllib.request import Request, urlopen

# scripts/ -> sift-route-debug -> skills -> .agents -> repo root
REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import explain_route as er  # noqa: E402

DEFAULT_CACHE = REPO_ROOT / ".cache" / "sift-route-debug"
UPDATE_CACHE = SCRIPTS / "update_cache.py"
GEO_VERSION = "v1.1"
GEO_RELEASE_API = "https://api.github.com/repos/MetaCubeX/geo/releases/tags/{version}"


def utf8_python_env() -> Dict[str, str]:
    """Return an environment that makes child Python output UTF-8 on Windows."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


TEMPLATES: Dict[str, str] = {
    "HY-f": "rules/full.yaml",
    "HY-c": "rules/core.yaml",
    "HY-n": "rules/nano.yaml",
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
    "直连": "直连",
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
FULLS = ["HY-f"]
CORES = ["HY-c"]
NANOS = ["HY-n"]

# (domain, template_labels, allowed_policies, level)
# level: "FAIL" fails the run; "WARN" is informational only.
Expectation = Tuple[str, Sequence[str], Set[str], str]


def default_expectations() -> List[Expectation]:
    """Product-contract expectations for the current Sift routing design."""
    exp: List[Expectation] = []

    exp.append(("localhost", ALL, {"DIRECT"}, "FAIL"))

    # Google/Play hard anchors (routing contract). Pair with Full/Core DNS whitelist
    # (rule-set:proxy) so these domains enter Mihomo
    # with overseas DoH — DNS is not re-asserted by this domain matrix.
    # gstatic.cn stays in DEFAULT_DOMAINS for display only (no FAIL/WARN).
    exp.append(("googleapis.cn", FULLS, {"谷歌服务"}, "FAIL"))
    exp.append(("googleapis.cn", CORES + NANOS, {"节点选择"}, "FAIL"))
    exp.append(("play.googleapis.com", FULLS, {"谷歌服务"}, "FAIL"))
    exp.append(("play.googleapis.com", CORES + NANOS, {"节点选择"}, "FAIL"))

    exp.append(("www.google.com", FULLS, {"谷歌服务"}, "FAIL"))
    exp.append(("www.google.com", CORES + NANOS, {"节点选择"}, "FAIL"))

    exp.append(("www.youtube.com", FULLS, {"流媒体"}, "FAIL"))
    exp.append(("www.youtube.com", CORES + NANOS, {"节点选择", "漏网之鱼"}, "FAIL"))

    # Full intentionally binds CF verification traffic to the streaming group
    # through the DustinWin media domain set.
    exp.append(("challenges.cloudflare.com", FULLS, {"流媒体"}, "FAIL"))

    exp.append(("chatgpt.com", FULLS, {"AI"}, "FAIL"))
    exp.append(("chatgpt.com", CORES, {"节点选择", "漏网之鱼"}, "FAIL"))
    exp.append(("chatgpt.com", NANOS, {"节点选择"}, "FAIL"))

    exp.append(("www.netflix.com", FULLS, {"节点选择", "流媒体", "漏网之鱼"}, "WARN"))

    exp.append(("web.telegram.org", FULLS, {"Telegram"}, "FAIL"))
    exp.append(("web.telegram.org", CORES + NANOS, {"节点选择"}, "FAIL"))

    for domestic in ("www.baidu.com", "www.qq.com", "www.taobao.com", "www.bilibili.com"):
        exp.append((domestic, ALL, {"直连"}, "FAIL"))

    exp.append(("github.com", FULLS + CORES, {"GitHub"}, "FAIL"))
    exp.append(("github.com", NANOS, {"节点选择", "漏网之鱼"}, "FAIL"))

    # OneDrive: dedicated group on Full/Core; Nano has no group.
    exp.append(("onedrive.live.com", FULLS + CORES, {"OneDrive"}, "FAIL"))
    exp.append(("onedrive.live.com", NANOS, {"节点选择"}, "FAIL"))

    exp.append(("icloud.com", CORES, {"苹果服务"}, "FAIL"))
    exp.append(("office.com", CORES, {"微软服务"}, "FAIL"))
    exp.append(("icloud.com", FULLS, {"苹果服务"}, "FAIL"))
    exp.append(("office.com", FULLS, {"微软服务"}, "FAIL"))

    return exp


def update_all_caches(cache_dir: Path, labels: Sequence[str]) -> bool:
    """Refresh rule/geox caches once for all selected templates (URL-deduped, parallel)."""
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


def ensure_geo_bin(preferred: str) -> str:
    """Return a usable geo binary, downloading the official platform build if needed."""
    if preferred != "geo":
        return preferred
    installed = shutil.which("geo")
    if installed:
        return installed

    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = {
        "amd64": "amd64",
        "x86_64": "amd64",
        "aarch64": "arm64",
        "arm64": "arm64",
        "i386": "386",
        "i686": "386",
    }.get(machine)
    if system not in {"windows", "linux", "darwin"} or not arch:
        return preferred
    destination = REPO_ROOT / ".cache" / "tools" / "geo-bin" / GEO_VERSION / f"{system}-{arch}"
    binary = destination / ("geo.exe" if system == "windows" else "geo")
    if binary.is_file():
        return str(binary)

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Sift route matrix",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(GEO_RELEASE_API.format(version=GEO_VERSION), headers=headers), timeout=30) as response:
        release = json.load(response)
    assets = [asset for asset in release.get("assets", []) if isinstance(asset, dict)]
    matches = [
        asset
        for asset in assets
        if system in str(asset.get("name", "")).lower() and arch in str(asset.get("name", "")).lower()
    ]
    if not matches:
        raise RuntimeError(f"geo {GEO_VERSION} has no asset for {system}/{arch}")
    asset = matches[0]
    destination.mkdir(parents=True, exist_ok=True)
    temporary = binary.with_suffix(binary.suffix + ".tmp")
    with urlopen(
        Request(asset["browser_download_url"], headers={"User-Agent": "Sift route matrix"}),
        timeout=120,
    ) as response, temporary.open("wb") as output:
        shutil.copyfileobj(response, output)
    digest = asset.get("digest")
    if isinstance(digest, str) and digest.startswith("sha256:"):
        actual = hashlib.sha256(temporary.read_bytes()).hexdigest()
        if actual.lower() != digest.removeprefix("sha256:").lower():
            temporary.unlink(missing_ok=True)
            raise RuntimeError("geo SHA-256 mismatch")
    os.replace(temporary, binary)
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return str(binary)


def _geosite_data_dirs(engine: er.RouteEngine, template_paths: Dict[str, Path]) -> List[Path]:
    dirs: List[Path] = []
    seen: Set[str] = set()
    for path in template_paths.values():
        template = engine.load_template(path)
        if er.template_mode(template) != "geodata":
            continue
        url = template.geox.get("geosite")
        if not url:
            continue
        geo_file = er.cache_file(engine.cache_dir, "geo", url)
        if geo_file is None:
            continue
        key = str(geo_file.parent.resolve())
        if key in seen:
            continue
        seen.add(key)
        dirs.append(geo_file.parent)
    return dirs


def _warm_geo_outputs(engine: er.RouteEngine, data_dirs: Sequence[Path], domains: Sequence[str]) -> None:
    """Prefetch MetaCubeX geo look results in parallel (shared across MC templates)."""
    if not data_dirs or not domains:
        return

    # Resolve the working geo argv once so workers do not each try every variant.
    first = domains[0]
    for data_dir in data_dirs:
        engine.geo_output(data_dir, first, no_resolve=True)

    rest = list(domains[1:])
    if not rest:
        return

    def one(domain: str) -> None:
        for data_dir in data_dirs:
            engine.geo_output(data_dir, domain, no_resolve=True)

    workers = min(8, max(1, len(rest)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, rest))


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

    # MetaCubeX templates share geosite data; parallel-prefetch once per domain.
    _warm_geo_outputs(engine, _geosite_data_dirs(engine, template_paths), domains)

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
        help="Subset of template labels (default: all three)",
    )
    args = parser.parse_args()

    cache_dir = args.cache_dir
    if not cache_dir.is_absolute():
        cache_dir = REPO_ROOT / cache_dir

    labels = args.templates or list(TEMPLATES.keys())
    domains = args.domains or list(DEFAULT_DOMAINS)
    geo_bin = (
        ensure_geo_bin(args.geo_bin)
        if any(label.startswith("MC-") for label in labels)
        else args.geo_bin
    )

    if args.update_cache and not update_all_caches(cache_dir, labels):
        print("FAIL")
        return 1

    engine = er.RouteEngine(cache_dir, geo_bin)
    results = run_matrix(engine, labels, domains)

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
    print("  - Google/Play FAIL anchors: googleapis.cn + play.googleapis.com (gstatic.cn display-only).")
    print("  - In-process RouteEngine reuses provider indexes across all probes.")
    if fails:
        print("FAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
