#!/usr/bin/env python3
"""Bootstrap a pinned Mihomo release and validate every Sift YAML template."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Dict, List
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_VERSION = "v1.19.29"
DEFAULT_CACHE = REPO_ROOT / ".cache" / "mihomo-validation"
RELEASE_API = "https://api.github.com/repos/MetaCubeX/mihomo/releases/tags/{version}"


def platform_id() -> tuple[str, str, str]:
    system = platform.system().lower()
    if system not in {"windows", "linux", "darwin"}:
        raise RuntimeError(f"unsupported operating system: {system}")

    machine = platform.machine().lower()
    arch_aliases = {
        "amd64": "amd64",
        "x86_64": "amd64",
        "i386": "386",
        "i686": "386",
        "aarch64": "arm64",
        "arm64": "arm64",
    }
    arch = arch_aliases.get(machine)
    if not arch:
        raise RuntimeError(f"unsupported architecture: {machine}")
    return system, arch, ".zip" if system == "windows" else ".gz"


def api_json(url: str) -> Dict[str, object]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Sift Mihomo config validator",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return json.load(response)


def select_asset(release: Dict[str, object], system: str, arch: str, suffix: str, version: str) -> Dict[str, object]:
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise RuntimeError("GitHub release response has no assets")

    exact = f"mihomo-{system}-{arch}-{version}{suffix}"
    compatible = f"mihomo-{system}-{arch}-compatible-{version}{suffix}"
    v1 = f"mihomo-{system}-{arch}-v1-{version}{suffix}"
    by_name = {
        asset.get("name"): asset
        for asset in assets
        if isinstance(asset, dict) and isinstance(asset.get("name"), str)
    }
    for name in (exact, compatible, v1):
        asset = by_name.get(name)
        if isinstance(asset, dict):
            return asset
    raise RuntimeError(f"release {version} has no asset for {system}/{arch}")


def download_asset(asset: Dict[str, object], destination: Path) -> Path:
    url = asset.get("browser_download_url")
    name = asset.get("name")
    digest = asset.get("digest")
    if not isinstance(url, str) or not isinstance(name, str):
        raise RuntimeError("invalid GitHub release asset metadata")
    if not isinstance(digest, str) or not digest.startswith("sha256:"):
        raise RuntimeError(f"release asset has no SHA-256 digest: {name}")

    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / name
    request = Request(url, headers={"User-Agent": "Sift Mihomo config validator"})
    with urlopen(request, timeout=120) as response, archive.open("wb") as output:
        shutil.copyfileobj(response, output)

    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    expected = digest.removeprefix("sha256:")
    if actual.lower() != expected.lower():
        archive.unlink(missing_ok=True)
        raise RuntimeError(f"SHA-256 mismatch for {name}")
    return archive


def extract_binary(archive: Path, destination: Path, system: str) -> Path:
    binary = destination / ("mihomo.exe" if system == "windows" else "mihomo")
    temporary = binary.with_suffix(binary.suffix + ".tmp")
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as package:
            members = [item for item in package.infolist() if not item.is_dir()]
            executable = next((item for item in members if item.filename.lower().endswith(".exe")), None)
            if not executable:
                raise RuntimeError(f"no executable found in {archive.name}")
            with package.open(executable) as source, temporary.open("wb") as output:
                shutil.copyfileobj(source, output)
    else:
        with gzip.open(archive, "rb") as source, temporary.open("wb") as output:
            shutil.copyfileobj(source, output)
    os.replace(temporary, binary)
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return binary


def bootstrap_mihomo(version: str, cache_dir: Path) -> Path:
    system, arch, suffix = platform_id()
    destination = cache_dir / "tools" / version / f"{system}-{arch}"
    binary = destination / ("mihomo.exe" if system == "windows" else "mihomo")
    if binary.is_file():
        return binary

    release = api_json(RELEASE_API.format(version=version))
    asset = select_asset(release, system, arch, suffix, version)
    print(f"[GET] {asset['name']}")
    archive = download_asset(asset, destination)
    try:
        return extract_binary(archive, destination, system)
    finally:
        archive.unlink(missing_ok=True)


def discover_templates(arguments: List[str]) -> List[Path]:
    if arguments:
        templates = [Path(item) if Path(item).is_absolute() else REPO_ROOT / item for item in arguments]
    else:
        templates = sorted((REPO_ROOT / "rules").rglob("*.yaml"))
    missing = [path for path in templates if not path.is_file()]
    if missing:
        raise RuntimeError(f"template not found: {missing[0]}")
    return templates


def validate(binary: Path, templates: List[Path], cache_dir: Path) -> int:
    failed = 0
    print(
        f"[MIHOMO] {subprocess.check_output([str(binary), '-v'], text=True, encoding='utf-8', errors='replace').strip()}"
    )
    for template in templates:
        relative = template.relative_to(REPO_ROOT)
        slug = "__".join(relative.with_suffix("").parts)
        home = cache_dir / "homes" / slug
        home.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [str(binary), "-t", "-d", str(home), "-f", str(template)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0:
            failed += 1
            print(f"[FAIL] {relative}")
            detail = (result.stdout + result.stderr).strip()
            if detail:
                print(detail)
        else:
            print(f"[OK] {relative}")
    print(f"\nSUMMARY: {len(templates) - failed} PASS, {failed} FAIL")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("templates", nargs="*", help="Template paths (default: rules/**/*.yaml)")
    parser.add_argument("--mihomo", type=Path, help="Use an existing Mihomo binary")
    parser.add_argument("--version", default=DEFAULT_VERSION, help=f"Pinned release (default: {DEFAULT_VERSION})")
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    args = parser.parse_args()

    cache_dir = args.cache_dir if args.cache_dir.is_absolute() else REPO_ROOT / args.cache_dir
    try:
        binary = args.mihomo or bootstrap_mihomo(args.version, cache_dir)
        if not binary.is_absolute():
            binary = REPO_ROOT / binary
        if not binary.is_file():
            raise RuntimeError(f"Mihomo binary not found: {binary}")
        return validate(binary, discover_templates(args.templates), cache_dir)
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
