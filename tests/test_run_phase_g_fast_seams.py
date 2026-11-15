"""Hermetic unit tests for the pure seams in scripts/run_phase_g_fast.py.

Gap: ``scripts/run_phase_g_fast.py`` (DISPERSION-001 phase-G fast runner)
exposes five deterministic pure DataFrame seams — ``formation_dates_monthly``,
``momentum_compounded``, ``build_daily_dispersion_series``,
``get_state_for_formation`` and ``compute_momentum_spread`` — but no test
imports the module or exercises them directly. The module is import-safe
(top-level code is only imports and constants; ``main()`` is guarded by
``__main__``), so these seams can be tested without touching any committed
panel/artifact or the network.

These tests build small synthetic DataFrames and assert the exact numerical
behavior of each seam. No frozen artifact/config/input is read or written.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_phase_g_fast.py"


def _load():
    spec = importlib.util.spec_from_file_location("run_phase_g_fast_seams_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _make_panel(n_assets: int, n_days: int, seed: int = 0):
    dates = list(pd.date_range("2026-01-01", periods=n_days, freq="D").strftime("%Y-%m-%d"))
    assets = [f"a{i}" for i in range(n_assets)]
    rng = np.random.RandomState(seed)
    prices = pd.DataFrame(
        100.0 + rng.randn(n_days, n_assets).cumsum(axis=0),
        index=dates,
        columns=assets,
    )
    returns = prices.pct_change()
    univ = pd.DataFrame(
        [(d, a, True) for d in dates for a in assets],
        columns=["date", "asset_id", "eligible"],
    )
    return prices, returns, univ, dates, assets


class FormationDatesMonthlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_returns_first_eligible_date_per_month_in_order(self):
        univ = pd.DataFrame(
            {
                "date": ["2026-01-05", "2026-01-20", "2026-02-03", "2026-03-01", "2026-03-02"],
                "asset_id": ["a"] * 5,
                "eligible": [True, False, True, True, False],
            }
        )
        # 2026-01-20 ineligible; 2026-03-02 ineligible -> first eligible per month.
        self.assertEqual(
            self.mod.formation_dates_monthly(None, univ),
            ["2026-01-05", "2026-02-03", "2026-03-01"],
        )

    def test_no_eligible_rows_returns_empty(self):
        univ = pd.DataFrame(
            {
                "date": ["2026-01-05", "2026-02-03"],
                "asset_id": ["a", "a"],
                "eligible": [False, False],
            }
        )
        self.assertEqual(self.mod.formation_dates_monthly(None, univ), [])


class MomentumCompoundedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()
        cls.dates = list(pd.date_range("2026-01-01", periods=4, freq="D").strftime("%Y-%m-%d"))
        cls.rets = pd.DataFrame(
            {
                "a": [0.1, 0.1, 0.1, 0.1],
                "b": [0.2, 0.2, np.nan, 0.2],
                "c": [np.nan, np.nan, np.nan, np.nan],
            },
            index=cls.dates,
        )

    def test_compounds_only_assets_with_complete_window(self):
        # end 2026-01-04, lookback 2 -> window rows 2026-01-03/04.
        # a complete -> (1.1*1.1)-1; b has NaN in window -> dropped; c all NaN -> dropped.
        out = self.mod.momentum_compounded(self.rets, "2026-01-04", 2, ["a", "b", "c"])
        self.assertEqual(list(out.index), ["a"])
        self.assertAlmostEqual(float(out["a"]), 1.1 * 1.1 - 1.0, places=12)

    def test_end_date_not_in_index_returns_empty(self):
        out = self.mod.momentum_compounded(self.rets, "2030-01-01", 2, ["a"])
        self.assertEqual(len(out), 0)

    def test_lookback_longer_than_history_returns_empty(self):
        out = self.mod.momentum_compounded(self.rets, "2026-01-04", 99, ["a"])
        self.assertEqual(len(out), 0)

    def test_all_requested_assets_incomplete_returns_empty(self):
        out = self.mod.momentum_compounded(self.rets, "2026-01-04", 2, ["c"])
        self.assertEqual(len(out), 0)


class BuildDailyDispersionSeriesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()
        cls.prices, cls.returns, cls.univ, cls.dates, cls.assets = _make_panel(30, 6, seed=1)

    def test_skips_dates_before_lookback_and_returns_numeric_std(self):
        disp = self.mod.build_daily_dispersion_series(
            self.prices, self.returns, self.univ, 3, "cross_sectional_population_stddev"
        )
        # With 6 days and lookback 3, first eligible loc is index 2 (2026-01-03).
        self.assertEqual(list(disp.keys()), ["2026-01-03", "2026-01-04", "2026-01-05", "2026-01-06"])
        for v in disp.values():
            self.assertIsInstance(v, float)
            self.assertGreaterEqual(v, 0.0)

    def test_scaled_mad_estimator_is_nonnegative_and_nonempty(self):
        disp = self.mod.build_daily_dispersion_series(
            self.prices, self.returns, self.univ, 3, "scaled_median_absolute_deviation_1_4826"
        )
        self.assertTrue(disp)
        for v in disp.values():
            self.assertGreaterEqual(v, 0.0)

    def test_too_few_eligible_assets_yields_empty(self):
        univ_small = pd.DataFrame(
            [(d, a, True) for d in self.dates for a in self.assets[:5]],
            columns=["date", "asset_id", "eligible"],
        )
        disp = self.mod.build_daily_dispersion_series(
            self.prices, self.returns, univ_small, 3, "cross_sectional_population_stddev"
        )
        self.assertEqual(disp, {})


class GetStateForFormationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()
        cls.T = "2026-06-01"
        daylist = pd.date_range(
            end=pd.Timestamp(cls.T) - pd.Timedelta(days=10), periods=200, freq="D"
        ).strftime("%Y-%m-%d")
        cls.dd = {d: float(i) for i, d in enumerate(daylist)}

    def test_outer_deciles_low(self):
        self.assertEqual(
            self.mod.get_state_for_formation(self.T, -5.0, self.dd, "trailing_365d_outer_deciles"),
            "low",
        )

    def test_outer_deciles_high(self):
        self.assertEqual(
            self.mod.get_state_for_formation(self.T, 1e9, self.dd, "trailing_365d_outer_deciles"),
            "high",
        )

    def test_outer_deciles_mid(self):
        self.assertEqual(
            self.mod.get_state_for_formation(self.T, 100.0, self.dd, "trailing_365d_outer_deciles"),
            "mid",
        )

    def test_median_split_low_and_high(self):
        self.assertEqual(
            self.mod.get_state_for_formation(self.T, -5.0, self.dd, "trailing_365d_median_split"),
            "low",
        )
        self.assertEqual(
            self.mod.get_state_for_formation(self.T, 1e9, self.dd, "trailing_365d_median_split"),
            "high",
        )

    def test_unknown_rule_returns_mid(self):
        self.assertEqual(
            self.mod.get_state_for_formation(self.T, 1e9, self.dd, "not_a_rule"), "mid"
        )

    def test_insufficient_history_returns_mid(self):
        self.assertEqual(
            self.mod.get_state_for_formation(self.T, 1e9, {}, "trailing_365d_outer_deciles"),
            "mid",
        )


class ComputeMomentumSpreadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()
        cls.prices, cls.returns, cls.univ, cls.dates, cls.assets = _make_panel(30, 8, seed=2)
        cls.T = cls.dates[4]
        cls.univT = pd.DataFrame(
            [(cls.T, a, True) for a in cls.assets],
            columns=["date", "asset_id", "eligible"],
        )

    def test_valid_structure_and_cost_arithmetic(self):
        res = self.mod.compute_momentum_spread(
            self.prices, self.returns, self.univT, self.T, 3, 2, "top_bottom_deciles", pd.DataFrame()
        )
        self.assertTrue(res["valid"])
        self.assertEqual(res["formation_date"], self.T)
        self.assertEqual(res["n_assets"], 30)
        self.assertEqual(res["dispersion"], float(res["dispersion"]))
        gross = res["momentum_spread_gross"]
        # cost_1x = 0.0005*2.0*1, cost_2x = (0.0005*2.0)*2, cost_3x = (0.0005*3.0)*2.
        self.assertAlmostEqual(res["momentum_spread_net_1x"], gross - 0.001, places=12)
        self.assertAlmostEqual(res["momentum_spread_net_2x"], gross - 0.002, places=12)
        self.assertAlmostEqual(res["momentum_spread_net_3x"], gross - 0.003, places=12)
        self.assertAlmostEqual(
            res["momentum_spread_net_1x"] - res["momentum_spread_net_2x"], 0.001, places=12
        )

    def test_invalid_when_too_few_eligible(self):
        univ_small = pd.DataFrame(
            [(self.T, a, True) for a in self.assets[:5]],
            columns=["date", "asset_id", "eligible"],
        )
        res = self.mod.compute_momentum_spread(
            self.prices, self.returns, univ_small, self.T, 3, 2, "top_bottom_deciles", pd.DataFrame()
        )
        self.assertEqual(res, {"valid": False})

    def test_invalid_when_forward_window_empty(self):
        # T is the last date -> no forward rows.
        last = self.dates[-1]
        univ_last = pd.DataFrame(
            [(last, a, True) for a in self.assets],
            columns=["date", "asset_id", "eligible"],
        )
        res = self.mod.compute_momentum_spread(
            self.prices, self.returns, univ_last, last, 3, 2,
            "top_bottom_deciles", pd.DataFrame(),
        )
        self.assertEqual(res, {"valid": False})


if __name__ == "__main__":
    unittest.main()