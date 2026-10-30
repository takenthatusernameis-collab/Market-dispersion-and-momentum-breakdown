"""Regression tests for the sealed forward block's accounting identity.

The canonical H004V106 forward block (forward_block_evaluation.json) records
both gross and net-of-cost spreads per formation, plus state-level means and a
single headline high-minus-low difference. Those headline numbers are the only
quantities the program ever cites, and every prior integrity test asserted only
on the formation *set*, never on the arithmetic that turns formations into the
headline estimate. A cost applied to only one leg, or a headline computed from
a different pairing than the state means, would be invisible to the existing
tests while producing a materially wrong published number.

These tests pin the invariants that make the headline self-consistent with the
underlying formations. They are pure stdlib (json + unittest): the sealed block
is read directly, so they run in environments without pandas/numpy and cannot
fail on missing runtime dependencies.

Observed state (2026-10-30): every invariant holds on the canonical block.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
FB = ART / "forward_block" / "forward_block_evaluation.json"

COST_1X = 0.001  # BASE_COST_TURN 0.0005 * 2, as declared in eval_forward_block.py


def _fb():
    return json.loads(FB.read_text())


class ForwardBlockAccountingTests(unittest.TestCase):
    def test_every_formation_net_equals_gross_minus_cost(self):
        """net_1x == gross - COST_1X for every formation, no exceptions."""
        fb = _fb()
        for f in fb["formations"]:
            with self.subTest(f["formation_date"]):
                self.assertAlmostEqual(
                    f["spread_gross"] - f["spread_net_1x"], COST_1X, places=12,
                    msg="net 1x spread must be gross minus the declared 1x cost",
                )

    def test_headline_diff_equals_state_mean_difference(self):
        """high_low_diff_* == high_*_mean - low_*_mean for both gross and net."""
        fb = _fb()
        self.assertAlmostEqual(
            fb["high_low_diff_gross"],
            fb["high_gross_mean"] - fb["low_gross_mean"], places=12,
            msg="high_low_diff_gross must equal high_gross_mean - low_gross_mean",
        )
        self.assertAlmostEqual(
            fb["high_low_diff_net_1x"],
            fb["high_net_1x_mean"] - fb["low_net_1x_mean"], places=12,
            msg="high_low_diff_net_1x must equal high_net_1x_mean - low_net_1x_mean",
        )

    def test_state_means_are_weighted_by_all_formations_not_subsampled(self):
        """State means must be unweighted means over that state's formations,
        and the headline diff must therefore be a mean-of-means difference, not
        a pooled or size-weighted contrast."""
        fb = _fb()
        for state, key_gross, key_net in (
            ("high", "high_gross_mean", "high_net_1x_mean"),
            ("low", "low_gross_mean", "low_net_1x_mean"),
        ):
            forms = [f for f in fb["formations"] if f["state"] == state]
            self.assertGreater(len(forms), 0)
            with self.subTest(state):
                self.assertAlmostEqual(
                    fb[key_gross],
                    sum(f["spread_gross"] for f in forms) / len(forms), places=12,
                )
                self.assertAlmostEqual(
                    fb[key_net],
                    sum(f["spread_net_1x"] for f in forms) / len(forms), places=12,
                )

    def test_formations_count_matches_n_formations_and_state_counts(self):
        fb = _fb()
        self.assertEqual(len(fb["formations"]), fb["n_formations"])
        import collections
        counts = collections.Counter(f["state"] for f in fb["formations"])
        self.assertEqual(counts["high"], fb["n_high"])
        self.assertEqual(counts["low"], fb["n_low"])
        self.assertEqual(counts["mid"], fb["n_mid"])
        self.assertEqual(fb["n_high"] + fb["n_low"] + fb["n_mid"], fb["n_formations"])

    def test_date_bounds_and_eligible_asset_stats_match_formations(self):
        fb = _fb()
        dates = [f["formation_date"] for f in fb["formations"]]
        self.assertEqual(fb["date_first"], min(dates))
        self.assertEqual(fb["date_last"], max(dates))
        n_assets = [f["n_assets"] for f in fb["formations"]]
        self.assertAlmostEqual(
            fb["eligible_assets_per_date"]["mean"], sum(n_assets) / len(n_assets),
            places=12,
        )
        self.assertEqual(fb["eligible_assets_per_date"]["min"], min(n_assets))
        self.assertEqual(fb["eligible_assets_per_date"]["max"], max(n_assets))

    def test_gross_and_net_headlines_differ_by_exactly_cost_per_formation(self):
        """The gross/net headline pair must differ by exactly COST_1X on every
        aggregate that is a mean or median over formations (the cost is a
        per-formation constant, so it must pass through to aggregates
        unchanged)."""
        fb = _fb()
        for gross, net in (
            ("spread_gross_mean", "spread_net_1x_mean"),
            ("spread_gross_median", "spread_net_1x_median"),
            ("high_gross_mean", "high_net_1x_mean"),
            ("low_gross_mean", "low_net_1x_mean"),
        ):
            with self.subTest(gross):
                self.assertAlmostEqual(
                    fb[gross] - fb[net], COST_1X, places=12,
                    msg=f"{gross} - {net} must equal the per-formation cost",
                )


if __name__ == "__main__":
    unittest.main()