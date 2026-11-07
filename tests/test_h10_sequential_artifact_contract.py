"""Runtime contract: the committed H10 fresh block's sequential alpha-spending
fields match the single source of truth at artifact level.

scripts/eval_forward_block.py emits sequential_* fields from
scripts.alpha_spending.evaluate_look(look_k) (H10 prereg sec 4.1).
test_sequential_alpha_rule_source.py guards the source-level emission pattern
statically; this test pins the committed artifact's emitted VALUES at runtime,
closing the evaluator <-> alpha_spending <-> prereg chain for the sequential-look
and IMMATURE look-counter semantics.

Dep-light: reads JSON only and imports stdlib-only scripts.alpha_spending. It does
NOT import scripts.eval_forward_block (requires numpy/pandas) and touches no
frozen artifact (reads forward_block_h10_fresh/, never forward_block/).

Note: the committed fresh block predates the 2026-11-07 confirmatory-gate
emission (prereg sec 4.2) and cannot be re-sealed in this dep-light env, so its
confirmatory_* block is asserted by source-level guards instead; the sequential
contract below is fully runtime-verifiable here.
"""
import json
import unittest
from pathlib import Path

from scripts import alpha_spending

ROOT = Path(__file__).resolve().parents[1]
FRESH = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
    / "forward_block_h10_fresh"
    / "forward_block_evaluation.json"
)


class H10SequentialArtifactContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fb = json.loads(FRESH.read_text(encoding="utf-8"))

    def test_sequential_fields_match_evaluate_look(self):
        # Every sequential_* artifact field must equal the alpha_spending module's
        # evaluate_look(look_k) output, never a divergent literal.
        look_k = self.fb["sequential_look_number"]
        spend = alpha_spending.evaluate_look(look_k)
        self.assertEqual(self.fb["sequential_family_alpha"], spend.family_alpha)
        self.assertEqual(self.fb["sequential_alpha_k"], spend.alpha_k)
        self.assertEqual(self.fb["sequential_cumulative_spend"], spend.cumulative_spend)
        self.assertEqual(self.fb["sequential_remaining_budget"], spend.remaining_budget)
        self.assertEqual(self.fb["sequential_alpha_rule"], spend.rule)

    def test_look_maturity_derived_from_state_counts(self):
        # sequential_look_mature / sequential_look_consumes_budget must be
        # bool(n_high > 0 and n_low > 0) (H10 prereg sec 4.1 look-counter
        # semantics), never hardcoded to True.
        mature = self.fb["n_high"] > 0 and self.fb["n_low"] > 0
        self.assertEqual(self.fb["sequential_look_mature"], mature)
        self.assertEqual(self.fb["sequential_look_consumes_budget"], mature)

    def test_immature_look_consumes_no_budget_and_keeps_k(self):
        # An IMMATURE look (n_high=0 or n_low=0) produces no inference, consumes
        # no budget and does NOT advance the counter; the next mature evaluation
        # is still look k, not k+1 (prereg sec 4.1).
        self.assertEqual(self.fb["n_high"], 0)
        self.assertEqual(self.fb["n_low"], 0)
        self.assertFalse(self.fb["sequential_look_mature"])
        self.assertFalse(self.fb["sequential_look_consumes_budget"])
        self.assertEqual(self.fb["sequential_look_number"], 1)
        self.assertEqual(self.fb["sequential_remaining_budget"],
                         alpha_spending.evaluate_look(1).remaining_budget)

    def test_spend_budget_respected(self):
        # Cumulative spend for the emitted look must stay at or below the family
        # alpha and remaining_budget must reconcile.
        self.assertLessEqual(self.fb["sequential_cumulative_spend"],
                             self.fb["sequential_family_alpha"] + 1e-12)
        self.assertAlmostEqual(
            self.fb["sequential_cumulative_spend"]
            + self.fb["sequential_remaining_budget"],
            self.fb["sequential_family_alpha"],
        )


if __name__ == "__main__":
    unittest.main()
