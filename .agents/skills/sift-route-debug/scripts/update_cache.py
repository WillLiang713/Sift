#!/usr/bin/env python3
"""Download route-debug cache from URLs declared in a Sift template."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CACHE = REPO_ROOT / ".cache" / "sift-route-debug"
MRS_DUMP = Path(__file__).resolve().parent / "dump_mrs.mjs"


def strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    for index, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:index]
    return line


def clean_value(value: str) -> str:
    value = strip_comment(value).strip()
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def parse_template(path: Path) -> Dict[str, object]:
    providers: Dict[str, Dict[str, str]] = {}
    geox: Dict[str, str] = {}
    used_providers = set()
    section: Optional[str] = None
    provider: Optional[str] = None

    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            if line and not line.startswith(" ") and not line.startswith("- ") and ":" in line:
                section = line.split(":", 1)[0].strip()
                provider = None
                continue

            if section == "geox-url" and line.startswith("  ") and ":" in line:
                key, value = line.strip().split(":", 1)
                geox[key.strip()] = clean_value(value)
                continue

            if section == "rule-providers":
                if line.startswith("  ") and not line.startswith("    ") and stripped.endswith(":"):
                    provider = stripped[:-1]
                    providers[provider] = {}
                    continue
                if provider and line.startswith("    ") and ":" in line:
                    key, value = stripped.split(":", 1)
                    providers[provider][key.strip()] = clean_value(value)
                continue

            if section == "rules" and line.startswith("- "):
                raw_rule = strip_comment(line[2:]).strip()
                parts = [part.strip() for part in raw_rule.split(",")]
                if len(parts) >= 2 and parts[0].upper() == "RULE-SET":
                    used_providers.add(parts[1])

    return {"providers": providers, "geox": geox, "used_providers": used_providers}


def cache_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def filename_from_url(url: str, fallback: str) -> str:
    name = Path(urlparse(url).path).name
    return name or fallback


def download(
    url: str,
    dest: Path,
    manifest_path: Path,
    force: bool,
) -> Tuple[bool, str]:
    headers = {"User-Agent": "Sift route debug cache updater"}
    if manifest_path.exists() and not force:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("url") == url and manifest.get("etag"):
                headers["If-None-Match"] = manifest["etag"]
            if manifest.get("url") == url and manifest.get("last_modified"):
                headers["If-Modified-Since"] = manifest["last_modified"]
        except json.JSONDecodeError:
            pass

    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_suffix(dest.suffix + ".tmp")
            tmp.write_bytes(response.read())
            os.replace(tmp, dest)
            manifest = {
                "url": url,
                "file": dest.name,
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
            }
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return True, "downloaded"
    except HTTPError as exc:
        if exc.code == 304 and dest.exists():
            return False, "not modified"
        raise


def is_mrs_source(data: Dict[str, str], url: str) -> bool:
    return data.get("format", "").lower() == "mrs" or urlparse(url).path.lower().endswith(".mrs")


def dump_mrs(source: Path, behavior: str, dest: Path) -> None:
    """Convert a binary MRS cache into text for deterministic diagnostics."""
    behavior = behavior.lower()
    if behavior not in {"domain", "ipcidr"}:
        raise ValueError(f"unsupported MRS behavior: {behavior or '(missing)'}")

    mihomo = shutil.which("mihomo")
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    if mihomo:
        command = [mihomo, "convert-ruleset", behavior, "mrs", str(source), str(tmp)]
    else:
        node = shutil.which("node")
        if not node:
            raise RuntimeError("MRS diagnostics require mihomo or Node.js with Zstandard support")
        command = [node, str(MRS_DUMP), behavior, str(source), str(tmp)]

    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        tmp.unlink(missing_ok=True)
        detail = proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}"
        raise RuntimeError(f"unable to decode MRS: {detail}")
    os.replace(tmp, dest)


def point_manifest_to_text(manifest_path: Path, source: Path, text: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(
        {
            "file": text.name,
            "source_file": source.name,
            "source_format": "mrs",
            "format": "text",
        }
    )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def iter_sources(parsed: Dict[str, object]) -> Iterable[Tuple[str, str, str, str, str]]:
    providers: Dict[str, Dict[str, str]] = parsed["providers"]  # type: ignore[assignment]
    geox: Dict[str, str] = parsed["geox"]  # type: ignore[assignment]
    used_providers = parsed["used_providers"]  # type: ignore[assignment]

    for name, data in sorted(providers.items()):
        if name not in used_providers:
            continue
        url = data.get("url", "")
        if url:
            source_format = "mrs" if is_mrs_source(data, url) else data.get("format", "")
            yield ("ruleset", name, url, data.get("behavior", ""), source_format)

    for name in ("geosite", "geoip", "mmdb"):
        url = geox.get(name, "")
        if url:
            yield ("geo", name, url, "", "")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("templates", nargs="+", help="Template YAML files to cache")
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--force", action="store_true", help="Ignore conditional cache headers")
    args = parser.parse_args()

    for template_arg in args.templates:
        template = Path(template_arg)
        if not template.is_absolute():
            template = REPO_ROOT / template
        if not template.exists():
            print(f"[FAIL] template not found: {template_arg}")
            return 1

        sources = list(iter_sources(parse_template(template)))
        if not sources:
            print(f"[WARN] no cacheable rule/geox URLs in {template_arg}")
            continue

        print(f"== {template.relative_to(REPO_ROOT)} ==")
        for kind, name, url, behavior, source_format in sources:
            key = cache_key(url)
            filename = filename_from_url(url, f"{name}.dat" if kind == "geo" else f"{name}.list")
            dest = args.cache_dir / kind / key / filename
            manifest = args.cache_dir / kind / key / "manifest.json"
            try:
                changed, status = download(url, dest, manifest, args.force)
                output = dest
                conversion = ""
                if kind == "ruleset" and source_format == "mrs":
                    output = dest.with_suffix(".list")
                    if changed or not output.exists():
                        dump_mrs(dest, behavior, output)
                        conversion = "; decoded MRS"
                    point_manifest_to_text(manifest, dest, output)
                marker = "OK" if changed else "SKIP"
                print(
                    f"  [{marker}] {kind}:{name} {status}{conversion}"
                    f" -> {output.relative_to(REPO_ROOT)}"
                )
            except Exception as exc:  # noqa: BLE001
                print(f"  [FAIL] {kind}:{name} {url}")
                print(f"         {exc}")
                return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
