#!/usr/bin/env python3
"""Explain the first matching Sift route rule for a domain or IP."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CACHE = REPO_ROOT / ".cache" / "sift-route-debug"


@dataclass
class Provider:
    name: str
    behavior: str = ""
    format: str = ""
    path: str = ""
    url: str = ""


@dataclass
class Rule:
    line_no: int
    raw: str
    parts: List[str]


@dataclass
class Template:
    path: Path
    providers: Dict[str, Provider]
    geox: Dict[str, str]
    rules: List[Rule]


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


def split_rule(raw: str) -> List[str]:
    return [part.strip() for part in raw.split(",")]


def parse_template(path: Path) -> Template:
    providers: Dict[str, Provider] = {}
    geox: Dict[str, str] = {}
    rules: List[Rule] = []
    section: Optional[str] = None
    provider: Optional[str] = None

    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.rstrip("\n")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            if line and not line.startswith(" ") and not line.startswith("- ") and ":" in line:
                section = line.split(":", 1)[0].strip()
                provider = None
                if section != "rules":
                    continue

            if section == "geox-url" and line.startswith("  ") and ":" in line:
                key, value = line.strip().split(":", 1)
                geox[key.strip()] = clean_value(value)
                continue

            if section == "rule-providers":
                if line.startswith("  ") and not line.startswith("    ") and stripped.endswith(":"):
                    provider = stripped[:-1]
                    providers[provider] = Provider(name=provider)
                    continue
                if provider and line.startswith("    ") and ":" in line:
                    key, value = stripped.split(":", 1)
                    attr = key.strip().replace("-", "_")
                    merged = clean_value(value)
                    if attr == "<<" and merged in {"*mrs-domain", "*mrs-ip"}:
                        providers[provider].format = "mrs"
                        providers[provider].behavior = (
                            "domain" if merged == "*mrs-domain" else "ipcidr"
                        )
                        continue
                    if attr == "format":
                        providers[provider].format = clean_value(value)
                    elif hasattr(providers[provider], attr):
                        setattr(providers[provider], attr, clean_value(value))
                continue

            if section == "rules" and stripped.startswith("- "):
                raw = strip_comment(stripped[2:]).strip()
                if raw:
                    rules.append(Rule(line_no=line_no, raw=raw, parts=split_rule(raw)))

    return Template(path=path, providers=providers, geox=geox, rules=rules)


def cache_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def cache_file(cache_dir: Path, kind: str, url: str) -> Optional[Path]:
    directory = cache_dir / kind / cache_key(url)
    manifest = directory / "manifest.json"
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            candidate = directory / data.get("file", "")
            if candidate.exists():
                return candidate
        except json.JSONDecodeError:
            pass
    if not directory.exists():
        return None
    files = [path for path in directory.iterdir() if path.is_file() and path.name != "manifest.json"]
    return files[0] if files else None


def resolve_provider_file(provider: Provider, cache_dir: Path) -> Optional[Path]:
    is_mrs = provider.format.lower() == "mrs" or provider.url.lower().endswith(".mrs")
    if is_mrs:
        if not provider.url:
            return None
        candidate = cache_file(cache_dir, "ruleset", provider.url)
        if candidate and candidate.suffix.lower() != ".mrs":
            return candidate
        return None
    if provider.path:
        local = REPO_ROOT / provider.path
        if local.exists():
            return local
    if provider.url:
        return cache_file(cache_dir, "ruleset", provider.url)
    return None


def input_ip(value: str) -> Optional[ipaddress._BaseAddress]:
    try:
        return ipaddress.ip_address(value)
    except ValueError:
        return None


def normalize_domain(domain: str) -> str:
    return domain.strip(".").lower()


def domain_is_suffix(domain: str, suffix: str) -> bool:
    domain = normalize_domain(domain)
    suffix = normalize_domain(suffix)
    return domain == suffix or domain.endswith("." + suffix)


def match_domain_entry(domain: str, entry: str) -> Optional[str]:
    line = strip_comment(entry).strip()
    if not line or line.startswith("#"):
        return None

    if "," in line:
        kind, value = line.split(",", 1)
        kind = kind.strip().upper()
        value = value.strip()
        if kind == "DOMAIN" and normalize_domain(domain) == normalize_domain(value):
            return line
        if kind == "DOMAIN-SUFFIX" and domain_is_suffix(domain, value):
            return line
        if kind == "DOMAIN-KEYWORD" and value.lower() in domain.lower():
            return line
        if kind == "DOMAIN-REGEX":
            try:
                return line if re.search(value, domain) else None
            except re.error:
                return None
        return None

    lower = line.lower()
    if lower.startswith("domain:") or lower.startswith("full:"):
        value = line.split(":", 1)[1]
        return line if normalize_domain(domain) == normalize_domain(value) else None
    if lower.startswith("suffix:"):
        return line if domain_is_suffix(domain, line.split(":", 1)[1]) else None
    if lower.startswith("keyword:"):
        return line if line.split(":", 1)[1].lower() in domain.lower() else None
    if lower.startswith("regexp:") or lower.startswith("regex:"):
        pattern = line.split(":", 1)[1]
        try:
            return line if re.search(pattern, domain) else None
        except re.error:
            return None

    if line.startswith("+."):
        return line if domain_is_suffix(domain, line[2:]) else None
    if line.startswith("."):
        return line if domain_is_suffix(domain, line[1:]) else None
    return line if domain_is_suffix(domain, line) else None


def match_ip_entry(ip: ipaddress._BaseAddress, entry: str) -> Optional[str]:
    line = strip_comment(entry).strip()
    if not line or line.startswith("#"):
        return None
    if "," in line:
        kind, value = line.split(",", 1)
        kind = kind.strip().upper()
        value = value.split(",", 1)[0].strip()
        if kind not in {"IP-CIDR", "IP-CIDR6"}:
            return None
    else:
        value = line
    try:
        network = ipaddress.ip_network(value, strict=False)
    except ValueError:
        return None
    return line if ip in network else None


def iter_provider_lines(path: Path) -> Iterable[Tuple[int, str]]:
    if path.suffix.lower() == ".mrs":
        raise ValueError(f"binary MRS ruleset is not directly readable: {path}")
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            yield line_no, line.rstrip("\n")


def policy_from_rule(parts: Sequence[str]) -> str:
    if not parts:
        return ""
    index = len(parts) - 1
    if parts[index] in {"no-resolve", "src"}:
        index -= 1
    return parts[index] if index >= 0 else ""


def explain_ruleset(template: Template, target: str, cache_dir: Path) -> int:
    ip = input_ip(target)
    mode = "ip" if ip else "domain"
    skipped_ip = False
    missing: List[str] = []

    print(f"template: {template.path.relative_to(REPO_ROOT)}")
    print("mode: ruleset")
    print(f"input: {target}")
    print(f"input type: {mode}")
    print()

    for rule in template.rules:
        if not rule.parts:
            continue
        kind = rule.parts[0].upper()
        if kind == "MATCH":
            if missing:
                print("missing cache:")
                for missing_name in missing:
                    provider = template.providers.get(missing_name)
                    print(f"  - {missing_name}: {provider.url if provider else ''}")
                print()
                print("run:")
                print(f"  .agents/skills/sift-route-debug/scripts/update_cache.py {template.path.relative_to(REPO_ROOT)}")
                return 2
            print("first matched rule:")
            print(f"  line: {rule.line_no}")
            print(f"  template rule: {rule.raw}")
            print(f"  policy: {policy_from_rule(rule.parts)}")
            return 0
        if kind != "RULE-SET" or len(rule.parts) < 3:
            continue

        name = rule.parts[1]
        provider = template.providers.get(name)
        if not provider:
            continue

        behavior = provider.behavior.lower()
        if mode == "domain" and behavior == "ipcidr":
            skipped_ip = True
            continue
        if mode == "ip" and behavior == "domain":
            continue

        provider_file = resolve_provider_file(provider, cache_dir)
        if not provider_file:
            missing.append(name)
            continue

        for provider_line_no, entry in iter_provider_lines(provider_file):
            matched = match_ip_entry(ip, entry) if ip else match_domain_entry(target, entry)
            if matched:
                print("first matched rule:")
                print(f"  line: {rule.line_no}")
                print(f"  template rule: {rule.raw}")
                print(f"  provider: {name}")
                print(f"  provider behavior: {provider.behavior or '(unknown)'}")
                print(f"  provider source: {provider.url or provider.path}")
                print(f"  provider line: {provider_line_no}")
                print(f"  provider match: {matched}")
                print(f"  policy: {policy_from_rule(rule.parts)}")
                if mode == "domain" and skipped_ip:
                    print()
                    print("notes:")
                    print("  IP providers were skipped for domain-only diagnosis.")
                return 0

    if missing:
        print("missing cache:")
        for name in missing:
            provider = template.providers.get(name)
            print(f"  - {name}: {provider.url if provider else ''}")
        print()
        print("run:")
        print(f"  .agents/skills/sift-route-debug/scripts/update_cache.py {template.path.relative_to(REPO_ROOT)}")
        return 2

    print("no matching rule found")
    if skipped_ip and mode == "domain":
        print()
        print("notes:")
        print("  Domain diagnosis skipped IP providers; runtime may route by resolved IP.")
    return 1


def run_geo_look(geo_bin: str, data_dir: Path, target: str, no_resolve: bool) -> Tuple[int, str, str, List[str]]:
    no_resolve_args = ["--no-resolve"] if no_resolve else []
    variants = [
        [geo_bin, "look", "-D", str(data_dir), *no_resolve_args, target],
        [geo_bin, "look", "--data-dir", str(data_dir), *no_resolve_args, target],
        [geo_bin, "-D", str(data_dir), "look", *no_resolve_args, target],
        [geo_bin, "look", *no_resolve_args, "-d", str(data_dir), target],
    ]
    tried: List[str] = []
    last_stdout = ""
    last_stderr = ""
    for command in variants:
        tried.append(" ".join(command))
        try:
            proc = subprocess.run(
                command, check=False, text=True, encoding="utf-8", errors="replace", capture_output=True
            )
        except FileNotFoundError:
            return 127, "", f"{geo_bin} not found on PATH", tried
        last_stdout, last_stderr = proc.stdout, proc.stderr
        if proc.returncode == 0:
            return 0, proc.stdout, proc.stderr, tried
    return 1, last_stdout, last_stderr, tried


def extract_geo_matches(output: str, candidates: Sequence[str]) -> List[str]:
    matches: List[str] = []
    for tag in candidates:
        pattern = re.compile(r"(?<![A-Za-z0-9_@!.-])" + re.escape(tag) + r"(?![A-Za-z0-9_@!.-])", re.I)
        if pattern.search(output):
            matches.append(tag)
    return matches


def explain_geodata(template: Template, target: str, cache_dir: Path, geo_bin: str) -> int:
    ip = input_ip(target)
    mode = "ip" if ip else "domain"
    candidates: List[str] = []
    for rule in template.rules:
        if len(rule.parts) >= 2 and rule.parts[0].upper() in {"GEOSITE", "GEOIP"}:
            candidates.append(rule.parts[1])

    print(f"template: {template.path.relative_to(REPO_ROOT)}")
    print("mode: geodata")
    print(f"input: {target}")
    print(f"input type: {mode}")

    if ip:
        geo_url = template.geox.get("mmdb") or template.geox.get("geoip")
        geo_kind = "mmdb" if template.geox.get("mmdb") else "geoip"
    else:
        geo_url = template.geox.get("geosite")
        geo_kind = "geosite"

    if not geo_url:
        print()
        print(f"[FAIL] template has no geox-url.{geo_kind}")
        return 2

    geo_file = cache_file(cache_dir, "geo", geo_url)
    if not geo_file:
        print()
        print("missing cache:")
        print(f"  - {geo_kind}: {geo_url}")
        print()
        print("run:")
        print(f"  .agents/skills/sift-route-debug/scripts/update_cache.py {template.path.relative_to(REPO_ROOT)}")
        return 2

    data_dir = geo_file.parent
    print("geo source:")
    print(f"  {geo_kind}: {geo_url}")
    print(f"  cache: {geo_file.relative_to(REPO_ROOT)}")
    print()

    code, stdout, stderr, tried = run_geo_look(geo_bin, data_dir, target, no_resolve=not ip)
    if code != 0:
        print("[FAIL] unable to query geo database")
        print("tried:")
        for command in tried:
            print(f"  - {command}")
        if stderr.strip():
            print("stderr:")
            print(stderr.strip())
        if stdout.strip():
            print("stdout:")
            print(stdout.strip())
        return 2

    output = stdout + "\n" + stderr
    matches = extract_geo_matches(output, candidates)
    if matches:
        print("matched geo tags:")
        for match in matches:
            print(f"  - {match}")
    else:
        print("matched geo tags: none found in geo output")
        print()
        print("raw geo output:")
        print(stdout.strip() or stderr.strip() or "(empty)")

    for rule in template.rules:
        if len(rule.parts) < 3:
            continue
        kind = rule.parts[0].upper()
        tag = rule.parts[1]
        if mode == "domain" and kind != "GEOSITE":
            continue
        if mode == "ip" and kind != "GEOIP":
            continue
        if tag in matches:
            print()
            print("first matched rule:")
            print(f"  line: {rule.line_no}")
            print(f"  template rule: {rule.raw}")
            print(f"  policy: {policy_from_rule(rule.parts)}")
            if mode == "domain":
                print()
                print("notes:")
                print("  Domain mode used no-resolve; GEOIP rules were not evaluated.")
            return 0

    print()
    print("no matching geodata rule found")
    return 1


def template_mode(template: Template) -> str:
    has_ruleset = any(rule.parts and rule.parts[0].upper() == "RULE-SET" for rule in template.rules)
    has_geo = any(rule.parts and rule.parts[0].upper() in {"GEOSITE", "GEOIP"} for rule in template.rules)
    if has_ruleset and has_geo:
        return "mixed"
    if has_geo:
        return "geodata"
    return "ruleset"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", help="Template YAML file")
    parser.add_argument("target", help="Domain or IP to diagnose")
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--geo-bin", default="geo", help="Geo CLI binary for geodata templates")
    args = parser.parse_args()

    template_path = Path(args.template)
    if not template_path.is_absolute():
        template_path = REPO_ROOT / template_path
    if not template_path.exists():
        print(f"[FAIL] template not found: {args.template}", file=sys.stderr)
        return 2

    template = parse_template(template_path)
    mode = template_mode(template)
    if mode == "mixed":
        print("[FAIL] mixed RULE-SET and GEOSITE/GEOIP rules are not supported", file=sys.stderr)
        return 2
    if mode == "geodata":
        return explain_geodata(template, args.target, args.cache_dir, args.geo_bin)
    return explain_ruleset(template, args.target, args.cache_dir)


if __name__ == "__main__":
    raise SystemExit(main())
