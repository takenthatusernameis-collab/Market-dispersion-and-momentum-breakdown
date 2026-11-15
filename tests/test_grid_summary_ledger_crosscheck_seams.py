"""Hermetic unit tests for the pure seams in scripts/grid_summary_ledger_crosscheck.py.

Gap: the crosscheck script exposes deterministic pure functions
(recompute_from_formations, compare_values) but no test imports the module or
exercises them directly. These tests cover the seams with synthetic DataFrames/
dicts (no frozen artifacts, no network, no market data).
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "grid_summary_ledger_crosscheck.py"


def _load():
    spec = importlib.util.spec_from_file_location("grid_summary_ledger_crosscheck_seams_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class RecomputeFromFormationsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_empty_formations(self):
        result = self.mod.recompute_from_formations([])
        self.assertEqual(result["n_formations"], 0)
        self.assertEqual(result["n_high"], 0)
        self.assertEqual(result["n_low"], 0)
        self.assertEqual(result["n_mid"], 0)
        self.assertIsNone(result["high_gross_mean"])
        self.assertIsNone(result["high_low_diff_net_1x"])
        self.assertEqual(result["eligible_assets_per_date"], {"mean": 0.0, "min": 0, "max": 0})

    def test_single_formation_mid(self):
        forms = [{"formation_date": "2023-01-31", "state": "mid", "spread_gross": 0.1, "spread_net_1x": 0.099, "n_assets": 26}]
        result = self.mod.recompute_from_formations(forms)
        self.assertEqual(result["n_formations"], 1)
        self.assertEqual(result["n_high"], 0)
        self.assertEqual(result["n_low"], 0)
        self.assertEqual(result["n_mid"], 1)
        self.assertIsNone(result["high_gross_mean"])
        self.assertIsNone(result["low_gross_mean"])
        self.assertIsNone(result["high_low_diff_net_1x"])
        self.assertAlmostEqual(result["spread_gross_mean"], 0.1)
        self.assertAlmostEqual(result["spread_net_1x_mean"], 0.099)
        self.assertEqual(result["date_first"], "2023-01-31")
        self.assertEqual(result["date_last"], "2023-01-31")
        self.assertEqual(result["eligible_assets_per_date"], {"mean": 26.0, "min": 26, "max": 26})

    def test_mixed_states(self):
        forms = [
            {"formation_date": "2023-01-31", "state": "high", "spread_gross": 0.2, "spread_net_1x": 0.199, "n_assets": 26},
            {"formation_date": "2023-02-28", "state": "low", "spread_gross": -0.1, "spread_net_1x": -0.101, "n_assets": 27},
            {"formation_date": "2023-03-31", "state": "mid", "spread_gross": 0.05, "spread_net_1x": 0.049, "n_assets": 26},
        ]
        result = self.mod.recompute_from_formations(forms)
        self.assertEqual(result["n_formations"], 3)
        self.assertEqual(result["n_high"], 1)
        self.assertEqual(result["n_low"], 1)
        self.assertEqual(result["n_mid"], 1)
        self.assertAlmostEqual(result["high_gross_mean"], 0.2)
        self.assertAlmostEqual(result["low_gross_mean"], -0.1)
        self.assertAlmostEqual(result["high_net_1x_mean"], 0.199)
        self.assertAlmostEqual(result["low_net_1x_mean"], -0.101)
        self.assertAlmostEqual(result["high_low_diff_gross"], 0.3)
        self.assertAlmostEqual(result["high_low_diff_net_1x"], 0.3)
        self.assertAlmostEqual(result["spread_gross_mean"], (0.2 - 0.1 + 0.05) / 3)
        self.assertAlmostEqual(result["spread_net_1x_mean"], (0.199 - 0.101 + 0.049) / 3)
        self.assertEqual(result["date_first"], "2023-01-31")
        self.assertEqual(result["date_last"], "2023-03-31")
        self.assertEqual(result["eligible_assets_per_date"], {"mean": 26.333333333333332, "min": 26, "max": 27})

    def test_nan_values_dropped(self):
        forms = [
            {"formation_date": "2023-01-31", "state": "high", "spread_gross": 0.2, "spread_net_1x": 0.199, "n_assets": 26},
            {"formation_date": "2023-02-28", "state": "high", "spread_gross": np.nan, "spread_net_1x": 0.15, "n_assets": 26},
        ]
        result = self.mod.recompute_from_formations(forms)
        # NaN spread_gross should be dropped from mean
        self.assertAlmostEqual(result["high_gross_mean"], 0.2)
        self.assertAlmostEqual(result["high_net_1x_mean"], (0.199 + 0.15) / 2)

    def test_eligible_assets_min_max(self):
        forms = [
            {"formation_date": "2023-01-31", "state": "mid", "spread_gross": 0.1, "spread_net_1x": 0.09, "n_assets": 25},
            {"formation_date": "2023-02-28", "state": "mid", "spread_gross": 0.2, "spread_net_1x": 0.19, "n_assets": 30},
            {"formation_date": "2023-03-31", "state": "mid", "spread_gross": 0.3, "spread_net_1x": 0.29, "n_assets": 28},
        ]
        result = self.mod.recompute_from_formations(forms)
        self.assertEqual(result["eligible_assets_per_date"]["min"], 25)
        self.assertEqual(result["eligible_assets_per_date"]["max"], 30)
        self.assertAlmostEqual(result["eligible_assets_per_date"]["mean"], (25 + 30 + 28) / 3)


class CompareValuesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_both_none(self):
        diffs = []
        self.mod.compare_values("test", None, None, diffs)
        self.assertEqual(diffs, [])

    def test_one_none(self):
        diffs = []
        self.mod.compare_values("test", 1.0, None, diffs)
        self.assertEqual(len(diffs), 1)
        self.assertIn("one None", diffs[0])

    def test_float_match_within_tol(self):
        diffs = []
        self.mod.compare_values("test", 1.0, 1.0 + 1e-13, diffs)
        self.assertEqual(diffs, [])

    def test_float_mismatch_beyond_tol(self):
        diffs = []
        self.mod.compare_values("test", 1.0, 1.0 + 1e-10, diffs)
        self.assertEqual(len(diffs), 1)
        self.assertIn("diff", diffs[0])

    def test_nan_both(self):
        diffs = []
        self.mod.compare_values("test", float("nan"), float("nan"), diffs)
        self.assertEqual(diffs, [])

    def test_exact_match_int(self):
        diffs = []
        self.mod.compare_values("test", 5, 5, diffs)
        self.assertEqual(diffs, [])

    def test_mismatch_int(self):
        diffs = []
        self.mod.compare_values("test", 5, 6, diffs)
        self.assertEqual(len(diffs), 1)

    def test_string_match(self):
        diffs = []
        self.mod.compare_values("test", "abc", "abc", diffs)
        self.assertEqual(diffs, [])

    def test_string_mismatch(self):
        diffs = []
        self.mod.compare_values("test", "abc", "def", diffs)
        self.assertEqual(len(diffs), 1)


class ModuleConstantsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def setUp(self):
        self.mod = self.__class__.mod

    def test_tol_constant(self):
        self.assertEqual(self.mod.TOL, 1e-12)

    def test_anchors_tuple(self):
        self.assertEqual(self.mod.ANCHORS, ("H004V105", "H004V106"))

    def test_summary_keys_map(self):
        self.assertEqual(self.mod.SUMMARY_KEYS["H004V105"], "primary_anchor_legacy_H004V105")
        self.assertEqual(self.mod.SUMMARY_KEYS["H004V106"], "primary_anchor_expanding_H004V106")


if __name__ == "__main__":
    unittest.main()