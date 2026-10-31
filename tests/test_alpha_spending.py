"""Tests for scripts/alpha_spending.py.

The research protocol (docs/research_protocol.md section 6) requires a
predeclared alpha-spending rule for sequential sealed forward-block looks:

    alpha_k = 0.05 / (k * (k + 1))

These tests pin the arithmetic, the budget invariant and the per-look spend so
the H10 preregistration can quote an exact, auditable per-look significance
level instead of a prose promise.
"""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "alpha_spending.py"

spec = importlib.util.spec_from_file_location("alpha_spending", SCRIPT)
alpha_spending = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alpha_spending)


class AlphaSpendingTests(unittest.TestCase):
    def test_first_look_spends_one_third_of_budget(self):
        # k=1: 0.05 / (1*2) = 0.025
        self.assertAlmostEqual(alpha_spending.alpha_for_look(1), 0.025)

    def test_second_look_spends_one_sixth(self):
        # k=2: 0.05 / (2*3) = 0.05/6
        self.assertAlmostEqual(alpha_spending.alpha_for_look(2), 0.05 / 6)

    def test_alpha_decreases_with_each_look(self):
        previous = alpha_spending.alpha_for_look(1)
        for k in range(2, 20):
            current = alpha_spending.alpha_for_look(k)
            self.assertLess(current, previous)
            previous = current

    def test_rejects_non_positive_k(self):
        for bad in (0, -1, -100):
            with self.assertRaises(ValueError):
                alpha_spending.alpha_for_look(bad)

    def test_rejects_invalid_family_alpha(self):
        for bad in (0.0, -0.05, 1.5, float("nan")):
            with self.assertRaises(ValueError):
                alpha_spending.alpha_for_look(1, bad)

    def test_cumulative_spend_is_monotone_and_bounded(self):
        # 1/2 + 1/6 + 1/12 + ... = 1 - 1/(k+1), so spend(k) = 0.05*(1 - 1/(k+1))
        for k in (1, 2, 3, 5, 10, 100, 1000):
            spent = alpha_spending.cumulative_spend(k)
            self.assertAlmostEqual(spent, 0.05 * (1 - 1 / (k + 1)))
        # monotone
        self.assertLess(alpha_spending.cumulative_spend(1),
                        alpha_spending.cumulative_spend(2))
        self.assertLess(alpha_spending.cumulative_spend(2),
                        alpha_spending.cumulative_spend(10))
        # never exceeds family budget
        for k in (1, 2, 3, 10, 100, 10000):
            self.assertLessEqual(alpha_spending.cumulative_spend(k), 0.05)

    def test_budget_invariant_holds(self):
        self.assertTrue(alpha_spending.verify_budget_invariant(max_k=1000))

    def test_evaluate_look_returns_all_fields(self):
        result = alpha_spending.evaluate_look(3)
        self.assertEqual(result.k, 3)
        self.assertAlmostEqual(result.alpha_k, 0.05 / 12)
        self.assertAlmostEqual(result.cumulative_spend, 0.05 * (1 - 1 / 4))
        self.assertAlmostEqual(result.remaining_budget, 0.05 / 4)
        self.assertIn("alpha_k = 0.05 / (k * (k + 1))", result.rule)
        # as_dict is JSON-serialisable
        import json
        json.dumps(result.as_dict())

    def test_sequence_uses_index_not_position(self):
        # A skipped look (k=2 absent) must not consume budget; spend is keyed by
        # the look index, not by position in the supplied sequence.
        seq = alpha_spending.evaluate_sequence([1, 3])
        self.assertAlmostEqual(seq[0].alpha_k, 0.025)
        self.assertAlmostEqual(seq[1].alpha_k, 0.05 / 12)
        self.assertAlmostEqual(seq[1].cumulative_spend,
                               0.05 * (1 - 1 / 2) + 0.05 * (1 - 1 / 4) - 0.05 * (1 - 1 / 2))
        # simpler: spend after looks 1 and 3 == spend(1) + spend(3)
        self.assertAlmostEqual(seq[1].cumulative_spend,
                               alpha_spending.cumulative_spend(1)
                               + alpha_spending.alpha_for_look(3))

    def test_family_budget_never_exhausted_at_finite_k(self):
        # The series asymptotes to family_alpha, so no finite look exhausts it.
        for k in (1, 10, 100, 1000, 10_000):
            self.assertFalse(alpha_spending.family_budget_exhausted(k))


if __name__ == "__main__":
    unittest.main()