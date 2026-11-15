"""Hermetic tests for scripts/grid_anchor_crosscheck.py pure seams.

Tests the cross-check logic on synthetic data without reading any committed artifacts.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import grid_anchor_crosscheck as gac


class GridAnchorCrosscheckSeamTests(unittest.TestCase):
    def make_formations(self, n=10, start_date="2023-01-31"):
        """Create synthetic formation records."""
        from datetime import datetime, timedelta
        base = datetime.strptime(start_date, "%Y-%m-%d")
        formations = []
        for i in range(n):
            d = base + timedelta(days=i)
            state = "mid"
            if i % 3 == 0:
                state = "high"
            elif i % 3 == 1:
                state = "low"
            formations.append({
                "formation_date": d.strftime("%Y-%m-%d"),
                "dispersion": 0.1 + i * 0.01,
                "n_assets": 30 + i,
                "spread_gross": float(i * 0.001),
                "spread_net_1x": float(i * 0.001 - 0.001),
                "state": state,
            })
        return formations

    def test_compute_summary_from_formations_basic(self):
        """Basic summary computation matches expected values."""
        formations = self.make_formations(12)
        summary = gac.compute_summary_from_formations(formations)
        self.assertEqual(summary["n_formations"], 12)
        self.assertEqual(summary["n_high"], 4)  # indices 0,3,6,9
        self.assertEqual(summary["n_low"], 4)   # indices 1,4,7,10
        self.assertEqual(summary["n_mid"], 4)   # indices 2,5,8,11
        self.assertEqual(summary["date_first"], "2023-01-31")
        self.assertEqual(summary["date_last"], "2023-02-11")

    def test_compute_summary_from_formations_high_low_diff(self):
        """High-low diff computation is correct."""
        formations = self.make_formations(12)
        summary = gac.compute_summary_from_formations(formations)
        # High states: indices 0,3,6,9 -> spread_net = -0.001, 0.002, 0.005, 0.008
        # Mean = (-0.001 + 0.002 + 0.005 + 0.008) / 4 = 0.014 / 4 = 0.0035
        # Low states: indices 1,4,7,10 -> spread_net = 0.0, 0.003, 0.006, 0.009
        # Mean = (0.0 + 0.003 + 0.006 + 0.009) / 4 = 0.018 / 4 = 0.0045
        # Diff = 0.0035 - 0.0045 = -0.001
        import numpy as np
        hi_net = np.array([-0.001, 0.002, 0.005, 0.008])
        lo_net = np.array([0.0, 0.003, 0.006, 0.009])
        expected = float(np.mean(hi_net) - np.mean(lo_net))
        self.assertAlmostEqual(summary["high_low_diff_net_1x"], expected, places=12)

    def test_compare_formations_identical(self):
        """Identical formation lists match perfectly."""
        f1 = self.make_formations(10)
        f2 = [dict(r) for r in f1]
        result = gac.compare_formations(f1, f2, "A", "B")
        self.assertTrue(result["match"])
        self.assertEqual(result["mismatches"], [])
        self.assertEqual(result["n_compared"], 10)

    def test_compare_formations_length_mismatch(self):
        """Length mismatch is detected."""
        f1 = self.make_formations(10)
        f2 = self.make_formations(9)
        result = gac.compare_formations(f1, f2, "A", "B")
        self.assertFalse(result["match"])
        self.assertEqual(len(result["mismatches"]), 1)
        self.assertEqual(result["mismatches"][0]["type"], "length_mismatch")

    def test_compare_formations_date_mismatch(self):
        """Date mismatch is detected."""
        f1 = self.make_formations(10)
        f2 = [dict(r) for r in f1]
        f2[3]["formation_date"] = "2023-02-15"  # different date
        result = gac.compare_formations(f1, f2, "A", "B")
        self.assertFalse(result["match"])
        self.assertTrue(any(m["type"] == "date_mismatch" for m in result["mismatches"]))

    def test_compare_formations_numeric_mismatch(self):
        """Numeric field mismatch beyond tolerance is detected."""
        f1 = self.make_formations(10)
        f2 = [dict(r) for r in f1]
        f2[3]["dispersion"] = 0.999  # large difference
        result = gac.compare_formations(f1, f2, "A", "B")
        self.assertFalse(result["match"])
        self.assertTrue(any(m["type"] == "numeric_mismatch" and m["field"] == "dispersion" for m in result["mismatches"]))

    def test_compare_formations_numeric_within_tolerance(self):
        """Numeric field mismatch within tolerance is OK."""
        f1 = self.make_formations(10)
        f2 = [dict(r) for r in f1]
        f2[3]["dispersion"] = f1[3]["dispersion"] + 1e-13  # within TOL=1e-12
        result = gac.compare_formations(f1, f2, "A", "B")
        self.assertTrue(result["match"])

    def test_compare_formations_n_assets_mismatch(self):
        """n_assets mismatch is detected."""
        f1 = self.make_formations(10)
        f2 = [dict(r) for r in f1]
        f2[3]["n_assets"] = 999
        result = gac.compare_formations(f1, f2, "A", "B")
        self.assertFalse(result["match"])
        self.assertTrue(any(m["type"] == "n_assets_mismatch" for m in result["mismatches"]))

    def test_compare_formations_state_mismatch(self):
        """State mismatch is detected."""
        f1 = self.make_formations(10)
        f2 = [dict(r) for r in f1]
        f2[2]["state"] = "high"  # index 2 is "mid" in original
        result = gac.compare_formations(f1, f2, "A", "B")
        self.assertFalse(result["match"])
        self.assertTrue(any(m["type"] == "state_mismatch" for m in result["mismatches"]))

    def test_compare_summaries_identical(self):
        """Identical summaries match perfectly."""
        s1 = {"n_formations": 100, "n_high": 10, "n_low": 10, "n_mid": 80,
              "high_low_diff_net_1x": 0.001, "high_low_diff_gross": 0.001,
              "spread_net_1x_mean": 0.0, "spread_net_1x_median": 0.0,
              "spread_gross_mean": 0.001, "spread_gross_median": 0.001,
              "high_net_1x_mean": 0.01, "low_net_1x_mean": -0.01,
              "high_gross_mean": 0.01, "low_gross_mean": -0.01,
              "date_first": "2023-01-31", "date_last": "2026-09-29"}
        s2 = dict(s1)
        result = gac.compare_summaries(s1, s2, "A", "B")
        self.assertTrue(result["match"])
        self.assertEqual(result["mismatches"], [])

    def test_compare_summaries_numeric_mismatch(self):
        """Numeric summary mismatch beyond tolerance is detected."""
        s1 = {"n_formations": 100, "n_high": 10, "n_low": 10, "n_mid": 80,
              "high_low_diff_net_1x": 0.001, "high_low_diff_gross": 0.001,
              "spread_net_1x_mean": 0.0, "spread_net_1x_median": 0.0,
              "spread_gross_mean": 0.001, "spread_gross_median": 0.001,
              "high_net_1x_mean": 0.01, "low_net_1x_mean": -0.01,
              "high_gross_mean": 0.01, "low_gross_mean": -0.01,
              "date_first": "2023-01-31", "date_last": "2026-09-29"}
        s2 = dict(s1)
        s2["high_low_diff_net_1x"] = 0.002  # diff = 0.001 > TOL
        result = gac.compare_summaries(s1, s2, "A", "B")
        self.assertFalse(result["match"])
        self.assertTrue(any(m["field"] == "high_low_diff_net_1x" for m in result["mismatches"]))

    def test_compare_summaries_numeric_within_tolerance(self):
        """Numeric summary mismatch within tolerance is OK."""
        s1 = {"n_formations": 100, "n_high": 10, "n_low": 10, "n_mid": 80,
              "high_low_diff_net_1x": 0.001, "high_low_diff_gross": 0.001,
              "spread_net_1x_mean": 0.0, "spread_net_1x_median": 0.0,
              "spread_gross_mean": 0.001, "spread_gross_median": 0.001,
              "high_net_1x_mean": 0.01, "low_net_1x_mean": -0.01,
              "high_gross_mean": 0.01, "low_gross_mean": -0.01,
              "date_first": "2023-01-31", "date_last": "2026-09-29"}
        s2 = dict(s1)
        s2["high_low_diff_net_1x"] = 0.001 + 1e-13
        result = gac.compare_summaries(s1, s2, "A", "B")
        self.assertTrue(result["match"])

    def test_check_data_integrity_clean(self):
        """Clean formations pass integrity checks."""
        formations = self.make_formations(10)
        result = gac.check_data_integrity(formations, "test")
        self.assertTrue(result["all_ok"])
        self.assertEqual(result["issues"], [])
        self.assertEqual(result["n_formations"], 10)
        self.assertEqual(result["unique_dates"], 10)

    def test_check_data_integrity_duplicate_date(self):
        """Duplicate dates are detected."""
        formations = self.make_formations(10)
        formations[3]["formation_date"] = formations[0]["formation_date"]
        result = gac.check_data_integrity(formations, "test")
        self.assertFalse(result["all_ok"])
        self.assertTrue(any(i["type"] == "duplicate_date" for i in result["issues"]))

    def test_check_data_integrity_non_finite(self):
        """Non-finite values are detected."""
        formations = self.make_formations(10)
        formations[3]["dispersion"] = float("nan")
        result = gac.check_data_integrity(formations, "test")
        self.assertFalse(result["all_ok"])
        self.assertTrue(any(i["type"] == "non_finite" and i["field"] == "dispersion" for i in result["issues"]))

    def test_check_data_integrity_missing_field(self):
        """Missing fields are detected."""
        formations = self.make_formations(10)
        formations[3]["spread_gross"] = None
        result = gac.check_data_integrity(formations, "test")
        self.assertFalse(result["all_ok"])
        self.assertTrue(any(i["type"] == "missing_field" and i["field"] == "spread_gross" for i in result["issues"]))

    def test_check_data_integrity_invalid_state(self):
        """Invalid state is detected."""
        formations = self.make_formations(10)
        formations[3]["state"] = "invalid"
        result = gac.check_data_integrity(formations, "test")
        self.assertFalse(result["all_ok"])
        self.assertTrue(any(i["type"] == "invalid_state" for i in result["issues"]))

    def test_check_data_integrity_non_increasing_dates(self):
        """Non-increasing dates are detected."""
        formations = self.make_formations(10)
        formations[3]["formation_date"] = "2023-01-30"  # before previous
        result = gac.check_data_integrity(formations, "test")
        self.assertFalse(result["all_ok"])
        self.assertTrue(any(i["type"] == "non_increasing_date" for i in result["issues"]))


if __name__ == "__main__":
    unittest.main()