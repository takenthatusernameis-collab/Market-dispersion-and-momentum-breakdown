import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1] if False else Path('.').resolve()
SCRIPT = ROOT / 'scripts' / 'phase_b_placebos.py'

spec = importlib.util.spec_from_file_location('phase_b_placebos_seams_test', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestBlockBootstrapCI(unittest.TestCase):
    def test_empty_series_returns_nan(self):
        lo, hi = mod.block_bootstrap_ci(pd.Series(dtype=float))
        self.assertTrue(np.isnan(lo))
        self.assertTrue(np.isnan(hi))

    def test_all_nan_series_returns_nan(self):
        lo, hi = mod.block_bootstrap_ci(pd.Series([np.nan, np.nan]))
        self.assertTrue(np.isnan(lo))
        self.assertTrue(np.isnan(hi))

    def test_constant_series_bounds_equal_mean(self):
        s = pd.Series([2.0, 2.0, 2.0, 2.0, 2.0])
        lo, hi = mod.block_bootstrap_ci(s, n_boot=200, block_size=2, seed=7)
        self.assertAlmostEqual(lo, 2.0, places=12)
        self.assertAlmostEqual(hi, 2.0, places=12)

    def test_deterministic_with_same_seed(self):
        s = pd.Series([1.0, -1.0, 2.0, 0.5, -0.5, 1.5])
        a = mod.block_bootstrap_ci(s, n_boot=500, block_size=2, seed=123)
        b = mod.block_bootstrap_ci(s, n_boot=500, block_size=2, seed=123)
        self.assertEqual(a, b)

    def test_different_seed_can_differ(self):
        s = pd.Series([1.0, -2.0, 3.0, -1.0, 0.5, 2.5, -0.7, 1.2])
        a = mod.block_bootstrap_ci(s, n_boot=500, block_size=2, seed=1)
        b = mod.block_bootstrap_ci(s, n_boot=500, block_size=2, seed=9999)
        self.assertNotEqual(a, b)

    def test_interval_covers_sample_mean_for_typical_series(self):
        s = pd.Series([0.1, -0.2, 0.05, 0.3, -0.1, 0.2, 0.0, -0.05])
        mean = float(s.mean())
        lo, hi = mod.block_bootstrap_ci(s, n_boot=2000, block_size=2, seed=42)
        self.assertLessEqual(lo, hi)
        self.assertLessEqual(lo, mean + 1e-12)
        self.assertGreaterEqual(hi, mean - 1e-12)

    def test_single_element_series(self):
        s = pd.Series([3.5])
        lo, hi = mod.block_bootstrap_ci(s, n_boot=100, block_size=3, seed=5)
        self.assertAlmostEqual(lo, 3.5, places=12)
        self.assertAlmostEqual(hi, 3.5, places=12)

if __name__ == '__main__':
    unittest.main()
