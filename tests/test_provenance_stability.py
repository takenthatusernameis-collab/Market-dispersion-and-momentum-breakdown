"""Regression tests for provenance-manifest stability under no-op refreshes.

The sealed DISPERSION-003 forward block records SHA-256 hashes over the panel
manifests (``binance_panel_manifest.json``, ``data_refresh_provenance.json``,
``marketcap_panel_manifest.json``) and the candidate validation record. A data
refresh that changes nothing must therefore leave those files byte-identical;
otherwise ``test_forward_block_hashes_match_files_on_disk`` fails even though
no data moved.

These tests cover the ``preserve_fetch_utc_if_unchanged`` helper used by
``scripts/refresh_free_data.py`` and ``scripts/validate_candidate_batch.py``,
including the order-independent Binance ``series`` signature (the series are
collected via a thread pool, so their order is not reproducible run to run).
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _import_helpers():
    import importlib.util

    for name, script in (
        ("rfd", ROOT / "scripts" / "refresh_free_data.py"),
        ("vcb", ROOT / "scripts" / "validate_candidate_batch.py"),
    ):
        spec = importlib.util.spec_from_file_location(name, script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        yield mod


class ProvenanceStabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._modules = {m.__name__: m for m in _import_helpers()}

    def _with(self, attr):
        """Yield every loaded module that exposes ``attr``."""
        for mod in self._modules.values():
            if hasattr(mod, attr):
                yield mod

    def test_helper_preserves_fetch_utc_when_data_unchanged(self):
        for mod in self._with("preserve_fetch_utc_if_unchanged"):
            helper = mod.preserve_fetch_utc_if_unchanged
            sig = mod._series_sig
            new = {"fetch_utc": "2026-10-24T14:00:00Z", "series": [{"asset": "btc", "kind": "klines"}]}
            existing = {"fetch_utc": "2026-10-24T12:46:42Z", "series": [{"asset": "btc", "kind": "klines"}]}
            path = Path("/tmp/_provenance_stability_test.json")
            path.write_text(json.dumps(existing))
            skip = helper(path, new, sig)
            self.assertTrue(skip, "no-op refresh should skip writing")
            self.assertEqual(new["fetch_utc"], existing["fetch_utc"],
                             "fetch_utc must be preserved when data is unchanged")
            self.assertEqual(path.read_bytes(), json.dumps(existing).encode(),
                             "committed file must stay byte-identical")

    def test_helper_writes_when_data_changes(self):
        for mod in self._with("preserve_fetch_utc_if_unchanged"):
            helper = mod.preserve_fetch_utc_if_unchanged
            sig = mod._series_sig
            new = {"fetch_utc": "2026-10-24T14:00:00Z", "series": [{"asset": "btc", "kind": "klines", "rows": 100}]}
            existing = {"fetch_utc": "2026-10-24T12:46:42Z", "series": [{"asset": "btc", "kind": "klines", "rows": 99}]}
            path = Path("/tmp/_provenance_stability_test2.json")
            path.write_text(json.dumps(existing))
            skip = helper(path, new, sig)
            self.assertFalse(skip, "changed data must be written")
            self.assertEqual(new["fetch_utc"], "2026-10-24T14:00:00Z",
                             "new fetch_utc must be kept when data changed")

    def test_series_signature_is_order_independent(self):
        for mod in self._with("_series_sig"):
            sig = mod._series_sig
            a = {"series": [{"asset": "btc", "kind": "klines"}, {"asset": "eth", "kind": "funding"}]}
            b = {"series": [{"asset": "eth", "kind": "funding"}, {"asset": "btc", "kind": "klines"}]}
            self.assertEqual(sig(a), sig(b),
                             "series order must not affect the signature")
            c = {"series": [{"asset": "btc", "kind": "klines", "rows": 100}]}
            self.assertNotEqual(sig(a), sig(c),
                                "a real data change must change the signature")

    def test_series_signature_recurses_into_nested_dicts(self):
        for mod in self._with("_series_sig"):
            sig = mod._series_sig
            nested = {
                "binance": {
                    "series": [{"asset": "eth", "kind": "funding"}],
                },
                "series": [{"asset": "btc", "kind": "klines"}],
            }
            out = sig(nested)
            self.assertEqual(out["binance"]["series"],
                             [{"asset": "eth", "kind": "funding"}])
            self.assertEqual(out["series"],
                             [{"asset": "btc", "kind": "klines"}])


if __name__ == "__main__":
    unittest.main()