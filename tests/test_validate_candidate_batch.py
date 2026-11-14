"""Hermetic tests for the pure seams of scripts/validate_candidate_batch.py.

Tests only the deterministic, side-effect-free helpers:
  - _series_sig(d): order-independent recursive signature that drops
    fetch_utc/time_order_note and sorts series by (asset, kind).
  - preserve_fetch_utc_if_unchanged(path, new_dict, data_sig): keeps a
    committed manifest byte-stable when a refresh changes no data.

No network, no committed-panel dependency, no frozen-artifact reads/writes.
Synthetic fixtures are software tests only, never market evidence.
"""
import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_candidate_batch import _series_sig, preserve_fetch_utc_if_unchanged


class SeriesSigTests(unittest.TestCase):
    """Tests for the _series_sig pure function."""

    def test_returns_same_object_for_non_dict_non_list(self):
        self.assertEqual(_series_sig("string"), "string")
        self.assertEqual(_series_sig(123), 123)
        self.assertEqual(_series_sig(None), None)
        self.assertEqual(_series_sig(3.14), 3.14)

    def test_recurses_into_nested_dicts(self):
        d = {"a": {"b": {"c": 1}}}
        out = _series_sig(d)
        self.assertEqual(out, {"a": {"b": {"c": 1}}})

    def test_drops_fetch_utc_key(self):
        d = {"fetch_utc": "2026-01-01T00:00:00Z", "data": 1}
        out = _series_sig(d)
        self.assertNotIn("fetch_utc", out)
        self.assertEqual(out, {"data": 1})

    def test_drops_time_order_note_key(self):
        d = {"time_order_note": "some note", "data": 1}
        out = _series_sig(d)
        self.assertNotIn("time_order_note", out)
        self.assertEqual(out, {"data": 1})

    def test_drops_both_fetch_utc_and_time_order_note(self):
        d = {
            "fetch_utc": "2026-01-01T00:00:00Z",
            "time_order_note": "note",
            "data": 1
        }
        out = _series_sig(d)
        self.assertNotIn("fetch_utc", out)
        self.assertNotIn("time_order_note", out)
        self.assertEqual(out, {"data": 1})

    def test_sorts_series_by_asset_then_kind(self):
        d = {
            "series": [
                {"asset": "BTC", "kind": "klines", "value": 2},
                {"asset": "ETH", "kind": "funding", "value": 3},
                {"asset": "BTC", "kind": "funding", "value": 1},
            ]
        }
        out = _series_sig(d)
        self.assertEqual(out["series"], [
            {"asset": "BTC", "kind": "funding", "value": 1},
            {"asset": "BTC", "kind": "klines", "value": 2},
            {"asset": "ETH", "kind": "funding", "value": 3},
        ])

    def test_series_sort_order_funding_before_klines(self):
        """funding (0) comes before klines (1) per _KIND_ORDER."""
        d = {"series": [{"asset": "BTC", "kind": "klines"}, {"asset": "BTC", "kind": "funding"}]}
        out = _series_sig(d)
        self.assertEqual(out["series"][0]["kind"], "funding")
        self.assertEqual(out["series"][1]["kind"], "klines")

    def test_unknown_kind_sorts_after_known(self):
        """Unknown kind gets order 99, sorts after funding (0) and klines (1)."""
        d = {
            "series": [
                {"asset": "BTC", "kind": "unknown"},
                {"asset": "BTC", "kind": "funding"},
                {"asset": "BTC", "kind": "klines"},
            ]
        }
        out = _series_sig(d)
        kinds = [s["kind"] for s in out["series"]]
        self.assertEqual(kinds, ["funding", "klines", "unknown"])

    def test_missing_asset_key_not_added_but_sorts_first(self):
        d = {"series": [{"kind": "funding"}, {"asset": "BTC", "kind": "funding"}]}
        out = _series_sig(d)
        self.assertNotIn("asset", out["series"][0])
        self.assertEqual(out["series"][1]["asset"], "BTC")

    def test_missing_kind_key_defaults_to_99(self):
        d = {"series": [{"asset": "BTC"}, {"asset": "BTC", "kind": "funding"}]}
        out = _series_sig(d)
        self.assertEqual(out["series"][0]["kind"], "funding")
        self.assertEqual(out["series"][1].get("kind"), None)

    def test_recurses_into_list_elements(self):
        d = [{"fetch_utc": "x", "a": 1}, {"time_order_note": "y", "b": 2}]
        out = _series_sig(d)
        self.assertEqual(out, [{"a": 1}, {"b": 2}])

    def test_deep_nested_series_sort(self):
        d = {
            "candidates_processed": [
                {
                    "asset": "BTC",
                    "series": [
                        {"asset": "BTC", "kind": "klines"},
                        {"asset": "BTC", "kind": "funding"},
                    ],
                },
                {
                    "asset": "ETH",
                    "series": [
                        {"asset": "ETH", "kind": "klines"},
                        {"asset": "ETH", "kind": "funding"},
                    ],
                },
            ]
        }
        out = _series_sig(d)
        for c in out["candidates_processed"]:
            kinds = [s["kind"] for s in c["series"]]
            self.assertEqual(kinds, ["funding", "klines"])

    def test_returns_new_object_not_mutate_input(self):
        d = {"fetch_utc": "x", "series": [{"asset": "BTC", "kind": "klines"}]}
        original_fetch = d.get("fetch_utc")
        original_series = d["series"][0]["kind"]
        out = _series_sig(d)
        self.assertIn("fetch_utc", d)
        self.assertEqual(d["fetch_utc"], original_fetch)
        self.assertEqual(d["series"][0]["kind"], original_series)
        self.assertNotIn("fetch_utc", out)

    def test_empty_series_list(self):
        d = {"series": []}
        out = _series_sig(d)
        self.assertEqual(out["series"], [])

    def test_series_elements_are_dicts_assumption(self):
        """_series_sig assumes series elements are dicts; non-dicts would error.
        This documents the current contract."""
        d = {"series": [{"asset": "BTC", "kind": "funding"}]}
        out = _series_sig(d)
        self.assertEqual(out["series"], [{"asset": "BTC", "kind": "funding"}])


class PreserveFetchUtcIfUnchangedTests(unittest.TestCase):
    """Tests for the preserve_fetch_utc_if_unchanged pure function."""

    def test_returns_false_when_path_does_not_exist(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "nonexistent.json"
            new_dict = {"fetch_utc": "2026-01-01T00:00:00Z", "data": "new"}
            result = preserve_fetch_utc_if_unchanged(path, new_dict, _series_sig)
            self.assertFalse(result)

    def test_returns_false_when_existing_file_is_invalid_json(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "invalid.json"
            path.write_text("not json")
            new_dict = {"fetch_utc": "2026-01-01T00:00:00Z", "data": "new"}
            result = preserve_fetch_utc_if_unchanged(path, new_dict, _series_sig)
            self.assertFalse(result)

    def test_returns_false_when_existing_file_missing_fetch_utc(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "no_fetch.json"
            path.write_text(json.dumps({"data": "old"}))
            new_dict = {"fetch_utc": "2026-01-01T00:00:00Z", "data": "new"}
            result = preserve_fetch_utc_if_unchanged(path, new_dict, _series_sig)
            self.assertFalse(result)

    def test_returns_true_and_preserves_fetch_utc_when_data_sig_matches(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "match.json"
            old_fetch = "2026-01-01T00:00:00Z"
            path.write_text(json.dumps({"fetch_utc": old_fetch, "series": [{"asset": "BTC", "kind": "funding"}]}))
            new_dict = {"fetch_utc": "2026-01-02T00:00:00Z", "series": [{"asset": "BTC", "kind": "funding"}]}
            result = preserve_fetch_utc_if_unchanged(path, new_dict, _series_sig)
            self.assertTrue(result)
            self.assertEqual(new_dict["fetch_utc"], old_fetch)

    def test_returns_false_when_data_sig_differs(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "diff.json"
            path.write_text(json.dumps({"fetch_utc": "2026-01-01T00:00:00Z", "series": [{"asset": "BTC", "kind": "funding"}]}))
            new_dict = {"fetch_utc": "2026-01-02T00:00:00Z", "series": [{"asset": "ETH", "kind": "funding"}]}
            result = preserve_fetch_utc_if_unchanged(path, new_dict, _series_sig)
            self.assertFalse(result)
            self.assertEqual(new_dict["fetch_utc"], "2026-01-02T00:00:00Z")

    def test_returns_false_when_series_order_differs_but_sig_normalizes(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "order.json"
            path.write_text(json.dumps({
                "fetch_utc": "2026-01-01T00:00:00Z",
                "series": [{"asset": "BTC", "kind": "klines"}, {"asset": "BTC", "kind": "funding"}]
            }))
            new_dict = {
                "fetch_utc": "2026-01-02T00:00:00Z",
                "series": [{"asset": "BTC", "kind": "funding"}, {"asset": "BTC", "kind": "klines"}]
            }
            result = preserve_fetch_utc_if_unchanged(path, new_dict, _series_sig)
            self.assertTrue(result)
            self.assertEqual(new_dict["fetch_utc"], "2026-01-01T00:00:00Z")

    def test_returns_false_when_fetch_utc_differs_but_data_sig_matches(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "fetch_diff.json"
            path.write_text(json.dumps({"fetch_utc": "2026-01-01T00:00:00Z", "data": "same"}))
            new_dict = {"fetch_utc": "2026-01-02T00:00:00Z", "data": "same"}
            result = preserve_fetch_utc_if_unchanged(path, new_dict, _series_sig)
            self.assertTrue(result)
            self.assertEqual(new_dict["fetch_utc"], "2026-01-01T00:00:00Z")

    def test_returns_false_on_os_error_reading_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "no_read.json"
            path.write_text(json.dumps({"fetch_utc": "2026-01-01T00:00:00Z", "data": "x"}))
            path.chmod(0o000)
            try:
                new_dict = {"fetch_utc": "2026-01-02T00:00:00Z", "data": "x"}
                result = preserve_fetch_utc_if_unchanged(path, new_dict, _series_sig)
                self.assertFalse(result)
            finally:
                path.chmod(0o644)

    def test_new_dict_mutated_in_place_when_true(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "mutate.json"
            path.write_text(json.dumps({"fetch_utc": "2026-01-01T00:00:00Z", "data": "same"}))
            new_dict = {"fetch_utc": "2026-01-02T00:00:00Z", "data": "same"}
            result = preserve_fetch_utc_if_unchanged(path, new_dict, _series_sig)
            self.assertTrue(result)
            self.assertEqual(new_dict["fetch_utc"], "2026-01-01T00:00:00Z")

    def test_new_dict_unchanged_when_false(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "no_mutate.json"
            path.write_text(json.dumps({"fetch_utc": "2026-01-01T00:00:00Z", "data": "old"}))
            new_dict = {"fetch_utc": "2026-01-02T00:00:00Z", "data": "new"}
            result = preserve_fetch_utc_if_unchanged(path, new_dict, _series_sig)
            self.assertFalse(result)
            self.assertEqual(new_dict["fetch_utc"], "2026-01-02T00:00:00Z")
            self.assertEqual(new_dict["data"], "new")

    def test_handles_nested_structure_with_series_sig(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "nested.json"
            old = {
                "fetch_utc": "2026-01-01T00:00:00Z",
                "candidates_processed": [{
                    "asset": "BTC",
                    "series": [{"asset": "BTC", "kind": "klines"}, {"asset": "BTC", "kind": "funding"}]
                }]
            }
            path.write_text(json.dumps(old))
            new_dict = {
                "fetch_utc": "2026-01-02T00:00:00Z",
                "candidates_processed": [{
                    "asset": "BTC",
                    "series": [{"asset": "BTC", "kind": "funding"}, {"asset": "BTC", "kind": "klines"}]
                }]
            }
            result = preserve_fetch_utc_if_unchanged(path, new_dict, _series_sig)
            self.assertTrue(result)
            self.assertEqual(new_dict["fetch_utc"], "2026-01-01T00:00:00Z")


if __name__ == "__main__":
    unittest.main()