"""Single-source-of-truth guard for the sequential alpha-spending rule.

The research protocol (section 6) requires a predeclared alpha-spending rule for
sequential sealed forward-block looks. The rule lives in exactly one place:
scripts/alpha_spending.py (AlphaSpendResult.rule default). scripts/eval_forward_block.py
must emit that same rule string into every fresh-block artifact via
`freeze_record["sequential_alpha_rule"] = spend.rule`, never via a hardcoded
literal that could silently diverge from the H10 preregistration section 4.1.

This test parses source only (no import of eval_forward_block, which requires
numpy/pandas), so it runs in dep-light environments and cannot introduce
look-ahead or outcome-informed choices.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_SRC = (ROOT / "scripts" / "eval_forward_block.py").read_text(encoding="utf-8")
ALPHA_SRC = (ROOT / "scripts" / "alpha_spending.py").read_text(encoding="utf-8")


class SequentialAlphaRuleSourceTests(unittest.TestCase):
    def test_eval_forward_block_imports_alpha_spending(self):
        self.assertIn("import alpha_spending", EVAL_SRC,
                      "eval_forward_block.py must import the alpha_spending module "
                      "(the single source of truth for the rule)")

    def test_sequential_alpha_rule_emitted_from_spend_rule_not_hardcoded(self):
        # The sealed artifact must carry the rule from spend.rule; a bare
        # hardcoded literal assigned directly to sequential_alpha_rule is the
        # single-source-of-truth hazard this guard prevents.
        self.assertIn('freeze_record["sequential_alpha_rule"] = spend.rule', EVAL_SRC,
                      "eval_forward_block.py must emit sequential_alpha_rule from "
                      "spend.rule (the alpha_spending module), not a hardcoded literal")
        self.assertNotIn('freeze_record["sequential_alpha_rule"] = "alpha_k', EVAL_SRC,
                         "sequential_alpha_rule must not be assigned a hardcoded rule literal")

    def test_alpha_spending_rule_default_matches_h10_prereg_declaration(self):
        # The module's declared default rule string is what H10 prereg section 4.1
        # quotes; they must stay in sync (test_h10_sequential_alpha_spending parses
        # the prereg text and asserts the same rule string appears there).
        self.assertIn('rule: str = "alpha_k = 0.05 / (k * (k + 1))"', ALPHA_SRC,
                      "alpha_spending.py must declare the rule string quoted by "
                      "H10 prereg section 4.1 as the AlphaSpendResult.rule default")

    def test_sequential_spend_fields_emitted_from_spend_object_not_hardcoded(self):
        # All sealed-artifact sequential alpha fields (except look number/k, which
        # comes from --look-number) must be sourced from the alpha_spending result
        # object, never hardcoded. This prevents a silent divergence between the
        # emitted artifact and the single source of truth in alpha_spending.py.
        for artifact_key, spend_attr in [
            ('sequential_family_alpha', 'spend.family_alpha'),
            ('sequential_alpha_k', 'spend.alpha_k'),
            ('sequential_cumulative_spend', 'spend.cumulative_spend'),
            ('sequential_remaining_budget', 'spend.remaining_budget'),
            ('sequential_alpha_rule', 'spend.rule'),
        ]:
            self.assertIn(
                f'freeze_record["{artifact_key}"] = {spend_attr}',
                EVAL_SRC,
                f"eval_forward_block.py must emit {artifact_key} from {spend_attr} "
                "(alpha_spending single source of truth), not a hardcoded literal",
            )

    def test_alpha_spending_exposes_expected_spend_result_fields(self):
        # The evaluator reads spend.family_alpha/alpha_k/cumulative_spend/
        # remaining_budget/rule; the module must declare these on AlphaSpendResult
        # so the contract is explicit and dep-light-auditable.
        for field in ("family_alpha", "alpha_k", "cumulative_spend",
                      "remaining_budget", "rule"):
            self.assertRegex(
                ALPHA_SRC, rf"\b{field}\b\s*:",
                f"alpha_spending.AlphaSpendResult must declare field {field!r} "
                "consumed by eval_forward_block.py artifact emission",
            )


if __name__ == "__main__":
    unittest.main()
