"""Regression tests for the Holm p-value construction defect.

DISPERSION-003 built its Holm step-down input as abs(high_low_diff_net_1x),
which is a raw mean difference, not a p-value. Any nonzero difference was then
compared against alpha/(m-k+1) and could be flagged "significant". The corrected
pipeline uses a two-sided block-bootstrap p-value and validates its domain.

These tests pin the corrected inference path.
"""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_dispersion003_grid.py"

spec = importlib.util.spec_from_file_location("run_grid", SCRIPT)
run_grid = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_grid)


class HolmPvalueTests(unittest.TestCase):
    def test_abs_diff_was_not_a_pvalue(self):
        """The old code fed abs(mean difference) into Holm; that is not a p-value.

        A mean difference is not bounded to [0, 1]. The real defective values
        were ~1e128 (price-level dispersion) and ~0.3-0.6 (return dispersion).
        The domain check rejects anything outside [0, 1], so a genuine defective
        input is caught; a coincidental in-range value is not, which is why the
        fix also has to live at the call site (bootstrap p-value), not only here.
        """
        # Real defective magnitude from the price-level bug: must be rejected.
        with self.assertRaises(ValueError):
            run_grid.holm_step_down({"H004V001": 1.785698233962778e+128})
        # A coincidental in-range value is accepted by the domain check alone;
        # the call site must not feed it in.
        rej = run_grid.holm_step_down({"H004V001": 0.3}, 0.05)
        self.assertFalse(rej["H004V001"])

    def test_holm_rejects_only_after_real_pvalues(self):
        # Genuine p-values in [0,1]; nothing significant at alpha 0.05 across 216.
        pvals = {f"H004V{i:03d}": 0.5 for i in range(1, 217)}
        rej = run_grid.holm_step_down(pvals, 0.05)
        self.assertFalse(any(rej.values()))
        self.assertEqual(len(rej), 216)

    def test_holm_detects_one_significant_after_correction(self):
        # m=3, alpha=0.05. Sorted p: 0.001, 0.02, 0.04.
        # k=1: 0.05/3=0.0167 -> 0.001 rejected
        # k=2: 0.05/2=0.025 -> 0.02 rejected
        # k=3: 0.05/1=0.05  -> 0.04 rejected
        pvals = {"a": 0.001, "b": 0.02, "c": 0.04}
        rej = run_grid.holm_step_down(pvals, 0.05)
        self.assertTrue(all(rej.values()))

    def test_holm_stops_at_first_non_significant(self):
        # m=3. p: 0.001, 0.03, 0.04.
        # k=1: 0.0167 -> 0.001 rejected
        # k=2: 0.025 -> 0.03 NOT rejected, stop.
        pvals = {"a": 0.001, "b": 0.03, "c": 0.04}
        rej = run_grid.holm_step_down(pvals, 0.05)
        self.assertTrue(rej["a"])
        self.assertFalse(rej["b"])
        self.assertFalse(rej["c"])

    def test_bootstrap_pvalue_is_in_unit_interval(self):
        rng = __import__("random").Random(1)
        high = [rng.uniform(-0.1, 0.1) for _ in range(100)]
        low = [rng.uniform(-0.1, 0.1) for _ in range(100)]
        p = run_grid.bootstrap_diff_pvalue(high, low, block_len=10, n_boot=200, seed=1)
        self.assertGreaterEqual(p, 0.0)
        self.assertLessEqual(p, 1.0)

    def test_bootstrap_is_symmetric_under_sign_flip(self):
        rng = __import__("random").Random(2)
        base = [rng.uniform(-0.1, 0.1) for _ in range(100)]
        p_pos = run_grid.bootstrap_diff_pvalue(base, [b * 0.5 for b in base],
                                                block_len=10, n_boot=200, seed=2)
        p_neg = run_grid.bootstrap_diff_pvalue([-b for b in base],
                                               [-b * 0.5 for b in base],
                                               block_len=10, n_boot=200, seed=2)
        self.assertAlmostEqual(p_pos, p_neg, places=12)

    def test_committed_ledger_uses_real_pvalues_not_abs_diff(self):
        import json
        ledger = json.loads(
            (ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
             / "grid_result_ledger.json").read_text()
        )
        self.assertEqual(ledger["cells_ok"], 216)
        self.assertEqual(ledger["cells_evaluated"], 216)
        # With genuine p-values no cell survives Holm at 0.05 across 216.
        self.assertEqual(ledger["holm_rejected_count"], 0)
        self.assertIn("pvalue_method", ledger)
        for cid, cell in ledger["cells"].items():
            if cell.get("holm_rejected") is True:
                self.assertIn("pvalue_bootstrap_two_sided", cell)
                self.assertGreaterEqual(cell["pvalue_bootstrap_two_sided"], 0.0)
                self.assertLessEqual(cell["pvalue_bootstrap_two_sided"], 1.0)


if __name__ == "__main__":
    unittest.main()