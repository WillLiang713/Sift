#!/usr/bin/env python3
"""Download route-debug cache from URLs declared in Sift templates.

Collects rule-provider and geox-url sources across all given templates,
deduplicates by URL, then downloads (and decodes MRS) in parallel.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CACHE = REPO_ROOT / ".cache" / "sift-route-debug"
MRS_DUMP = Path(__file__).resolve().parent / "dump_mrs.mjs"
DEFAULT_WORKERS = 12


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
                    key = key.strip()
                    value = clean_value(value)
                    providers[provider][key] = value
                    if key == "<<" and value in {"*mrs-domain", "*mrs-ip"}:
                        providers[provider]["format"] = "mrs"
                        providers[provider]["behavior"] = (
                            "domain" if value == "*mrs-domain" else "ipcidr"
                        )
                continue

            if section == "rules" and stripped.startswith("- "):
                raw_rule = strip_comment(stripped[2:]).strip()
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

    proc = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False
    )
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


@dataclass
class CacheJob:
    """One unique downloadable URL (possibly referenced by many templates)."""

    kind: str
    url: str
    behavior: str
    source_format: str
    names: List[str] = field(default_factory=list)
    templates: List[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        primary = self.names[0] if self.names else "unknown"
        if len(self.names) > 1:
            return f"{primary}(+{len(self.names) - 1})"
        return primary


@dataclass
class JobResult:
    job: CacheJob
    ok: bool
    marker: str
    status: str
    output: Optional[Path] = None
    error: str = ""


def resolve_template(template_arg: str) -> Path:
    template = Path(template_arg)
    if not template.is_absolute():
        template = REPO_ROOT / template
    return template


def collect_jobs(templates: Sequence[Path]) -> Tuple[List[CacheJob], List[str]]:
    """Deduplicate sources by (kind, url). Return jobs and empty-template warnings."""
    by_key: Dict[Tuple[str, str], CacheJob] = {}
    empty: List[str] = []

    for template in templates:
        rel = str(template.relative_to(REPO_ROOT)) if template.is_relative_to(REPO_ROOT) else str(template)
        sources = list(iter_sources(parse_template(template)))
        if not sources:
            empty.append(rel)
            continue
        for kind, name, url, behavior, source_format in sources:
            key = (kind, url)
            job = by_key.get(key)
            if job is None:
                by_key[key] = CacheJob(
                    kind=kind,
                    url=url,
                    behavior=behavior,
                    source_format=source_format,
                    names=[name],
                    templates=[rel],
                )
                continue
            if name not in job.names:
                job.names.append(name)
            if rel not in job.templates:
                job.templates.append(rel)
            # Prefer a concrete MRS behavior if one reference has it.
            if not job.behavior and behavior:
                job.behavior = behavior
            if job.source_format.lower() != "mrs" and source_format.lower() == "mrs":
                job.source_format = source_format

    jobs = sorted(by_key.values(), key=lambda j: (j.kind, j.names[0] if j.names else "", j.url))
    return jobs, empty


def process_job(job: CacheJob, cache_dir: Path, force: bool) -> JobResult:
    primary = job.names[0] if job.names else "asset"
    key = cache_key(job.url)
    filename = filename_from_url(job.url, f"{primary}.dat" if job.kind == "geo" else f"{primary}.list")
    dest = cache_dir / job.kind / key / filename
    manifest = cache_dir / job.kind / key / "manifest.json"
    try:
        changed, status = download(job.url, dest, manifest, force)
        output = dest
        conversion = ""
        if job.kind == "ruleset" and job.source_format.lower() == "mrs":
            output = dest.with_suffix(".list")
            if changed or not output.exists():
                dump_mrs(dest, job.behavior, output)
                conversion = "; decoded MRS"
            point_manifest_to_text(manifest, dest, output)
        marker = "OK" if changed else "SKIP"
        return JobResult(
            job=job,
            ok=True,
            marker=marker,
            status=f"{status}{conversion}",
            output=output,
        )
    except Exception as exc:  # noqa: BLE001
        return JobResult(job=job, ok=False, marker="FAIL", status="error", error=str(exc))


def run_jobs(
    jobs: Sequence[CacheJob],
    cache_dir: Path,
    force: bool,
    workers: int,
) -> List[JobResult]:
    if not jobs:
        return []
    worker_count = max(1, min(workers, len(jobs)))
    if worker_count == 1:
        return [process_job(job, cache_dir, force) for job in jobs]

    results: List[Optional[JobResult]] = [None] * len(jobs)
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as pool:
        future_map = {
            pool.submit(process_job, job, cache_dir, force): index for index, job in enumerate(jobs)
        }
        for future in concurrent.futures.as_completed(future_map):
            index = future_map[future]
            results[index] = future.result()
    return [result for result in results if result is not None]


def print_results(results: Sequence[JobResult], cache_dir: Path) -> int:
    failed = 0
    for result in results:
        job = result.job
        if result.ok and result.output is not None:
            try:
                rel_out = result.output.relative_to(REPO_ROOT)
            except ValueError:
                rel_out = result.output
            print(
                f"  [{result.marker}] {job.kind}:{job.label} {result.status}"
                f" -> {rel_out}"
            )
        else:
            failed += 1
            print(f"  [FAIL] {job.kind}:{job.label} {job.url}")
            if result.error:
                print(f"         {result.error}")
    return failed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("templates", nargs="+", help="Template YAML files to cache")
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--force", action="store_true", help="Ignore conditional cache headers")
    parser.add_argument(
        "--jobs",
        type=int,
        default=DEFAULT_WORKERS,
        metavar="N",
        help=f"Parallel download/decode workers (default: {DEFAULT_WORKERS})",
    )
    args = parser.parse_args()

    cache_dir = args.cache_dir if args.cache_dir.is_absolute() else REPO_ROOT / args.cache_dir
    workers = max(1, args.jobs)

    templates: List[Path] = []
    for template_arg in args.templates:
        template = resolve_template(template_arg)
        if not template.exists():
            print(f"[FAIL] template not found: {template_arg}")
            return 1
        templates.append(template)

    jobs, empty = collect_jobs(templates)
    for rel in empty:
        print(f"[WARN] no cacheable rule/geox URLs in {rel}")

    if not jobs:
        print("[WARN] no cacheable sources found")
        return 0

    template_count = len(templates)
    unique = len(jobs)
    print(
        f"== cache update: {template_count} template(s), {unique} unique URL(s), "
        f"workers={min(workers, unique)} =="
    )

    results = run_jobs(jobs, cache_dir, args.force, workers)
    failed = print_results(results, cache_dir)

    downloaded = sum(1 for r in results if r.ok and r.marker == "OK")
    skipped = sum(1 for r in results if r.ok and r.marker == "SKIP")
    print(
        f"SUMMARY: {unique} unique, {downloaded} downloaded, {skipped} skipped, {failed} failed"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
