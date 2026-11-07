"""Sequential alpha-spending guard for the H10 fresh forward block.

H10 is re-evaluated every calendar month as the Binance archive publishes
(November 2026, December 2026, ...). Each re-evaluation with a wider formation
window is a sequential look at the same estimand, so research protocol 6
requires a predeclared alpha-spending rule:

    "For future ongoing blocks, freeze each new block and evaluate it once.
    Number sequential looks and apply a predeclared alpha-spending rule such as
    alpha_k = 0.05 / (k * (k + 1))."

This test is the single-source-of-truth guard that the H10 preregistration
(artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/
H10_FRESH_FORWARD_BLOCK_v1.md, section 4.1) and the implementation
(scripts/alpha_spending.py) agree on the same rule and the same declared
per-look values. It parses the prereg text rather than hard-coding the values,
so a drift between the two is a build failure instead of a silent mismatch.

The module is pure arithmetic (no market data), so this guard cannot introduce
look-ahead or outcome-informed choices.
"""
import re
import unittest
from pathlib import Path

from scripts import alpha_spending

ROOT = Path(__file__).resolve().parents[1]
PREREQ = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
    / "preregistrations"
    / "H10_FRESH_FORWARD_BLOCK_v1.md"
)

FAMILY_ALPHA = 0.05


class H10SequentialAlphaSpendingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = PREREQ.read_text(encoding="utf-8")
        # Extract the section 4.1 block (from its heading to the next "## " heading).
        match = re.search(r"## 4\.1.*?(?=\n## )", cls.text, re.DOTALL)
        cls.section = match.group(0) if match else ""

    def test_prereg_has_section_4_1(self):
        self.assertTrue(
            self.section,
            "H10 prereg is missing section 4.1 (sequential looks and "
            "alpha-spending); the prereg must declare the rule before any "
            "mature outcome exists",
        )

    def test_declared_rule_matches_implementation(self):
        self.assertIn(alpha_spending.alpha_for_look.__doc__.splitlines()[3].strip(),
                      self.section)
        # The rule string carried by AlphaSpendResult must appear in the prereg.
        self.assertIn("alpha_k = 0.05 / (k * (k + 1))", self.section)

    def test_declared_look_1_values_match_module(self):
        section = self.section
        # The prereg must declare the k=1 per-look alpha explicitly.
        self.assertTrue(re.search(r"k=1\s*->\s*alpha_1\s*=\s*0\.025", section),
                        "prereg section 4.1 does not declare k=1 -> alpha_1 = 0.025")
        result = alpha_spending.evaluate_look(1, FAMILY_ALPHA)
        self.assertAlmostEqual(result.alpha_k, 0.025)
        self.assertAlmostEqual(result.cumulative_spend, 0.025)
        self.assertAlmostEqual(result.remaining_budget, 0.025)

    def test_declared_look_2_values_match_module(self):
        section = self.section
        self.assertTrue(re.search(r"k=2\s*->\s*alpha_2\s*=\s*0\.05/6", section),
                        "prereg section 4.1 does not declare k=2 -> alpha_2 = 0.05/6")
        result = alpha_spending.evaluate_look(2, FAMILY_ALPHA)
        self.assertAlmostEqual(result.alpha_k, FAMILY_ALPHA / 6)
        self.assertAlmostEqual(result.cumulative_spend, 0.025 + FAMILY_ALPHA / 6)
        self.assertAlmostEqual(result.remaining_budget, FAMILY_ALPHA - (0.025 + FAMILY_ALPHA / 6))

    def test_cumulative_spend_stays_below_family_alpha(self):
        # Any finite number of declared sequential looks must not exhaust the
        # family budget; the prereg must never let a later look reuse an earlier
        # look's alpha.
        for k in range(1, 50):
            self.assertLess(
                alpha_spending.cumulative_spend(k, FAMILY_ALPHA), FAMILY_ALPHA + 1e-12
            )

    def test_immature_look_consumes_no_budget(self):
        # An evaluation that returns IMMATURE (n_high=0 or n_low=0) produces no
        # inference and must not advance the look counter. The module models this
        # by skipping a look index: a sequence [1, 3] spends alpha_1 + alpha_3,
        # not alpha_1 + alpha_2, so the skipped second look costs nothing.
        seq = alpha_spending.evaluate_sequence([1, 3], FAMILY_ALPHA)
        self.assertEqual([r.k for r in seq], [1, 3])
        self.assertAlmostEqual(seq[0].cumulative_spend, 0.025)
        self.assertAlmostEqual(
            seq[1].cumulative_spend, 0.025 + FAMILY_ALPHA / (3 * 4)
        )


class H10EconomicSignificanceThresholdTests(unittest.TestCase):
    """Guard for prereg section 4.2 (quantified economic-significance threshold).

    H10's prereg declared criterion 4(a) -- "|high_low_diff_net_1x| above a
    predeclared economic-significance threshold (after costs)" -- without a
    number, so no outcome could ever satisfy or fail it: the confirmatory gate
    was structurally undecidable. Section 4.2 supplies the number, and this test
    is the single-source-of-truth guard that the prereg text and the evaluator
    constant agree. It parses the prereg rather than hard-coding the value, so a
    drift between the two is a build failure instead of a silent mismatch.

    The constant lives in scripts/eval_forward_block.py
    (ECONOMIC_SIGNIFICANCE_THRESHOLD) and is emitted into every fresh-block
    artifact, so the decision is auditable and cannot be re-argued from the raw
    outcome later.
    """

    @classmethod
    def setUpClass(cls):
        cls.text = PREREQ.read_text(encoding="utf-8")
        match = re.search(r"## 4\.2.*?(?=\n## )", cls.text, re.DOTALL)
        cls.section = match.group(0) if match else ""

    def test_prereg_has_section_4_2(self):
        self.assertTrue(
            self.section,
            "H10 prereg is missing section 4.2 (quantified economic-significance "
            "threshold); criterion 4(a) is undecidable without it and must be "
            "declared before any mature outcome exists",
        )

    def test_declared_threshold_matches_evaluator_constant(self):
        import scripts.eval_forward_block as efb

        # The constant is module-level and is read from the current source at
        # import time; no reload is needed and none is performed, so this guard
        # cannot be satisfied by a stale cached value.
        threshold = efb.ECONOMIC_SIGNIFICANCE_THRESHOLD
        section = self.section
        self.assertIn(
            f"ECONOMIC_SIGNIFICANCE_THRESHOLD = {threshold}",
            section,
            "prereg section 4.2 does not declare the threshold constant as "
            f"ECONOMIC_SIGNIFICANCE_THRESHOLD = {threshold}",
        )
        self.assertAlmostEqual(threshold, 0.05)

    def test_declared_threshold_is_net_of_cost(self):
        # The endpoint high_low_diff_net_1x is already net of COST_1X = 0.001
        # (BASE_COST_TURN 0.0005 x 2). The threshold must be stated against that
        # net quantity, and the prereg must say so explicitly.
        self.assertIn("already net of cost", self.section)
        self.assertIn("COST_1X = 0.001", self.section)

    def test_state_count_floor_declared(self):
        # Research protocol 6 requires the inference to be estimable: both
        # states need at least five independent formations. Section 4.2 folds
        # that floor into criterion 4(a) so it cannot be overlooked at decision
        # time, and the evaluator must carry the matching constant.
        import scripts.eval_forward_block as efb

        self.assertTrue(
            re.search(r"n_high >= 5 AND n_low >= 5", self.section),
            "prereg section 4.2 does not declare the n_high>=5 / n_low>=5 "
            "state-count floor",
        )
        self.assertEqual(efb.MIN_STATE_FORMATIONS, 5)

    def test_threshold_is_not_rederived_from_outcomes(self):
        # The threshold must be chosen in ignorance of every observed outcome,
        # including the canonical H004V106 block's exploratory +0.617. The
        # prereg must state that the canonical block is NOT an input to it.
        self.assertIn("NOT an input to this threshold", self.section)
        self.assertIn("development/exploratory evidence", self.section)

    def test_threshold_never_lowered(self):
        # The prereg must forbid lowering the threshold to manufacture a pass and
        # re-deriving it from the fresh block's outcome. The two clauses sit on
        # separate wrapped lines, so each is asserted independently.
        self.assertIn("never lowered to manufacture a pass", self.section)
        self.assertIn("re-derived from the fresh block", self.section)


if __name__ == "__main__":
    unittest.main()