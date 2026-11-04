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


if __name__ == "__main__":
    unittest.main()