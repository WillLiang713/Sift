from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import explain_route as er  # noqa: E402
class MrsDiagnosticsTest(unittest.TestCase):
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
