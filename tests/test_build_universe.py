"""Hermetic unit tests for scripts/build_universe.py.

Covers deterministic/pure seams: constants, symbol mappings, and sha256_file.
No network access, no dependency on committed panel artifacts, no frozen
artifact or config modification.
"""

from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_universe.py"


def _load():
    spec = importlib.util.spec_from_file_location("build_universe_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestBuildUniverseConstants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_experiment_id(self):
        self.assertEqual(self.mod.EXP, "HARMONY-CRYPTO-EDGE-004-DISPERSION-002")

    def test_panel_dir_under_artifacts(self):
        self.assertTrue(str(self.mod.PANEL_DIR).endswith(
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/data/panels"
        ))

    def test_symbol_map_has_expected_size(self):
        self.assertEqual(len(self.mod.SYMBOL_MAP), 28)

    def test_symbol_map_is_asset_to_binance_usdm_symbol(self):
        self.assertEqual(self.mod.SYMBOL_MAP["btc"], "BTCUSDT")
        self.assertEqual(self.mod.SYMBOL_MAP["eth"], "ETHUSDT")
        self.assertTrue(all(v.endswith("USDT") for v in self.mod.SYMBOL_MAP.values()))

    def test_symbol_to_asset_is_exact_inverse(self):
        self.assertEqual(len(self.mod.SYMBOL_TO_ASSET), len(self.mod.SYMBOL_MAP))
        for asset, symbol in self.mod.SYMBOL_MAP.items():
            self.assertEqual(self.mod.SYMBOL_TO_ASSET[symbol], asset)

    def test_known_legacy_assets_present(self):
        expected = {"btc", "eth", "sol", "bnb", "xrp", "ada", "doge", "ltc"}
        self.assertTrue(expected.issubset(set(self.mod.SYMBOL_MAP)))


class TestSha256File(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_sha256_file_matches_hashlib(self):
        payload = b"universe-coverage-test-payload\n"
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "sample.bin"
            p.write_bytes(payload)
            got = self.mod.sha256_file(p)
        self.assertEqual(got, hashlib.sha256(payload).hexdigest())

    def test_sha256_file_deterministic(self):
        payload = b"deterministic"
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "a.txt"
            p.write_bytes(payload)
            h1 = self.mod.sha256_file(p)
            h2 = self.mod.sha256_file(p)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)


if __name__ == "__main__":
    unittest.main()
