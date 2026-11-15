"""Hermetic unit tests for the pure seams in scripts/fix_inference.py.

Gap: scripts/fix_inference.py exposes two deterministic pure functions,
``block_bootstrap_ci`` and ``paired_diff_series``, but no test imports the
module or exercises them directly. ``tests/test_inference_repro.py`` only
re-runs the script as a subprocess and pins byte-repro artifacts; it never
calls the bootstrap CI or the paired-difference seam. These tests cover the
seams with synthetic series (no frozen artifacts, no network, no market data).

``block_bootstrap_ci(series)`` — fixed-seed block bootstrap (block 3, 10000
reps, alpha 0.05) returning (lo, hi); (None, None) for empty input.
``paired_diff_series(hi, lo)`` — aligns two formation-indexed series by index,
subtracts per formation, drops NaN legs, preserves chronological index order.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "fix_inference.py"


def _load():
    spec = importlib.util.spec_from_file_location("fix_inference_seams_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class BlockBootstrapCITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_empty_series_returns_none_none(self):
        self.assertEqual(self.mod.block_bootstrap_ci(pd.Series(dtype=float)), (None, None))
        self.assertEqual(self.mod.block_bootstrap_ci(pd.Series([np.nan, np.nan])), (None, None))

    def test_constant_series_ci_is_degenerate_at_value(self):
        s = pd.Series([5.0] * 20)
        lo, hi = self.mod.block_bootstrap_ci(s)
        self.assertEqual(lo, 5.0)
        self.assertEqual(hi, 5.0)

    def test_lo_le_hi_and_within_data_range(self):
        rng = np.random.RandomState(7)
        s = pd.Series(rng.normal(0.0, 1.0, 50))
        lo, hi = self.mod.block_bootstrap_ci(s)
        self.assertIsNotNone(lo)
        self.assertIsNotNone(hi)
        self.assertLessEqual(lo, hi)
        self.assertGreaterEqual(lo, float(s.min()))
        self.assertLessEqual(hi, float(s.max()))

    def test_deterministic_with_fixed_seed(self):
        s = pd.Series(np.arange(1.0, 11.0))
        self.assertEqual(
            self.mod.block_bootstrap_ci(s), self.mod.block_bootstrap_ci(s)
        )

    def test_ci_shifts_with_data(self):
        s1 = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        s2 = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0, 60.0])
        self.assertNotEqual(
            self.mod.block_bootstrap_ci(s1), self.mod.block_bootstrap_ci(s2)
        )


class PairedDiffSeriesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_subtracts_aligned_by_index(self):
        hi = pd.Series([10.0, 20.0, 30.0], index=["a", "b", "c"])
        lo = pd.Series([1.0, 2.0, 3.0], index=["a", "b", "c"])
        self.assertEqual(list(self.mod.paired_diff_series(hi, lo)), [9.0, 18.0, 27.0])

    def test_drops_missing_legs(self):
        hi = pd.Series([10.0, 20.0, 30.0], index=["a", "b", "c"])
        lo = pd.Series([1.0, 99.0], index=["a", "c"])
        self.assertEqual(list(self.mod.paired_diff_series(hi, lo)), [9.0, -69.0])

    def test_empty_when_no_overlap(self):
        hi = pd.Series([10.0, 20.0], index=["a", "b"])
        lo = pd.Series([1.0, 2.0], index=["c", "d"])
        self.assertEqual(len(self.mod.paired_diff_series(hi, lo)), 0)

    def test_preserves_chronological_index_order(self):
        hi = pd.Series([1.0, 2.0, 3.0], index=["2026-01", "2026-02", "2026-03"])
        lo = pd.Series([0.0, 0.0, 0.0], index=["2026-01", "2026-02", "2026-03"])
        self.assertEqual(
            list(self.mod.paired_diff_series(hi, lo).index),
            ["2026-01", "2026-02", "2026-03"],
        )

    def test_does_not_mutate_inputs(self):
        hi = pd.Series([10.0, 20.0], index=["a", "b"])
        lo = pd.Series([1.0, 2.0], index=["a", "b"])
        hi_copy = hi.copy()
        lo_copy = lo.copy()
        self.mod.paired_diff_series(hi, lo)
        self.assertTrue(hi.equals(hi_copy))
        self.assertTrue(lo.equals(lo_copy))


if __name__ == "__main__":
    unittest.main()
