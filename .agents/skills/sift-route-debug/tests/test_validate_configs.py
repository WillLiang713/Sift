from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock
from urllib.parse import urlparse


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate_configs as vc  # noqa: E402
import matrix_route as mr  # noqa: E402
import update_cache as uc  # noqa: E402

# cdn.jsdelivr.net 在中国移动直连会被 RST，规则集只能直连拉取，故固定用同源的 Fastly 边缘。
ALLOWED_PROVIDER_HOSTS = {"fastly.jsdelivr.net"}


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
        self.assertEqual(
            [path.relative_to(vc.REPO_ROOT).as_posix() for path in templates],
            ["rules/core.yaml", "rules/full.yaml", "rules/gfwlist.yaml"],
        )

    def test_rule_provider_hosts_stay_mobile_friendly(self) -> None:
        for path in vc.discover_templates([]):
            relative = path.relative_to(vc.REPO_ROOT).as_posix()
            for name, fields in uc.parse_template(path)["providers"].items():
                host = urlparse(fields.get("url", "")).hostname or ""
                with self.subTest(template=relative, provider=name):
                    self.assertIn(
                        host,
                        ALLOWED_PROVIDER_HOSTS,
                        f"{relative} 的 {name} 使用 {host}，移动网络直连拉取不可靠",
                    )

    def test_cache_collects_fake_ip_filter_provider(self) -> None:
        templates = vc.discover_templates([])
        for path in templates:
            relative = path.relative_to(vc.REPO_ROOT).as_posix()
            parsed = uc.parse_template(path)
            with self.subTest(template=relative):
                self.assertIn("fakeip-filter", parsed["providers"])
                self.assertIn("fakeip-filter", parsed["used_providers"])

        jobs, _ = uc.collect_jobs(templates)
        labels = {job.names[0] for job in jobs}
        self.assertIn("fakeip-filter", labels)

    def test_route_matrix_covers_every_repository_template(self) -> None:
        discovered = {
            path.relative_to(vc.REPO_ROOT).as_posix() for path in vc.discover_templates([])
        }
        self.assertEqual(set(mr.TEMPLATES.values()), discovered)


if __name__ == "__main__":
    unittest.main()
