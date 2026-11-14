"""Hermetic tests for pure seams in scripts.dispersion_regime_conditioning.

The committed ``tests/test_dispersion_regime_conditioning.py`` only pins the
audit *artifact* JSON on disk; the module's pure statistical seams
(``pearson``, ``ranks``, ``spearman``, ``high_low_diff``) have no direct test
reference. These tests exercise those seams with synthetic fixtures only.

No network, no committed-panel dependency, no frozen artifact reads/writes.
Synthetic fixtures are software tests only, never market evidence.
"""

import unittest

from scripts.dispersion_regime_conditioning import (
    CONTINUOUS_ASSOC_THRESHOLD,
    REGIME_MIN_PER_STATE,
    high_low_diff,
    pearson,
    ranks,
    spearman,
)


class TestModuleConstants(unittest.TestCase):
    def test_thresholds(self):
        self.assertAlmostEqual(CONTINUOUS_ASSOC_THRESHOLD, 0.30)
        self.assertEqual(REGIME_MIN_PER_STATE, 10)


class TestPearson(unittest.TestCase):
    def test_perfect_positive(self):
        self.assertAlmostEqual(pearson([1, 2, 3], [2, 4, 6]), 1.0, places=12)

    def test_perfect_negative(self):
        self.assertAlmostEqual(pearson([1, 2, 3], [-2, -4, -6]), -1.0, places=12)

    def test_known_value(self):
        self.assertAlmostEqual(
            pearson([1, 2, 3, 4], [2, 4, 5, 8]), 0.9811557810392121, places=12
        )

    def test_too_few_points_returns_none(self):
        self.assertIsNone(pearson([1], [2]))
        self.assertIsNone(pearson([], []))

    def test_zero_variance_x_returns_none(self):
        self.assertIsNone(pearson([1, 1, 1], [1, 2, 3]))

    def test_zero_variance_y_returns_none(self):
        self.assertIsNone(pearson([1, 2, 3], [5, 5, 5]))

    def test_pairing_is_positionwise(self):
        # same multiset, different pairing -> different correlation
        a = pearson([1, 2, 3], [1, 2, 3])
        b = pearson([1, 2, 3], [3, 2, 1])
        self.assertAlmostEqual(a, 1.0, places=12)
        self.assertAlmostEqual(b, -1.0, places=12)


class TestRanks(unittest.TestCase):
    def test_distinct_values_preserve_input_order(self):
        self.assertEqual(ranks([3.0, 1.0, 2.0]), [3.0, 1.0, 2.0])

    def test_ties_get_average_rank(self):
        # values 10,20,20,10 -> sorted 10,10,20,20 -> ranks 1.5,1.5,3.5,3.5
        self.assertEqual(ranks([10.0, 20.0, 20.0, 10.0]), [1.5, 3.5, 3.5, 1.5])

    def test_all_ties_share_one_rank(self):
        self.assertEqual(ranks([5.0, 5.0, 5.0]), [2.0, 2.0, 2.0])

    def test_single_element(self):
        self.assertEqual(ranks([42.0]), [1.0])

    def test_empty(self):
        self.assertEqual(ranks([]), [])

    def test_ranks_are_a_permutation_of_one_to_n_when_distinct(self):
        vals = [9.0, -3.0, 4.5, 0.0, 7.0]
        self.assertEqual(sorted(ranks(vals)), [1.0, 2.0, 3.0, 4.0, 5.0])


class TestSpearman(unittest.TestCase):
    def test_monotonic_increasing(self):
        self.assertAlmostEqual(
            spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0, places=12
        )

    def test_monotonic_decreasing(self):
        self.assertAlmostEqual(
            spearman([1, 2, 3, 4], [40, 30, 20, 10]), -1.0, places=12
        )

    def test_tied_ranks_still_monotonic(self):
        self.assertAlmostEqual(
            spearman([1, 2, 2, 3], [10, 20, 20, 40]), 1.0, places=12
        )

    def test_too_few_points_returns_none(self):
        self.assertIsNone(spearman([1], [2]))

    def test_matches_pearson_of_ranks(self):
        xs = [3.0, 1.0, 4.0, 1.0, 5.0]
        ys = [2.0, 7.0, 1.0, 8.0, 2.0]
        self.assertAlmostEqual(
            spearman(xs, ys), pearson(ranks(xs), ranks(ys)), places=12
        )


class TestHighLowDiff(unittest.TestCase):
    def test_mean_difference_and_counts_ignore_mid(self):
        rows = [
            {"state": "high", "spread_net_1x": 0.20},
            {"state": "high", "spread_net_1x": 0.40},
            {"state": "low", "spread_net_1x": -0.10},
            {"state": "mid", "spread_net_1x": 9.90},
        ]
        diff, nh, nl = high_low_diff(rows)
        self.assertAlmostEqual(diff, 0.40, places=12)
        self.assertEqual(nh, 2)
        self.assertEqual(nl, 1)

    def test_missing_low_returns_none_with_counts(self):
        diff, nh, nl = high_low_diff([{"state": "high", "spread_net_1x": 0.5}])
        self.assertIsNone(diff)
        self.assertEqual(nh, 1)
        self.assertEqual(nl, 0)

    def test_missing_high_returns_none_with_counts(self):
        diff, nh, nl = high_low_diff([{"state": "low", "spread_net_1x": -0.5}])
        self.assertIsNone(diff)
        self.assertEqual(nh, 0)
        self.assertEqual(nl, 1)

    def test_empty_returns_none_zero_counts(self):
        self.assertEqual(high_low_diff([]), (None, 0, 0))

    def test_all_mid_returns_none_zero_counts(self):
        self.assertEqual(
            high_low_diff([{"state": "mid", "spread_net_1x": 1.0}]),
            (None, 0, 0),
        )

    def test_multiple_per_state(self):
        rows = [
            {"state": "high", "spread_net_1x": 0.1},
            {"state": "high", "spread_net_1x": 0.3},
            {"state": "low", "spread_net_1x": -0.2},
            {"state": "low", "spread_net_1x": -0.4},
        ]
        diff, nh, nl = high_low_diff(rows)
        self.assertAlmostEqual(diff, 0.5, places=12)  # mean(0.2) - mean(-0.3)
        self.assertEqual(nh, 2)
        self.assertEqual(nl, 2)


if __name__ == "__main__":
    unittest.main()