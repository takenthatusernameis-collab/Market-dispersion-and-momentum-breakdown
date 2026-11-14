"""Hermetic tests for pure seams in scripts.dispersion_rolling_window.

No network, no committed-panel dependency, no frozen artifact reads/writes.
Synthetic fixtures are software tests only, never market evidence.
"""

import unittest

from scripts.dispersion_rolling_window import (
    DELTA_FRAC_BAND,
    MIN_PER_STATE,
    MIN_PRIOR_OBS,
    REFERENCE_HIGH_LOW_DIFF_NET_1X,
    REPRO_TOLERANCE,
    WINDOWS,
    assign_states,
    window_label,
    window_metrics,
)


def _formations(vals):
    return [
        {"formation_date": d, "dispersion": v, "spread_net_1x": s}
        for d, v, s in vals
    ]


class TestModuleConstants(unittest.TestCase):
    def test_windows_and_thresholds(self):
        self.assertEqual(WINDOWS, (30, 90, 180, 270, 365))
        self.assertEqual(MIN_PRIOR_OBS, 30)
        self.assertEqual(MIN_PER_STATE, 5)
        self.assertAlmostEqual(DELTA_FRAC_BAND, 0.50)
        self.assertAlmostEqual(REPRO_TOLERANCE, 1e-9)
        self.assertAlmostEqual(
            REFERENCE_HIGH_LOW_DIFF_NET_1X, 0.6165223953929935
        )


class TestWindowLabel(unittest.TestCase):
    def test_sparse_when_high_insufficient(self):
        self.assertEqual(window_label(4, 10, 1.0), "SPARSE")

    def test_sparse_when_low_insufficient(self):
        self.assertEqual(window_label(10, 4, -1.0), "SPARSE")

    def test_sparse_at_boundary(self):
        self.assertEqual(window_label(4, 5, 1.0), "SPARSE")
        self.assertEqual(window_label(5, 4, 1.0), "SPARSE")

    def test_sign_positive(self):
        self.assertEqual(window_label(5, 5, 0.25), "SIGN_POSITIVE")

    def test_sign_negative(self):
        self.assertEqual(window_label(5, 5, -0.25), "SIGN_NEGATIVE")

    def test_sign_zero_value(self):
        self.assertEqual(window_label(5, 5, 0.0), "SIGN_ZERO")

    def test_sign_zero_none(self):
        self.assertEqual(window_label(5, 5, None), "SIGN_ZERO")


class TestWindowMetrics(unittest.TestCase):
    def test_counts_means_and_diff(self):
        rows = _formations(
            [
                ("2020-01-01", 1.0, 0.20),
                ("2020-01-02", 1.0, 0.40),
                ("2020-01-03", 1.0, -0.10),
                ("2020-01-04", 1.0, 0.00),
            ]
        )
        # inject states
        rows[0]["state"] = "high"
        rows[1]["state"] = "high"
        rows[2]["state"] = "low"
        rows[3]["state"] = "mid"
        m = window_metrics(rows)
        self.assertEqual(m["n_formations"], 4)
        self.assertEqual(m["n_high"], 2)
        self.assertEqual(m["n_low"], 1)
        self.assertEqual(m["n_mid"], 1)
        self.assertAlmostEqual(m["mean_high_net_1x"], 0.30)
        self.assertAlmostEqual(m["mean_low_net_1x"], -0.10)
        self.assertAlmostEqual(m["high_low_diff_net_1x"], 0.40)

    def test_missing_side_returns_none(self):
        rows = [
            {"state": "mid", "spread_net_1x": 1.0},
            {"state": "high", "spread_net_1x": 0.5},
        ]
        m = window_metrics(rows)
        self.assertIsNone(m["high_low_diff_net_1x"])
        self.assertIsNone(m["mean_low_net_1x"])
        self.assertAlmostEqual(m["mean_high_net_1x"], 0.5)

    def test_all_mid(self):
        rows = [{"state": "mid", "spread_net_1x": 1.0}]
        m = window_metrics(rows)
        self.assertEqual(m["n_high"], 0)
        self.assertEqual(m["n_low"], 0)
        self.assertEqual(m["n_mid"], 1)
        self.assertIsNone(m["mean_high_net_1x"])
        self.assertIsNone(m["high_low_diff_net_1x"])


class TestAssignStates(unittest.TestCase):
    def _base(self, n, start_disp=1.0):
        # n formations with distinct dispersions 1..n to create spread
        return [
            {
                "formation_date": f"2020-01-{i:02d}" if i <= 31 else f"2020-02-{i-31:02d}",
                "dispersion": float(i),
                "spread_net_1x": 0.0,
            }
            for i in range(1, n + 1)
        ]

    def test_first_entries_mid_when_insufficient_prior(self):
        formations = self._base(40)
        out = assign_states(formations, window_days=365)
        # indices 0..28 have <30 prior observations
        for i in range(MIN_PRIOR_OBS):
            self.assertEqual(out[i]["state"], "mid", i)
        # index 30 has 30 prior observations -> can be labeled
        self.assertIn(out[30]["state"], {"high", "mid", "low"})

    def test_extreme_values_labeled_high_low(self):
        # 31 prior with dispersions 1..31 (span for deciles), then extremes
        formations = self._base(31) + [
            {"formation_date": "2020-03-01", "dispersion": 100.0, "spread_net_1x": 0.0},
            {"formation_date": "2020-03-02", "dispersion": 0.0, "spread_net_1x": 0.0},
        ]
        out = assign_states(formations, window_days=365)
        by_date = {r["formation_date"]: r["state"] for r in out}
        self.assertEqual(by_date["2020-03-01"], "high")
        self.assertEqual(by_date["2020-03-02"], "low")

    def test_window_caps_prior_history(self):
        # 61 prior observations then a probe; large window == all history,
        # small window uses tail only so thresholds can differ in general.
        formations = self._base(61) + [
            {"formation_date": "2020-04-01", "dispersion": 62.0, "spread_net_1x": 0.0}
        ]
        out_full = assign_states(formations, window_days=365)
        out_big = assign_states(formations, window_days=1000)
        # window larger than available history equals full available past
        self.assertEqual(out_full[-1]["state"], out_big[-1]["state"])
        self.assertIn(out_full[-1]["state"], {"high", "mid", "low"})

    def test_preserves_original_fields(self):
        formations = self._base(35)
        formations[34]["spread_net_1x"] = 0.123
        out = assign_states(formations, window_days=365)
        self.assertIn("state", out[-1])
        self.assertAlmostEqual(out[-1]["spread_net_1x"], 0.123)
        self.assertEqual(out[-1]["formation_date"], formations[34]["formation_date"])
        # original list not mutated
        self.assertNotIn("state", formations[34])


if __name__ == "__main__":
    unittest.main()
