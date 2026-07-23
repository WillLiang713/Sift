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
import threading
from dataclasses import dataclass, field
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


@dataclass
class DomainProviderIndex:
    """First-match domain index for one provider file."""

    exact: Dict[str, Tuple[int, str]] = field(default_factory=dict)
    suffixes: Dict[str, Tuple[int, str]] = field(default_factory=dict)
    keywords: List[Tuple[str, int, str]] = field(default_factory=list)
    regexes: List[Tuple[re.Pattern[str], int, str]] = field(default_factory=list)

    def match(self, domain: str) -> Optional[Tuple[int, str]]:
        needle = normalize_domain(domain)
        best: Optional[Tuple[int, str]] = None

        def consider(item: Tuple[int, str]) -> None:
            nonlocal best
            if best is None or item[0] < best[0]:
                best = item

        exact = self.exact.get(needle)
        if exact:
            consider(exact)

        labels = needle.split(".") if needle else []
        for index in range(len(labels)):
            suffix = ".".join(labels[index:])
            hit = self.suffixes.get(suffix)
            if hit:
                consider(hit)

        for keyword, line_no, entry in self.keywords:
            if keyword in needle:
                consider((line_no, entry))

        for pattern, line_no, entry in self.regexes:
            if pattern.search(domain) or pattern.search(needle):
                consider((line_no, entry))

        return best


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
    files = [
        path for path in directory.iterdir() if path.is_file() and path.name != "manifest.json"
    ]
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


def _remember_first(store: Dict[str, Tuple[int, str]], key: str, line_no: int, entry: str) -> None:
    previous = store.get(key)
    if previous is None or line_no < previous[0]:
        store[key] = (line_no, entry)


def build_domain_index(path: Path) -> DomainProviderIndex:
    index = DomainProviderIndex()
    for line_no, raw in iter_provider_lines(path):
        line = strip_comment(raw).strip()
        if not line or line.startswith("#"):
            continue

        if "," in line:
            kind, value = line.split(",", 1)
            kind = kind.strip().upper()
            value = value.strip()
            if kind == "DOMAIN":
                _remember_first(index.exact, normalize_domain(value), line_no, line)
            elif kind == "DOMAIN-SUFFIX":
                _remember_first(index.suffixes, normalize_domain(value), line_no, line)
            elif kind == "DOMAIN-KEYWORD":
                keyword = value.lower()
                if keyword:
                    index.keywords.append((keyword, line_no, line))
            elif kind == "DOMAIN-REGEX":
                try:
                    index.regexes.append((re.compile(value), line_no, line))
                except re.error:
                    pass
            continue

        lower = line.lower()
        if lower.startswith("domain:") or lower.startswith("full:"):
            value = line.split(":", 1)[1]
            _remember_first(index.exact, normalize_domain(value), line_no, line)
            continue
        if lower.startswith("suffix:"):
            _remember_first(index.suffixes, normalize_domain(line.split(":", 1)[1]), line_no, line)
            continue
        if lower.startswith("keyword:"):
            keyword = line.split(":", 1)[1].lower()
            if keyword:
                index.keywords.append((keyword, line_no, line))
            continue
        if lower.startswith("regexp:") or lower.startswith("regex:"):
            pattern = line.split(":", 1)[1]
            try:
                index.regexes.append((re.compile(pattern), line_no, line))
            except re.error:
                pass
            continue

        if line.startswith("+."):
            _remember_first(index.suffixes, normalize_domain(line[2:]), line_no, line)
        elif line.startswith("."):
            _remember_first(index.suffixes, normalize_domain(line[1:]), line_no, line)
        else:
            _remember_first(index.suffixes, normalize_domain(line), line_no, line)
    return index


def match_domain_entry(domain: str, entry: str) -> Optional[str]:
    """Linear single-entry matcher kept for tests and ad-hoc use."""
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


class RouteEngine:
    """Process-local route diagnosis with shared indexes and geo output cache."""

    def __init__(self, cache_dir: Path, geo_bin: str = "geo") -> None:
        self.cache_dir = cache_dir
        self.geo_bin = geo_bin
        self._templates: Dict[Path, Template] = {}
        self._domain_indexes: Dict[Path, DomainProviderIndex] = {}
        self._geo_output: Dict[Tuple[str, str, str], str] = {}
        self._geo_variant: Optional[int] = None
        self._geo_lock = threading.Lock()

    def load_template(self, path: Path) -> Template:
        resolved = path.resolve()
        cached = self._templates.get(resolved)
        if cached is None:
            cached = parse_template(resolved)
            self._templates[resolved] = cached
        return cached

    def domain_index_for(self, path: Path) -> DomainProviderIndex:
        resolved = path.resolve()
        cached = self._domain_indexes.get(resolved)
        if cached is None:
            cached = build_domain_index(resolved)
            self._domain_indexes[resolved] = cached
        return cached

    def diagnose(self, template_path: Path, target: str) -> Dict[str, Optional[str]]:
        template = self.load_template(template_path)
        mode = template_mode(template)
        if mode == "mixed":
            return {"policy": None, "rule": None, "raw": "mixed RULE-SET and GEOSITE/GEOIP"}
        if mode == "geodata":
            return self._diagnose_geodata(template, target)
        if input_ip(target):
            return self._diagnose_ruleset_ip(template, target)
        return self._diagnose_ruleset_domain(template, target)

    def _diagnose_ruleset_domain(self, template: Template, domain: str) -> Dict[str, Optional[str]]:
        missing: List[str] = []
        for rule in template.rules:
            if not rule.parts:
                continue
            kind = rule.parts[0].upper()
            if kind == "MATCH":
                if missing:
                    return {
                        "policy": None,
                        "rule": None,
                        "raw": "missing cache: " + ", ".join(missing),
                    }
                return {"policy": policy_from_rule(rule.parts), "rule": rule.raw}
            if kind == "GEOIP":
                continue
            if kind != "RULE-SET" or len(rule.parts) < 3:
                continue

            provider = template.providers.get(rule.parts[1])
            if not provider:
                continue
            if provider.behavior.lower() == "ipcidr":
                continue

            provider_file = resolve_provider_file(provider, self.cache_dir)
            if not provider_file:
                missing.append(provider.name)
                continue

            matched = self.domain_index_for(provider_file).match(domain)
            if matched:
                return {
                    "policy": policy_from_rule(rule.parts),
                    "rule": rule.raw,
                    "match": matched[1],
                    "provider": provider.name,
                }
        if missing:
            return {
                "policy": None,
                "rule": None,
                "raw": "missing cache: " + ", ".join(missing),
            }
        return {"policy": None, "rule": None}

    def _diagnose_ruleset_ip(self, template: Template, target: str) -> Dict[str, Optional[str]]:
        ip = input_ip(target)
        assert ip is not None
        missing: List[str] = []
        for rule in template.rules:
            if not rule.parts:
                continue
            kind = rule.parts[0].upper()
            if kind == "MATCH":
                if missing:
                    return {
                        "policy": None,
                        "rule": None,
                        "raw": "missing cache: " + ", ".join(missing),
                    }
                return {"policy": policy_from_rule(rule.parts), "rule": rule.raw}
            if kind != "RULE-SET" or len(rule.parts) < 3:
                continue
            provider = template.providers.get(rule.parts[1])
            if not provider or provider.behavior.lower() == "domain":
                continue
            provider_file = resolve_provider_file(provider, self.cache_dir)
            if not provider_file:
                missing.append(provider.name)
                continue
            for _, entry in iter_provider_lines(provider_file):
                matched = match_ip_entry(ip, entry)
                if matched:
                    return {
                        "policy": policy_from_rule(rule.parts),
                        "rule": rule.raw,
                        "match": matched,
                        "provider": provider.name,
                    }
        if missing:
            return {
                "policy": None,
                "rule": None,
                "raw": "missing cache: " + ", ".join(missing),
            }
        return {"policy": None, "rule": None}

    def _geo_variants(self, data_dir: Path, target: str, no_resolve: bool) -> List[List[str]]:
        no_resolve_args = ["--no-resolve"] if no_resolve else []
        return [
            [self.geo_bin, "look", "-D", str(data_dir), *no_resolve_args, target],
            [self.geo_bin, "look", "--data-dir", str(data_dir), *no_resolve_args, target],
            [self.geo_bin, "-D", str(data_dir), "look", *no_resolve_args, target],
            [self.geo_bin, "look", *no_resolve_args, "-d", str(data_dir), target],
        ]

    def run_geo_look(
        self, data_dir: Path, target: str, no_resolve: bool
    ) -> Tuple[int, str, str, List[str]]:
        variants = self._geo_variants(data_dir, target, no_resolve)
        order = list(range(len(variants)))
        if self._geo_variant is not None:
            order = [self._geo_variant] + [index for index in order if index != self._geo_variant]

        tried: List[str] = []
        last_stdout = ""
        last_stderr = ""
        for index in order:
            command = variants[index]
            tried.append(" ".join(command))
            try:
                proc = subprocess.run(
                    command,
                    check=False,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                )
            except FileNotFoundError:
                return 127, "", f"{self.geo_bin} not found on PATH", tried
            last_stdout, last_stderr = proc.stdout, proc.stderr
            if proc.returncode == 0:
                with self._geo_lock:
                    if self._geo_variant is None:
                        self._geo_variant = index
                return 0, proc.stdout, proc.stderr, tried
        return 1, last_stdout, last_stderr, tried

    def geo_output(
        self, data_dir: Path, target: str, no_resolve: bool
    ) -> Tuple[int, str, str, List[str]]:
        key = (str(data_dir.resolve()), target, "1" if no_resolve else "0")
        with self._geo_lock:
            cached = self._geo_output.get(key)
            if cached is not None:
                return 0, cached, "", ["(cache)"]
        code, stdout, stderr, tried = self.run_geo_look(data_dir, target, no_resolve)
        if code == 0:
            combined = stdout + "\n" + stderr
            with self._geo_lock:
                self._geo_output.setdefault(key, combined)
            return 0, combined, "", tried
        return code, stdout, stderr, tried


    def _diagnose_geodata(self, template: Template, target: str) -> Dict[str, Optional[str]]:
        ip = input_ip(target)
        mode = "ip" if ip else "domain"
        candidates = [
            rule.parts[1]
            for rule in template.rules
            if len(rule.parts) >= 2 and rule.parts[0].upper() in {"GEOSITE", "GEOIP"}
        ]

        if ip:
            geo_url = template.geox.get("mmdb") or template.geox.get("geoip")
            geo_kind = "mmdb" if template.geox.get("mmdb") else "geoip"
        else:
            geo_url = template.geox.get("geosite")
            geo_kind = "geosite"
        if not geo_url:
            return {"policy": None, "rule": None, "raw": f"missing geox-url.{geo_kind}"}

        geo_file = cache_file(self.cache_dir, "geo", geo_url)
        if not geo_file:
            return {"policy": None, "rule": None, "raw": f"missing cache: {geo_kind}"}

        code, output, stderr, tried = self.geo_output(geo_file.parent, target, no_resolve=not ip)
        if code != 0:
            return {
                "policy": None,
                "rule": None,
                "raw": "geo look failed: " + " | ".join(tried[:2]),
            }

        matches = extract_geo_matches(output if output else stderr, candidates)
        match_set = set(matches)
        for rule in template.rules:
            if len(rule.parts) < 3:
                continue
            kind = rule.parts[0].upper()
            tag = rule.parts[1]
            if mode == "domain" and kind != "GEOSITE":
                continue
            if mode == "ip" and kind != "GEOIP":
                continue
            if tag in match_set:
                return {
                    "policy": policy_from_rule(rule.parts),
                    "rule": rule.raw,
                    "match": tag,
                }
        return {"policy": None, "rule": None}


def explain_ruleset(template: Template, target: str, cache_dir: Path) -> int:
    engine = RouteEngine(cache_dir)
    ip = input_ip(target)
    mode = "ip" if ip else "domain"
    print(f"template: {template.path.relative_to(REPO_ROOT)}")
    print("mode: ruleset")
    print(f"input: {target}")
    print(f"input type: {mode}")
    print()

    result = engine.diagnose(template.path, target)
    raw = result.get("raw") or ""
    if raw.startswith("missing cache:"):
        missing = raw.removeprefix("missing cache: ").split(", ")
        print("missing cache:")
        for missing_name in missing:
            provider = template.providers.get(missing_name)
            print(f"  - {missing_name}: {provider.url if provider else ''}")
        print()
        print("run:")
        print(
            "  .agents/skills/sift-route-debug/scripts/update_cache.py "
            f"{template.path.relative_to(REPO_ROOT)}"
        )
        return 2

    if result.get("policy") and result.get("rule"):
        line_no = next(
            (rule.line_no for rule in template.rules if rule.raw == result["rule"]),
            "?",
        )
        print("first matched rule:")
        print(f"  line: {line_no}")
        print(f"  template rule: {result['rule']}")
        if result.get("provider"):
            provider = template.providers.get(str(result["provider"]))
            print(f"  provider: {result['provider']}")
            if provider:
                print(f"  provider behavior: {provider.behavior or '(unknown)'}")
                print(f"  provider source: {provider.url or provider.path}")
            if result.get("match"):
                print(f"  provider match: {result['match']}")
        print(f"  policy: {result['policy']}")
        if mode == "domain":
            print()
            print("notes:")
            print("  IP providers were skipped for domain-only diagnosis.")
        return 0

    print("no matching rule found")
    if mode == "domain":
        print()
        print("notes:")
        print("  Domain diagnosis skipped IP providers; runtime may route by resolved IP.")
    return 1


def run_geo_look(
    geo_bin: str, data_dir: Path, target: str, no_resolve: bool
) -> Tuple[int, str, str, List[str]]:
    """Backward-compatible wrapper used by older callers/tests."""
    return RouteEngine(DEFAULT_CACHE, geo_bin).run_geo_look(data_dir, target, no_resolve)


def extract_geo_matches(output: str, candidates: Sequence[str]) -> List[str]:
    matches: List[str] = []
    for tag in candidates:
        pattern = re.compile(
            r"(?<![A-Za-z0-9_@!.-])" + re.escape(tag) + r"(?![A-Za-z0-9_@!.-])",
            re.I,
        )
        if pattern.search(output):
            matches.append(tag)
    return matches


def explain_geodata(template: Template, target: str, cache_dir: Path, geo_bin: str) -> int:
    engine = RouteEngine(cache_dir, geo_bin)
    ip = input_ip(target)
    mode = "ip" if ip else "domain"
    candidates = [
        rule.parts[1]
        for rule in template.rules
        if len(rule.parts) >= 2 and rule.parts[0].upper() in {"GEOSITE", "GEOIP"}
    ]

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
        print(
            "  .agents/skills/sift-route-debug/scripts/update_cache.py "
            f"{template.path.relative_to(REPO_ROOT)}"
        )
        return 2

    print("geo source:")
    print(f"  {geo_kind}: {geo_url}")
    print(f"  cache: {geo_file.relative_to(REPO_ROOT)}")
    print()

    code, output, stderr, tried = engine.geo_output(geo_file.parent, target, no_resolve=not ip)
    if code != 0:
        print("[FAIL] unable to query geo database")
        print("tried:")
        for command in tried:
            print(f"  - {command}")
        if stderr.strip():
            print("stderr:")
            print(stderr.strip())
        if output.strip():
            print("stdout:")
            print(output.strip())
        return 2

    matches = extract_geo_matches(output, candidates)
    if matches:
        print("matched geo tags:")
        for match in matches:
            print(f"  - {match}")
    else:
        print("matched geo tags: none found in geo output")
        print()
        print("raw geo output:")
        print(output.strip() or stderr.strip() or "(empty)")

    result = engine.diagnose(template.path, target)
    if result.get("policy") and result.get("rule"):
        line_no = next(
            (rule.line_no for rule in template.rules if rule.raw == result["rule"]),
            "?",
        )
        print()
        print("first matched rule:")
        print(f"  line: {line_no}")
        print(f"  template rule: {result['rule']}")
        print(f"  policy: {result['policy']}")
        if mode == "domain":
            print()
            print("notes:")
            print("  Domain mode used no-resolve; GEOIP rules were not evaluated.")
        return 0

    print()
    print("no matching geodata rule found")
    return 1


def template_mode(template: Template) -> str:
    has_ruleset = any(
        rule.parts and rule.parts[0].upper() == "RULE-SET" for rule in template.rules
    )
    has_geo = any(
        rule.parts and rule.parts[0].upper() in {"GEOSITE", "GEOIP"} for rule in template.rules
    )
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

    cache_dir = args.cache_dir if args.cache_dir.is_absolute() else REPO_ROOT / args.cache_dir
    template = parse_template(template_path)
    mode = template_mode(template)
    if mode == "mixed":
        print(
            "[FAIL] mixed RULE-SET and GEOSITE/GEOIP rules are not supported",
            file=sys.stderr,
        )
        return 2
    if mode == "geodata":
        return explain_geodata(template, args.target, cache_dir, args.geo_bin)
    return explain_ruleset(template, args.target, cache_dir)


if __name__ == "__main__":
    raise SystemExit(main())
