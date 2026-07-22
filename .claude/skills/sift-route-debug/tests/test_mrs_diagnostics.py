from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import explain_route as er  # noqa: E402
import update_cache as uc  # noqa: E402


class MrsDiagnosticsTest(unittest.TestCase):
    def test_primary_template_anchor_and_indented_rules_are_parsed(self) -> None:
        template = """\
rule-anchor:
  mrs-domain: &mrs-domain {type: http, behavior: domain, format: mrs}
  mrs-ip: &mrs-ip {type: http, behavior: ipcidr, format: mrs}
rule-providers:
  proxy:
    <<: *mrs-domain
    url: https://example.test/proxy.mrs
  cnip:
    <<: *mrs-ip
    url: https://example.test/cnip.mrs
rules:
  - RULE-SET,proxy,节点选择
  - RULE-SET,cnip,全球直连
  - MATCH,节点选择
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.yaml"
            path.write_text(template, encoding="utf-8")

            explained = er.parse_template(path)
            cached = uc.parse_template(path)

        self.assertEqual(explained.providers["proxy"].behavior, "domain")
        self.assertEqual(explained.providers["cnip"].behavior, "ipcidr")
        self.assertEqual(len(explained.rules), 3)
        self.assertEqual(cached["used_providers"], {"proxy", "cnip"})
        self.assertEqual(cached["providers"]["proxy"]["format"], "mrs")

    def test_mrs_provider_uses_decoded_text_cache(self) -> None:
        source = "https://example.test/rules/cnip.mrs"
        provider = er.Provider(name="cnip", behavior="ipcidr", format="mrs", url=source)
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            directory = cache_dir / "ruleset" / er.cache_key(source)
            directory.mkdir(parents=True)
            companion = directory / "cnip.list"
            companion.write_text("2402:f000::/32\n", encoding="utf-8")
            (directory / "manifest.json").write_text(
                json.dumps(
                    {
                        "source_url": source,
                        "url": source,
                        "file": companion.name,
                        "source_file": "cnip.mrs",
                        "source_format": "mrs",
                        "format": "text",
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(er.resolve_provider_file(provider, cache_dir), companion)
            self.assertEqual(
                er.match_ip_entry(er.input_ip("2402:f000:1:400::2"), companion.read_text()),
                "2402:f000::/32",
            )

    def test_mrs_provider_rejects_binary_cache(self) -> None:
        source = "https://example.test/rules/cnip.mrs"
        provider = er.Provider(name="cnip", behavior="ipcidr", format="mrs", url=source)
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            directory = cache_dir / "ruleset" / er.cache_key(source)
            directory.mkdir(parents=True)
            binary = directory / "cnip.mrs"
            binary.write_bytes(b"MRS\x00\x01")
            (directory / "manifest.json").write_text(
                json.dumps({"url": source, "file": binary.name}),
                encoding="utf-8",
            )

            self.assertIsNone(er.resolve_provider_file(provider, cache_dir))


if __name__ == "__main__":
    unittest.main()
