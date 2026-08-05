from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate_configs as vc  # noqa: E402


class ValidateConfigsTest(unittest.TestCase):
    def test_platform_aliases(self) -> None:
        with mock.patch.object(vc.platform, "system", return_value="Windows"), mock.patch.object(
            vc.platform, "machine", return_value="AMD64"
        ):
            self.assertEqual(vc.platform_id(), ("windows", "amd64", ".zip"))

    def test_selects_compatible_amd64_release_asset_first(self) -> None:
        release = {
            "assets": [
                {"name": "mihomo-linux-amd64-v1.2.3.gz"},
                {"name": "mihomo-linux-amd64-compatible-v1.2.3.gz"},
            ]
        }
        asset = vc.select_asset(release, "linux", "amd64", ".gz", "v1.2.3")
        self.assertEqual(asset["name"], "mihomo-linux-amd64-compatible-v1.2.3.gz")

    def test_falls_back_to_plain_amd64_release_asset(self) -> None:
        release = {"assets": [{"name": "mihomo-linux-amd64-v1.2.3.gz"}]}
        asset = vc.select_asset(release, "linux", "amd64", ".gz", "v1.2.3")
        self.assertEqual(asset["name"], "mihomo-linux-amd64-v1.2.3.gz")

    def test_selects_plain_non_amd64_release_asset_first(self) -> None:
        release = {
            "assets": [
                {"name": "mihomo-linux-arm64-compatible-v1.2.3.gz"},
                {"name": "mihomo-linux-arm64-v1.2.3.gz"},
            ]
        }
        asset = vc.select_asset(release, "linux", "arm64", ".gz", "v1.2.3")
        self.assertEqual(asset["name"], "mihomo-linux-arm64-v1.2.3.gz")

    def test_rejects_unusable_cached_binary(self) -> None:
        result = mock.Mock(returncode=1)
        with mock.patch.object(vc.subprocess, "run", return_value=result):
            self.assertFalse(vc.binary_is_usable(Path("mihomo")))

    def test_discovers_all_repository_templates(self) -> None:
        templates = vc.discover_templates([])
        self.assertEqual(len(templates), 3)
        self.assertIn(vc.REPO_ROOT / "rules" / "full.yaml", templates)

    def test_full_region_filters_cover_expected_node_names(self) -> None:
        text = (vc.REPO_ROOT / "rules" / "full.yaml").read_text(encoding="utf-8")

        def anchor(name: str) -> str:
            match = re.search(rf'^  {name}: &{name} "(.*)"$', text, re.MULTILINE)
            self.assertIsNotNone(match, f"missing {name} anchor")
            return match.group(1)

        filters = {
            "filter-hk": anchor("filter-hk"),
            "filter-us": anchor("filter-us"),
            "filter-jp": anchor("filter-jp"),
            "filter-sg": anchor("filter-sg"),
        }
        fixtures = {
            "filter-hk": ["🇭🇰 香港 01", "HK-HKG-01"],
            "filter-us": ["US-LAX-01", "Seattle Premium"],
            "filter-jp": ["JP-NRT-01", "日本 东京"],
            "filter-sg": ["SG-SIN-01", "Singapore 01"],
        }
        for name, node_names in fixtures.items():
            regex = re.compile(filters[name])
            for node_name in node_names:
                self.assertRegex(node_name, regex)

        self.assertNotRegex("Russia Premium", re.compile(filters["filter-us"]))
        self.assertNotRegex("Business Premium", re.compile(filters["filter-sg"]))

    def test_other_region_filter_is_exact_union(self) -> None:
        text = (vc.REPO_ROOT / "rules" / "full.yaml").read_text(encoding="utf-8")

        def anchor(name: str) -> str:
            match = re.search(rf'^  {name}: &{name} "(.*)"$', text, re.MULTILINE)
            self.assertIsNotNone(match, f"missing {name} anchor")
            return match.group(1)

        region_filters = [anchor(name) for name in ("filter-hk", "filter-us", "filter-jp", "filter-sg")]
        expected = "(?i)" + "|".join(pattern.removeprefix("(?i)") for pattern in region_filters)
        self.assertEqual(anchor("other-region-exclude"), expected)


if __name__ == "__main__":
    unittest.main()
