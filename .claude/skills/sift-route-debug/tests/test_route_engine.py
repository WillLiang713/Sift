from __future__ import annotations

import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import explain_route as er  # noqa: E402
import matrix_route as mr  # noqa: E402


class DomainProviderIndexTest(unittest.TestCase):
    def test_cache_refresh_failure_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            failed = mock.Mock(returncode=1)
            with mock.patch.object(mr.subprocess, "run", return_value=failed):
                self.assertFalse(mr.update_all_caches(Path(temp_dir), ["HY-f"]))

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

    def test_geo_output_disk_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache = root / "cache"
            data_dir = root / "geo-data"
            data_dir.mkdir()
            (data_dir / "geosite.dat").write_bytes(b"fake-geosite-v1")

            engine = er.RouteEngine(cache, geo_bin="geo-not-used")
            calls = {"n": 0}

            def fake_look(
                data_dir_arg: Path, target: str, no_resolve: bool
            ) -> tuple[int, str, str, list[str]]:
                calls["n"] += 1
                return 0, f"tags: google\ntarget={target}\n", "", ["fake"]

            engine.run_geo_look = fake_look  # type: ignore[method-assign]

            code1, out1, _, tried1 = engine.geo_output(data_dir, "www.google.com", True)
            self.assertEqual(code1, 0)
            self.assertEqual(calls["n"], 1)
            self.assertNotIn("cache", tried1[0])

            disk = engine.geo_look_disk_path(data_dir, "www.google.com", True)
            self.assertTrue(disk.is_file())
            self.assertIn("google", disk.read_text(encoding="utf-8"))

            # New engine: memory empty, must hit disk without calling geo.
            engine2 = er.RouteEngine(cache, geo_bin="geo-not-used")
            engine2.run_geo_look = fake_look  # type: ignore[method-assign]
            code2, out2, _, tried2 = engine2.geo_output(data_dir, "www.google.com", True)
            self.assertEqual(code2, 0)
            self.assertEqual(out2, out1)
            self.assertEqual(calls["n"], 1)
            self.assertEqual(tried2, ["(disk-cache)"])

            # Same process memory hit.
            code3, _, _, tried3 = engine2.geo_output(data_dir, "www.google.com", True)
            self.assertEqual(code3, 0)
            self.assertEqual(tried3, ["(mem-cache)"])
            self.assertEqual(calls["n"], 1)

            # Changing geosite bytes/mtime invalidates fingerprint → re-run geo.
            (data_dir / "geosite.dat").write_bytes(b"fake-geosite-v2")
            engine3 = er.RouteEngine(cache, geo_bin="geo-not-used")
            engine3.run_geo_look = fake_look  # type: ignore[method-assign]
            code4, _, _, tried4 = engine3.geo_output(data_dir, "www.google.com", True)
            self.assertEqual(code4, 0)
            self.assertEqual(calls["n"], 2)
            self.assertEqual(tried4, ["fake"])


if __name__ == "__main__":
    unittest.main()
