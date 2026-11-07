"""Confirmatory-gate contract tests for the H10 fresh forward block.

H10 prereg section 4 / 4.2 (H10_FRESH_FORWARD_BLOCK_v1.md) and
scripts/eval_forward_block.py define a three-part confirmatory gate for any
fresh-block claim:
  (a) |high_low_diff_net_1x| >= ECONOMIC_SIGNIFICANCE_THRESHOLD (net of cost)
  (b) n_high >= MIN_STATE_FORMATIONS and n_low >= MIN_STATE_FORMATIONS
  (c) Holm-significance across the complete 216-cell family at alpha_k (caller)

A confirmatory claim requires ALL THREE True. (c) is recorded as pending in the
evaluator and must never be inferred here. This module is pure arithmetic +
artifact inspection (no network, no frozen artifact modified) and pins the gate
formula/contract so a drift between prereg, constants, and decision logic fails
the build. It does NOT re-run the block or compute Holm; Holm is out of scope
for this guard and is evaluated only on a mature, admissible fresh block.
"""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_SRC_PATH = ROOT / "scripts" / "eval_forward_block.py"


def _parse_eval_constant(name: str) -> str:
    src = EVAL_SRC_PATH.read_text(encoding="utf-8")
    m = re.search(rf"^{re.escape(name)}\s*=\s*(.+?)\s*(?:#.*)?$", src, re.M)
    if not m:
        raise AssertionError(f"{name} not found in eval_forward_block.py")
    return m.group(1)


def _has_numpy() -> bool:
    try:
        import numpy  # noqa: F401
        return True
    except Exception:
        return False


ECONOMIC_SIGNIFICANCE_THRESHOLD = float(_parse_eval_constant("ECONOMIC_SIGNIFICANCE_THRESHOLD"))
MIN_STATE_FORMATIONS = int(_parse_eval_constant("MIN_STATE_FORMATIONS"))
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
FRESH = ART / "forward_block_h10_fresh" / "forward_block_evaluation.json"
PREREQ = ART / "preregistrations" / "H10_FRESH_FORWARD_BLOCK_v1.md"
EVAL = ROOT / "scripts" / "eval_forward_block.py"


def confirmatory_gate(diff, n_high, n_low, holm_significant):
    """Mirror of eval_forward_block's confirmatory gate (sec 4/4.2)."""
    econ_ok = bool(
        diff is not None and abs(diff) >= ECONOMIC_SIGNIFICANCE_THRESHOLD
    )
    state_ok = bool(
        n_high >= MIN_STATE_FORMATIONS and n_low >= MIN_STATE_FORMATIONS
    )
    allowed = bool(econ_ok and state_ok and holm_significant is True)
    return {
        "economic_significance_met": econ_ok,
        "state_count_floor_met": state_ok,
        "confirmatory_claim_allowed": allowed,
    }


class TestH10ConfirmatoryGateFormula(unittest.TestCase):
    def test_boundary_pass_all_three(self):
        g = confirmatory_gate(0.05, 5, 5, True)
        self.assertTrue(g["economic_significance_met"])
        self.assertTrue(g["state_count_floor_met"])
        self.assertTrue(g["confirmatory_claim_allowed"])

    def test_below_threshold_fails(self):
        g = confirmatory_gate(0.049999, 5, 5, True)
        self.assertFalse(g["economic_significance_met"])
        self.assertFalse(g["confirmatory_claim_allowed"])

    def test_negative_magnitude_satisfies_threshold(self):
        # Sign is NOT pre-registered (H10 sec 4.2); magnitude is what counts.
        g = confirmatory_gate(-0.06, 5, 5, True)
        self.assertTrue(g["economic_significance_met"])
        self.assertTrue(g["confirmatory_claim_allowed"])

    def test_state_floor_n_high_fails(self):
        g = confirmatory_gate(0.10, 4, 5, True)
        self.assertFalse(g["state_count_floor_met"])
        self.assertFalse(g["confirmatory_claim_allowed"])

    def test_state_floor_n_low_fails(self):
        g = confirmatory_gate(0.10, 5, 4, True)
        self.assertFalse(g["state_count_floor_met"])
        self.assertFalse(g["confirmatory_claim_allowed"])

    def test_holm_false_fails(self):
        g = confirmatory_gate(0.10, 5, 5, False)
        self.assertFalse(g["confirmatory_claim_allowed"])

    def test_holm_pending_fails(self):
        # Pending caller evaluation (evaluator emits None) must never allow.
        g = confirmatory_gate(0.10, 5, 5, None)
        self.assertFalse(g["confirmatory_claim_allowed"])

    def test_null_diff_fails(self):
        g = confirmatory_gate(None, 5, 5, True)
        self.assertFalse(g["economic_significance_met"])
        self.assertFalse(g["confirmatory_claim_allowed"])


class TestH10FreshBlockImmatureNotConfirmable(unittest.TestCase):
    """The preserved IMMATURE H10 fresh block cannot satisfy the confirmatory gate."""

    @classmethod
    def setUpClass(cls):
        cls.art = json.loads(FRESH.read_text(encoding="utf-8"))
        cls.prereg = PREREQ.read_text(encoding="utf-8")

    def test_artifact_is_immature(self):
        self.assertEqual(self.art["n_formations"], 1)
        self.assertEqual(self.art["n_high"], 0)
        self.assertEqual(self.art["n_low"], 0)
        self.assertIsNone(self.art["high_low_diff_net_1x"])

    def test_gate_rejects_current_artifact_even_if_holm_true(self):
        # Even with a hypothetical Holm pass (impossible to evaluate on this
        # IMMATURE block), criteria (a) and (b) fail, so no confirmatory claim.
        g = confirmatory_gate(
            self.art["high_low_diff_net_1x"],
            self.art["n_high"],
            self.art["n_low"],
            holm_significant=True,
        )
        self.assertFalse(g["economic_significance_met"])
        self.assertFalse(g["state_count_floor_met"])
        self.assertFalse(g["confirmatory_claim_allowed"])

    def test_prereg_sec4_lists_all_three_criteria(self):
        # The inference rule must name (a) magnitude, (b) Holm at alpha_k, and
        # sec 4.2 must fold in the state-count floor; all must be present.
        self.assertIn("|high_low_diff_net_1x|", self.prereg)
        self.assertIn("Holm-significance", self.prereg)
        self.assertIn("alpha_k", self.prereg)
        self.assertIn("n_high >= 5 AND n_low >= 5", self.prereg)
        self.assertIn("ECONOMIC_SIGNIFICANCE_THRESHOLD = 0.05", self.prereg)

    def test_constants_match_prereg(self):
        self.assertEqual(ECONOMIC_SIGNIFICANCE_THRESHOLD, 0.05)
        self.assertEqual(MIN_STATE_FORMATIONS, 5)


class TestEvaluatorEmitsConfirmatoryGateFields(unittest.TestCase):
    """The current evaluator must emit the confirmatory gate fields for fresh blocks.

    This is an evaluator-contract guard (subprocess into a throwaway dir, no frozen
    artifact modified). It does NOT re-run the committed H10 fresh artifact and does
    NOT compute Holm; it proves the fresh-block output schema records the gate
    constants, per-criterion booleans, and a pending caller-filled Holm field so the
    confirmatory decision is auditable (prereg sec 4/4.2). The IMMATURE case must
    never emit confirmatory_claim_allowed=True.
    """

    @classmethod
    def setUpClass(cls):
        if not _has_numpy():
            raise unittest.SkipTest("numpy not installed; evaluator subprocess contract test is dep-limited")
        cls.td = tempfile.TemporaryDirectory()
        out_dir = Path(cls.td.name) / "h10_gate"
        r = subprocess.run(
            [
                sys.executable,
                str(EVAL),
                "--forward-block-start",
                "2026-09-30",
                "--data-cutoff",
                "2026-10-31",
                "--output-dir",
                str(out_dir),
                "--look-number",
                "1",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, f"evaluator failed: {r.stderr}\n{r.stdout}"
        cls.a = json.loads(
            (out_dir / "forward_block_evaluation.json").read_text(encoding="utf-8")
        )

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "td", None):
            cls.td.cleanup()

    def test_gate_constants_emitted(self):
        self.assertEqual(
            self.a["economic_significance_threshold"],
            ECONOMIC_SIGNIFICANCE_THRESHOLD,
        )
        self.assertEqual(self.a["min_state_formations"], MIN_STATE_FORMATIONS)
        self.assertEqual(self.a["economic_significance_threshold"], 0.05)
        self.assertEqual(self.a["min_state_formations"], 5)

    def test_immature_gate_fields(self):
        # IMMATURE: n_high=0, n_low=0, diff null -> (a),(b),(c-pending) all fail.
        self.assertEqual(self.a["n_high"], 0)
        self.assertEqual(self.a["n_low"], 0)
        self.assertIsNone(self.a["high_low_diff_net_1x"])
        self.assertIsNone(self.a["high_low_diff_net_1x_abs"])
        self.assertFalse(self.a["economic_significance_met"])
        self.assertFalse(self.a["state_count_floor_met"])
        self.assertIsNone(self.a["confirmatory_holm_significant"])
        self.assertFalse(self.a["confirmatory_claim_allowed"])

    def test_holm_field_is_pending_caller_fill(self):
        # The evaluator must never pre-compute Holm across the 216-cell family; it
        # records a pending null and requires the caller to fill it before any
        # SUPPORTED claim. A non-null True/False here would be a contract break.
        self.assertIsNone(self.a["confirmatory_holm_significant"])
        note = self.a["confirmatory_note"]
        self.assertIn("pending caller", note)
        self.assertIn("216-cell family", note)
        self.assertIn("alpha_k", note)

    def test_sequential_fields_emitted_for_fresh_block(self):
        self.assertEqual(self.a["sequential_look_number"], 1)
        self.assertAlmostEqual(self.a["sequential_alpha_k"], 0.025)
        self.assertFalse(self.a["sequential_look_mature"])
        self.assertFalse(self.a["sequential_look_consumes_budget"])


if __name__ == "__main__":
    unittest.main()
