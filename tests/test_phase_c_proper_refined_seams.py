"""Hermetic unit tests for the pure seams in scripts/phase_c_proper.py and scripts/phase_c_refined.py.

Gap: both modules (DISPERSION-001 phase C runners) expose deterministic pure seams
``formation_dates`` and ``momentum`` but no test imports either module or exercises
them directly. Both modules are import-safe (top-level code is only imports and
constants; ``main()`` is guarded by ``__main__``), so the seams can be tested
without touching any committed panel/artifact or the network.

``sha256_file`` is deliberately NOT a target (already covered by
``tests/test_build_universe.py``). ``load_price_panel`` and ``load_universe``
read committed panels and are not hermetic.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PROPER = ROOT / "scripts" / "phase_c_proper.py"
SCRIPT_REFINED = ROOT / "scripts" / "phase_c_refined.py"


def _load_proper():
    spec = importlib.util.spec_from_file_location("phase_c_proper_seams_test", SCRIPT_PROPER)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _load_refined():
    spec = importlib.util.spec_from_file_location("phase_c_refined_seams_test", SCRIPT_REFINED)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _make_returns(n_days: int = 10, n_assets: int = 5, seed: int = 0):
    dates = list(pd.date_range("2026-01-01", periods=n_days, freq="D").strftime("%Y-%m-%d"))
    assets = [f"a{i}" for i in range(n_assets)]
    rng = np.random.RandomState(seed)
    prices = pd.DataFrame(
        100.0 + rng.randn(n_days, n_assets).cumsum(axis=0),
        index=dates,
        columns=assets,
    )
    return prices.pct_change(), dates, assets


class FormationDatesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod_proper = _load_proper()
        cls.mod_refined = _load_refined()

    def _test_module(self, mod):
        # returns first eligible date per month in chronological order
        univ = pd.DataFrame(
            {
                "date": ["2026-01-05", "2026-01-20", "2026-02-03", "2026-03-01", "2026-03-02"],
                "asset_id": ["a"] * 5,
                "eligible": [True, False, True, True, False],
            }
        )
        self.assertEqual(
            mod.formation_dates(None, univ),
            ["2026-01-05", "2026-02-03", "2026-03-01"],
        )

        # no eligible rows -> empty list
        univ_none = pd.DataFrame(
            {
                "date": ["2026-01-05", "2026-02-03"],
                "asset_id": ["a", "a"],
                "eligible": [False, False],
            }
        )
        self.assertEqual(mod.formation_dates(None, univ_none), [])

        # multiple assets per date, still picks first eligible date per month
        univ_multi = pd.DataFrame(
            {
                "date": ["2026-01-05", "2026-01-05", "2026-01-20", "2026-02-03", "2026-02-03"],
                "asset_id": ["a", "b", "a", "a", "b"],
                "eligible": [True, True, False, True, True],
            }
        )
        self.assertEqual(
            mod.formation_dates(None, univ_multi),
            ["2026-01-05", "2026-02-03"],
        )

    def test_phase_c_proper_formation_dates(self):
        self._test_module(self.mod_proper)

    def test_phase_c_refined_formation_dates(self):
        self._test_module(self.mod_refined)


class MomentumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod_proper = _load_proper()
        cls.mod_refined = _load_refined()
        cls.rets, cls.dates, cls.assets = _make_returns(10, 5, seed=42)

    def _test_module(self, mod):
        # compounds only assets with complete window (no NaN in lookback)
        # use a simple deterministic returns matrix
        dates = list(pd.date_range("2026-01-01", periods=4, freq="D").strftime("%Y-%m-%d"))
        rets = pd.DataFrame(
            {
                "a": [0.1, 0.1, 0.1, 0.1],
                "b": [0.2, 0.2, np.nan, 0.2],
                "c": [np.nan, np.nan, np.nan, np.nan],
            },
            index=dates,
        )
        out = mod.momentum(rets, "2026-01-04", 2, ["a", "b", "c"])
        self.assertEqual(list(out.index), ["a"])
        self.assertAlmostEqual(float(out["a"]), 1.1 * 1.1 - 1.0, places=12)

        # end_date not in index -> empty
        self.assertEqual(len(mod.momentum(rets, "2030-01-01", 2, ["a"])), 0)

        # lookback longer than history -> empty
        self.assertEqual(len(mod.momentum(rets, "2026-01-04", 99, ["a"])), 0)

        # all requested assets incomplete -> empty
        self.assertEqual(len(mod.momentum(rets, "2026-01-04", 2, ["c"])), 0)

        # assets list empty -> empty
        self.assertEqual(len(mod.momentum(rets, "2026-01-04", 2, [])), 0)

        # verify compounding formula with known values
        dates2 = list(pd.date_range("2026-01-01", periods=5, freq="D").strftime("%Y-%m-%d"))
        rets2 = pd.DataFrame(
            {"x": [0.0, 0.5, 0.0, 0.0, 0.0]},  # (1+0)*(1+0.5)-1 = 0.5
            index=dates2,
        )
        out2 = mod.momentum(rets2, "2026-01-03", 3, ["x"])  # window: 01-01 to 01-03
        self.assertAlmostEqual(float(out2["x"]), 0.5, places=12)

    def test_phase_c_proper_momentum(self):
        self._test_module(self.mod_proper)

    def test_phase_c_refined_momentum(self):
        self._test_module(self.mod_refined)


if __name__ == "__main__":
    unittest.main()