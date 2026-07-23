from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import explain_route as er  # noqa: E402


class DomainProviderIndexTest(unittest.TestCase):
    def test_first_match_order_and_suffix_exact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "rules.list"
            path.write_text(
                "\n".join(
                    [
                        "DOMAIN-SUFFIX,example.com",
                        "DOMAIN,www.example.com",
                        "DOMAIN-KEYWORD,ads",
                        "+.cdn.example.com",
                        "DOMAIN-REGEX,^foo[0-9]+\\.bar$",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            index = er.build_domain_index(path)

            # Earlier broader suffix wins over later more-specific entries.
            self.assertEqual(index.match("www.example.com")[1], "DOMAIN-SUFFIX,example.com")
            self.assertEqual(index.match("a.cdn.example.com")[1], "DOMAIN-SUFFIX,example.com")
            self.assertEqual(index.match("tracker-ads.example.org")[1], "DOMAIN-KEYWORD,ads")
            self.assertEqual(index.match("foo12.bar")[1], "DOMAIN-REGEX,^foo[0-9]+\\.bar$")
            self.assertIsNone(index.match("unrelated.test"))

            # When the specific suffix is listed first, it wins for that host.
            path.write_text("+.cdn.example.com\nDOMAIN-SUFFIX,example.com\n", encoding="utf-8")
            index = er.build_domain_index(path)
            self.assertEqual(index.match("a.cdn.example.com")[1], "+.cdn.example.com")
            self.assertEqual(index.match("www.example.com")[1], "DOMAIN-SUFFIX,example.com")

    def test_route_engine_ruleset_domain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache = root / "cache"
            ruleset_dir = cache / "ruleset" / er.cache_key("https://example.test/ads.list")
            ruleset_dir.mkdir(parents=True)
            (ruleset_dir / "ads.list").write_text("DOMAIN-SUFFIX,doubleclick.net\n", encoding="utf-8")
            (ruleset_dir / "manifest.json").write_text(
                '{"url":"https://example.test/ads.list","file":"ads.list"}\n',
                encoding="utf-8",
            )
            template = root / "t.yaml"
            template.write_text(
                "\n".join(
                    [
                        "rule-providers:",
                        "  ads:",
                        "    type: http",
                        "    behavior: domain",
                        "    format: text",
                        "    url: https://example.test/ads.list",
                        "rules:",
                        "  - RULE-SET,ads,广告拦截",
                        "  - MATCH,节点选择",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            engine = er.RouteEngine(cache)
            hit = engine.diagnose(template, "ad.doubleclick.net")
            miss = engine.diagnose(template, "www.baidu.com")
            self.assertEqual(hit.get("policy"), "广告拦截")
            self.assertEqual(miss.get("policy"), "节点选择")


if __name__ == "__main__":
    unittest.main()
