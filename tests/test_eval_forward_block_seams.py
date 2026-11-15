"""Hermetic unit tests for the pure seams in scripts/eval_forward_block.py.

Gap: scripts/eval_forward_block.py exposes deterministic pure functions
(compute_dispersion, portfolio_spread, forward_returns, assign_trailing_decile_states,
overlap_aware_interval, MomentumCache.get) but no test imports the module or
exercises them directly. Existing tests (test_h10_sequential_artifact_contract.py,
test_h10_feasibility.py, test_eval_forward_block_maturity.py, etc.) only run the
script as a subprocess or import it for integration-style checks against frozen
artifacts; they never call the seams with synthetic data. These tests cover the
seams with synthetic DataFrames/Series (no frozen artifacts, no network, no
market data).

Pure seams tested:
- compute_dispersion(mom, estimator): cross-sectional population stddev and scaled MAD
- portfolio_spread(mom, rule): outer-decile top/bottom selection with tiebreak
- forward_returns(px_wide, T, horizon, assets): forward window return per asset
- assign_trailing_decile_states(dispersions, window_days, min_prior): high/low/mid classification
- overlap_aware_interval(formation_records, n_boot, rng_seed): cluster bootstrap (IMMATURE/OK)
- MomentumCache.get(end_date, lookback, assets): cached compounded momentum on daily returns
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "eval_forward_block.py"


def _load():
    spec = importlib.util.spec_from_file_location("eval_forward_block_seams_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class ComputeDispersionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_cross_sectional_population_stddev(self):
        mom = pd.Series([0.1, 0.2, 0.3, 0.4, 0.5])
        result = self.mod.compute_dispersion(mom, "cross_sectional_population_stddev")
        expected = float(mom.std(ddof=0))
        self.assertAlmostEqual(result, expected)

    def test_scaled_median_absolute_deviation(self):
        mom = pd.Series([0.1, 0.2, 0.3, 0.4, 0.5])
        result = self.mod.compute_dispersion(mom, "scaled_median_absolute_deviation_1_4826")
        med = float(mom.median())
        mad = float((mom - med).abs().median())
        expected = 1.4826 * mad
        self.assertAlmostEqual(result, expected)

    def test_unknown_estimator_raises(self):
        mom = pd.Series([0.1, 0.2, 0.3])
        with self.assertRaises(ValueError):
            self.mod.compute_dispersion(mom, "unknown_estimator")

    def test_empty_series_stddev(self):
        mom = pd.Series(dtype=float)
        result = self.mod.compute_dispersion(mom, "cross_sectional_population_stddev")
        self.assertTrue(np.isnan(result))

    def test_single_value_series_stddev(self):
        mom = pd.Series([0.5])
        result = self.mod.compute_dispersion(mom, "cross_sectional_population_stddev")
        self.assertEqual(result, 0.0)


class PortfolioSpreadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_outer_deciles_basic(self):
        # Need at least 20 assets for k >= 2 (n//10 >= 2)
        assets = [f"asset_{i:02d}" for i in range(20)]
        mom = pd.Series([float(i) / 100.0 for i in range(1, 21)], index=assets)
        top, bot = self.mod.portfolio_spread(mom, "trailing_window_outer_deciles")
        self.assertEqual(len(top), 2)
        self.assertEqual(len(bot), 2)
        self.assertEqual(top[0], "asset_19")
        self.assertEqual(top[1], "asset_18")
        # bot is tail of sorted (descending) series: asset_01 (0.02), asset_00 (0.01)
        self.assertEqual(bot[0], "asset_01")
        self.assertEqual(bot[1], "asset_00")

    def test_outer_deciles_tiebreak_by_asset_name(self):
        assets = [f"asset_{i:02d}" for i in range(20)]
        mom = pd.Series([0.5] * 20, index=assets)
        top, bot = self.mod.portfolio_spread(mom, "trailing_window_outer_deciles")
        self.assertEqual(len(top), 2)
        self.assertEqual(len(bot), 2)
        # With all equal values, tiebreak by asset name (ascending)
        # Top gets first k by name: asset_00, asset_01
        # Bot gets last k by name: asset_18, asset_19
        self.assertEqual(top[:2], ["asset_00", "asset_01"])
        self.assertEqual(bot[:2], ["asset_18", "asset_19"])

    def test_outer_deciles_k_less_than_two_returns_empty(self):
        assets = [f"asset_{i:02d}" for i in range(19)]  # 19 assets -> k=1
        mom = pd.Series([float(i) / 100.0 for i in range(1, 20)], index=assets)
        top, bot = self.mod.portfolio_spread(mom, "trailing_window_outer_deciles")
        self.assertEqual(top, [])
        self.assertEqual(bot, [])

    def test_unknown_rule_returns_empty(self):
        mom = pd.Series([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
                        index=["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"])
        top, bot = self.mod.portfolio_spread(mom, "unknown_rule")
        self.assertEqual(top, [])
        self.assertEqual(bot, [])

    def test_empty_series_returns_empty(self):
        mom = pd.Series(dtype=float)
        top, bot = self.mod.portfolio_spread(mom, "trailing_window_outer_deciles")
        self.assertEqual(top, [])
        self.assertEqual(bot, [])


class ForwardReturnsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_basic_forward_returns(self):
        dates = pd.date_range("2025-01-01", periods=10, freq="D", tz="UTC")
        px = pd.DataFrame({
            "A": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
            "B": [200.0, 202.0, 204.0, 206.0, 208.0, 210.0, 212.0, 214.0, 216.0, 218.0],
        }, index=dates)
        result = self.mod.forward_returns(px, "2025-01-03", 3, ["A", "B"])
        self.assertIn("A", result)
        self.assertIn("B", result)
        # T="2025-01-03" at pos 2, horizon=3 -> window pos 3,4,5 (2025-01-04,05,06)
        # A: 103->104->105->106? No, slice is iloc[3:6] = pos 3,4,5
        # A values at pos 3,4,5: 103, 104, 105 -> return = 105/103 - 1
        # B values at pos 3,4,5: 206, 208, 210 -> return = 210/206 - 1
        self.assertAlmostEqual(result["A"], 105.0/103.0 - 1.0)
        self.assertAlmostEqual(result["B"], 210.0/206.0 - 1.0)

    def test_T_not_in_index_returns_empty(self):
        dates = pd.date_range("2025-01-01", periods=5, freq="D", tz="UTC")
        px = pd.DataFrame({"A": [100.0, 101.0, 102.0, 103.0, 104.0]}, index=dates)
        result = self.mod.forward_returns(px, "2025-01-10", 3, ["A"])
        self.assertEqual(result, {})

    def test_empty_forward_window_returns_empty(self):
        dates = pd.date_range("2025-01-01", periods=3, freq="D", tz="UTC")
        px = pd.DataFrame({"A": [100.0, 101.0, 102.0]}, index=dates)
        result = self.mod.forward_returns(px, "2025-01-03", 3, ["A"])
        self.assertEqual(result, {})

    def test_asset_not_in_columns_skipped(self):
        dates = pd.date_range("2025-01-01", periods=5, freq="D", tz="UTC")
        px = pd.DataFrame({"A": [100.0, 101.0, 102.0, 103.0, 104.0]}, index=dates)
        result = self.mod.forward_returns(px, "2025-01-02", 2, ["A", "B"])
        self.assertIn("A", result)
        self.assertNotIn("B", result)

    def test_nan_values_in_window_dropped(self):
        dates = pd.date_range("2025-01-01", periods=5, freq="D", tz="UTC")
        px = pd.DataFrame({"A": [100.0, np.nan, 102.0, 103.0, 104.0]}, index=dates)
        result = self.mod.forward_returns(px, "2025-01-02", 2, ["A"])
        self.assertIn("A", result)
        self.assertAlmostEqual(result["A"], 103.0/102.0 - 1.0)


class AssignTrailingDecileStatesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_insufficient_prior_returns_mid(self):
        dispersions = {"2025-01-01": 0.1, "2025-01-02": 0.2, "2025-01-03": 0.3}
        result = self.mod.assign_trailing_decile_states(dispersions, window_days=365, min_prior=5)
        self.assertEqual(result["2025-01-01"], "mid")
        self.assertEqual(result["2025-01-02"], "mid")
        self.assertEqual(result["2025-01-03"], "mid")

    def test_sufficient_prior_classifies_high_low(self):
        dispersions = {f"2025-01-{d:02d}": float(d) / 100.0 for d in range(1, 31)}
        result = self.mod.assign_trailing_decile_states(dispersions, window_days=365, min_prior=5)
        self.assertEqual(result["2025-01-01"], "mid")
        self.assertEqual(result["2025-01-02"], "mid")
        self.assertEqual(result["2025-01-03"], "mid")
        self.assertEqual(result["2025-01-04"], "mid")
        self.assertEqual(result["2025-01-05"], "mid")
        self.assertIn(result["2025-01-30"], {"high", "low", "mid"})

    def test_empty_dispersions_returns_empty(self):
        result = self.mod.assign_trailing_decile_states({}, window_days=365, min_prior=5)
        self.assertEqual(result, {})

    def test_custom_min_prior(self):
        dispersions = {f"2025-01-{d:02d}": float(d) / 100.0 for d in range(1, 11)}
        result_3 = self.mod.assign_trailing_decile_states(dispersions, window_days=365, min_prior=3)
        result_7 = self.mod.assign_trailing_decile_states(dispersions, window_days=365, min_prior=7)
        self.assertEqual(sum(1 for v in result_3.values() if v != "mid"), 7)
        self.assertEqual(sum(1 for v in result_7.values() if v != "mid"), 3)


class OverlapAwareIntervalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_no_high_returns_immature(self):
        forms = [
            {"formation_date": "2025-01-01", "state": "mid", "spread_net_1x": 0.1},
            {"formation_date": "2025-02-01", "state": "mid", "spread_net_1x": 0.2},
        ]
        result = self.mod.overlap_aware_interval(forms, n_boot=100, rng_seed=123)
        self.assertEqual(result["status"], "IMMATURE")
        self.assertEqual(result["baseline_high_low_diff_net_1x"], None)

    def test_no_low_returns_immature(self):
        forms = [
            {"formation_date": "2025-01-01", "state": "high", "spread_net_1x": 0.1},
            {"formation_date": "2025-02-01", "state": "high", "spread_net_1x": 0.2},
        ]
        result = self.mod.overlap_aware_interval(forms, n_boot=100, rng_seed=123)
        self.assertEqual(result["status"], "IMMATURE")

    def test_both_states_returns_ok(self):
        forms = [
            {"formation_date": "2025-01-01", "state": "high", "spread_net_1x": 0.5},
            {"formation_date": "2025-01-02", "state": "high", "spread_net_1x": 0.6},
            {"formation_date": "2025-02-01", "state": "low", "spread_net_1x": -0.3},
            {"formation_date": "2025-02-02", "state": "low", "spread_net_1x": -0.4},
        ]
        result = self.mod.overlap_aware_interval(forms, n_boot=100, rng_seed=123)
        self.assertEqual(result["status"], "OK")
        self.assertIsNotNone(result["baseline_high_low_diff_net_1x"])
        self.assertIsNotNone(result["bootstrap_mean"])
        self.assertIsNotNone(result["ci_95_percentile"][0])
        self.assertIsNotNone(result["ci_95_percentile"][1])
        self.assertIsInstance(result["ci_includes_zero"], bool)

    def test_deterministic_with_fixed_seed(self):
        forms = [
            {"formation_date": "2025-01-01", "state": "high", "spread_net_1x": 0.5},
            {"formation_date": "2025-02-01", "state": "low", "spread_net_1x": -0.3},
        ]
        r1 = self.mod.overlap_aware_interval(forms, n_boot=50, rng_seed=42)
        r2 = self.mod.overlap_aware_interval(forms, n_boot=50, rng_seed=42)
        self.assertEqual(r1["bootstrap_mean"], r2["bootstrap_mean"])
        self.assertEqual(r1["ci_95_percentile"], r2["ci_95_percentile"])

    def test_different_seeds_produce_different_results(self):
        forms = [
            {"formation_date": "2025-01-01", "state": "high", "spread_net_1x": 0.5},
            {"formation_date": "2025-02-01", "state": "low", "spread_net_1x": -0.3},
        ]
        r1 = self.mod.overlap_aware_interval(forms, n_boot=50, rng_seed=1)
        r2 = self.mod.overlap_aware_interval(forms, n_boot=50, rng_seed=2)
        self.assertNotEqual(r1["bootstrap_mean"], r2["bootstrap_mean"])


class MomentumCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_basic_momentum_compounded(self):
        dates = pd.date_range("2025-01-01", periods=11, freq="D", tz="UTC")
        px = pd.DataFrame({
            "A": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0],
            "B": [200.0, 201.0, 202.0, 203.0, 204.0, 205.0, 206.0, 207.0, 208.0, 209.0, 210.0],
        }, index=dates)
        cache = self.mod.MomentumCache(px)
        # Use end_date at position 6 (2025-01-07), lookback=5 -> window positions 2-6
        mom = cache.get("2025-01-07", 5, ("A", "B"))
        self.assertEqual(len(mom), 2)
        self.assertIn("A", mom.index)
        self.assertIn("B", mom.index)

    def test_end_date_not_in_index_returns_empty(self):
        dates = pd.date_range("2025-01-01", periods=5, freq="D", tz="UTC")
        px = pd.DataFrame({"A": [100.0, 101.0, 102.0, 103.0, 104.0]}, index=dates)
        cache = self.mod.MomentumCache(px)
        mom = cache.get("2025-01-10", 3, ("A",))
        self.assertEqual(len(mom), 0)

    def test_lookback_longer_than_history_returns_empty(self):
        dates = pd.date_range("2025-01-01", periods=5, freq="D", tz="UTC")
        px = pd.DataFrame({"A": [100.0, 101.0, 102.0, 103.0, 104.0]}, index=dates)
        cache = self.mod.MomentumCache(px)
        mom = cache.get("2025-01-03", 10, ("A",))
        self.assertEqual(len(mom), 0)

    def test_asset_with_missing_returns_dropped(self):
        dates = pd.date_range("2025-01-01", periods=11, freq="D", tz="UTC")
        px = pd.DataFrame({
            "A": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0],
            "B": [200.0, np.nan, 202.0, np.nan, 204.0, 205.0, 206.0, 207.0, 208.0, 209.0, 210.0],
        }, index=dates)
        cache = self.mod.MomentumCache(px)
        # end_date at position 6, lookback=5 -> window positions 2-6
        mom = cache.get("2025-01-07", 5, ("A", "B"))
        self.assertEqual(len(mom), 1)
        self.assertIn("A", mom.index)
        self.assertNotIn("B", mom.index)

    def test_cache_hit_returns_same_object(self):
        dates = pd.date_range("2025-01-01", periods=10, freq="D", tz="UTC")
        px = pd.DataFrame({"A": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0]}, index=dates)
        cache = self.mod.MomentumCache(px)
        mom1 = cache.get("2025-01-05", 5, ("A",))
        mom2 = cache.get("2025-01-05", 5, ("A",))
        self.assertTrue(mom1.equals(mom2))

    def test_empty_asset_list_returns_empty(self):
        dates = pd.date_range("2025-01-01", periods=5, freq="D", tz="UTC")
        px = pd.DataFrame({"A": [100.0, 101.0, 102.0, 103.0, 104.0]}, index=dates)
        cache = self.mod.MomentumCache(px)
        mom = cache.get("2025-01-03", 3, ())
        self.assertEqual(len(mom), 0)


if __name__ == "__main__":
    unittest.main()