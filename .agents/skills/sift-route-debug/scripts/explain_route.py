#!/usr/bin/env python3
"""Explain the first matching Sift route rule for a domain or IP."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import sys
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

    return Template(path=path, providers=providers, rules=rules)


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
    """Process-local route diagnosis with shared provider indexes."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self._templates: Dict[Path, Template] = {}
        self._domain_indexes: Dict[Path, DomainProviderIndex] = {}

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
            if kind in ("DOMAIN", "DOMAIN-SUFFIX") and len(rule.parts) >= 3:
                target = normalize_domain(domain)
                value = normalize_domain(rule.parts[1])
                if target == value or (kind == "DOMAIN-SUFFIX" and target.endswith("." + value)):
                    return {"policy": policy_from_rule(rule.parts), "rule": rule.raw}
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", help="Template YAML file")
    parser.add_argument("target", help="Domain or IP to diagnose")
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    args = parser.parse_args()

    template_path = Path(args.template)
    if not template_path.is_absolute():
        template_path = REPO_ROOT / template_path
    if not template_path.exists():
        print(f"[FAIL] template not found: {args.template}", file=sys.stderr)
        return 2

    cache_dir = args.cache_dir if args.cache_dir.is_absolute() else REPO_ROOT / args.cache_dir
    template = parse_template(template_path)
    return explain_ruleset(template, args.target, cache_dir)


if __name__ == "__main__":
    raise SystemExit(main())
