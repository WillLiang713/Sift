from __future__ import annotations

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
        self.assertEqual(len(templates), 12)
        self.assertIn(vc.REPO_ROOT / "rules" / "full.yaml", templates)


if __name__ == "__main__":
    unittest.main()
