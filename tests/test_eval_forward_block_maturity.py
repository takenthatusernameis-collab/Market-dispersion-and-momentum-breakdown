"""Regression tests for the H10 fresh-block trailing-decile maturity rule.

Pure logic tests on synthetic fixtures: they never read market data, touch the
network, or modify any frozen artifact. They lock in that a formation is
classifiable as high or low only when at least 30 strictly prior in-block
dispersions exist within the trailing window; with fewer priors every
formation is "mid", so an immature block never emits a finite
high_low_diff_net_1x, the state-count floor fails, and no sequential budget is
consumed.
"""

import importlib
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

_HAS_NUMPY_PANDAS = True
try:
    __import__("numpy")
    __import__("pandas")
except Exception:
    _HAS_NUMPY_PANDAS = False

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

try:
    eval_fb = importlib.import_module("eval_forward_block")
    assign_trailing_decile_states = eval_fb.assign_trailing_decile_states
    overlap_aware_interval = eval_fb.overlap_aware_interval
    MIN_PRIOR_DISPERSIONS = eval_fb.MIN_PRIOR_DISPERSIONS
    MIN_STATE_FORMATIONS = eval_fb.MIN_STATE_FORMATIONS
except Exception:
    eval_fb = None
    assign_trailing_decile_states = None
    overlap_aware_interval = None
    MIN_PRIOR_DISPERSIONS = None
    MIN_STATE_FORMATIONS = None


def _dates(n, start="2026-01-01"):
    d0 = date.fromisoformat(start)
    return [d0 + timedelta(days=i) for i in range(n)]


def _form(formation_date, state, spread_net_1x):
    return {
        "formation_date": formation_date,
        "state": state,
        "spread_net_1x": spread_net_1x,
    }


@unittest.skipUnless(
    _HAS_NUMPY_PANDAS and eval_fb is not None,
    "numpy/pandas/eval_forward_block not importable (dep-light env)",
)
class TrailingDecileMaturityTests(unittest.TestCase):
    def test_fewer_than_30_prior_all_mid(self):
        dispersions = {d.isoformat(): 1.0 for d in _dates(30)}
        states = assign_trailing_decile_states(dispersions, window_days=365)
        self.assertEqual(len(states), 30)
        self.assertEqual(set(states.values()), {"mid"})
        self.assertEqual(sum(s == "high" for s in states.values()), 0)
        self.assertEqual(sum(s == "low" for s in states.values()), 0)

    def test_exactly_30_prior_is_classifiable_at_boundary(self):
        base = {d.isoformat(): 1.0 for d in _dates(30)}
        extreme = dict(base)
        extreme["2026-01-31"] = 2.0  # 31st date has exactly 30 strictly prior dispersions
        states = assign_trailing_decile_states(extreme, window_days=365)
        self.assertEqual(states["2026-01-31"], "high")
        self.assertEqual(
            [s for d, s in states.items() if d != "2026-01-31"],
            ["mid"] * 30,
        )

    def test_trailing_window_uses_only_strictly_prior_dispersions(self):
        base = {d.isoformat(): 1.0 for d in _dates(35)}
        both = dict(base)
        both["2026-02-05"] = 2.0   # 36th date: high
        both["2026-02-06"] = 0.5   # 37th date: low
        states = assign_trailing_decile_states(both, window_days=365)
        self.assertEqual(states["2026-02-05"], "high")
        self.assertEqual(states["2026-02-06"], "low")

    def test_min_prior_parameter_is_respected(self):
        dispersions = {d.isoformat(): 1.0 for d in _dates(7)}
        dispersions["2026-01-08"] = 2.0
        states = assign_trailing_decile_states(
            dispersions, window_days=365, min_prior=5
        )
        # The 8th date has 7 priors >= min_prior 5 -> classifiable -> high.
        self.assertEqual(states["2026-01-08"], "high")

    def test_immature_block_emits_no_finite_diff(self):
        dispersions = {d.isoformat(): 1.0 for d in _dates(20)}
        states = assign_trailing_decile_states(dispersions, window_days=365)
        n_high = sum(s == "high" for s in states.values())
        n_low = sum(s == "low" for s in states.values())
        self.assertEqual(n_high, 0)
        self.assertEqual(n_low, 0)
        diff_net = None if not (n_high and n_low) else 0.0
        self.assertIsNone(diff_net)
        self.assertFalse(
            n_high >= MIN_STATE_FORMATIONS and n_low >= MIN_STATE_FORMATIONS
        )
        forms = [_form(d, s, 0.1) for d, s in states.items()]
        ua = overlap_aware_interval(forms, n_boot=200, rng_seed=7)
        self.assertEqual(ua["status"], "IMMATURE")
        self.assertIsNone(ua["baseline_high_low_diff_net_1x"])

    def test_mature_block_emits_finite_diff_and_passes_state_floor(self):
        forms = [
            _form("2026-01-02", "high", 0.2),
            _form("2026-01-03", "high", 0.4),
            _form("2026-01-04", "high", 0.3),
            _form("2026-01-05", "high", 0.5),
            _form("2026-01-06", "high", 0.1),
            _form("2026-01-07", "low", -0.1),
            _form("2026-01-08", "low", -0.3),
            _form("2026-01-09", "low", -0.2),
            _form("2026-01-10", "low", -0.4),
            _form("2026-01-11", "low", -0.1),
        ]
        ua = overlap_aware_interval(forms, n_boot=200, rng_seed=7)
        self.assertEqual(ua["status"], "OK")
        self.assertIsNotNone(ua["baseline_high_low_diff_net_1x"])
        n_high = sum(f["state"] == "high" for f in forms)
        n_low = sum(f["state"] == "low" for f in forms)
        self.assertGreaterEqual(n_high, MIN_STATE_FORMATIONS)
        self.assertGreaterEqual(n_low, MIN_STATE_FORMATIONS)


if __name__ == "__main__":
    unittest.main()
