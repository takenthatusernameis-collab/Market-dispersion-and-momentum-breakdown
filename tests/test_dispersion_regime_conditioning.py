import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
AUDIT_PATH = ART / "integrity_audit" / "H004V106_dispersion_regime_conditioning_20261028.json"
BLOCK_PATH = ART / "forward_block" / "forward_block_evaluation.json"
PREREG_PATH = ART / "preregistrations" / "H004V106_DISPERSION_REGIME_CONDITIONING_v1.md"


class DispersionRegimeConditioningTests(unittest.TestCase):
    def test_audit_artifact_exists_and_is_exploratory(self):
        self.assertTrue(AUDIT_PATH.exists(), "regime-conditioning audit artifact must exist")
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(audit["status"], "EXPLORATORY_ONLY")
        self.assertEqual(audit["experiment_id"],
                         "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-REGIME-001")

    def test_audit_does_not_modify_canonical_block(self):
        block = json.loads(BLOCK_PATH.read_text(encoding="utf-8"))
        self.assertEqual(block["anchor_id"], "H004V106")
        self.assertEqual(block["n_formations"], 608)
        self.assertEqual(block["n_high"], 61)
        self.assertEqual(block["n_low"], 90)
        self.assertEqual(block["n_mid"], 457)
        self.assertAlmostEqual(block["high_low_diff_net_1x"], 0.6165223953929935, places=12)
        self.assertTrue(block.get("block_sealed"))

    def test_preregistration_exists(self):
        self.assertTrue(PREREG_PATH.exists())
        text = PREREG_PATH.read_text(encoding="utf-8")
        self.assertIn("EXPLORATORY_ONLY", text)
        self.assertIn("REGIME-001", text)

    def test_audit_labels_match_predeclared_rules(self):
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        cont = audit["A_continuous_dispersion_spread_association"]
        rho_excl = cont["excluding_2025_10"]["spearman_rho"]
        expected_cont = ("CONTINUOUS_ASSOCIATION_PRESENT"
                         if rho_excl is not None and abs(rho_excl) >= 0.30
                         else "WEAK_CONTINUOUS_ASSOCIATION")
        self.assertEqual(cont["label"], expected_cont)

        regime = audit["B_dispersion_regime_split"]
        d_lo = regime["regime_low_dispersion"]["high_low_diff_net_1x"]
        d_hi = regime["regime_high_dispersion"]["high_low_diff_net_1x"]
        same_sign = (d_lo is not None and d_hi is not None and (d_lo > 0) == (d_hi > 0))
        nh_lo = regime["regime_low_dispersion"]["n_high"]
        nl_lo = regime["regime_low_dispersion"]["n_low"]
        nh_hi = regime["regime_high_dispersion"]["n_high"]
        nl_hi = regime["regime_high_dispersion"]["n_low"]
        expected_regime = ("REGIME_ROBUST"
                           if (same_sign and nh_lo >= 10 and nl_lo >= 10
                               and nh_hi >= 10 and nl_hi >= 10)
                           else "REGIME_SPARSE_OR_SIGN_FLIP")
        self.assertEqual(regime["label"], expected_regime)

        cond = audit["C_2025_10_conditioning"]
        baseline = cond["baseline_high_low_diff_net_1x"]
        excluded = cond["without_2025_10"]["high_low_diff_net_1x"]
        self.assertAlmostEqual(cond["delta_fraction_vs_baseline"],
                               (excluded - baseline) / baseline, places=12)

    def test_decile_buckets_cover_all_formations(self):
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        buckets = audit["D_dispersion_decile_buckets"]["buckets"]
        self.assertEqual(len(buckets), 10)
        self.assertEqual(sum(b["n"] for b in buckets), 608)


if __name__ == "__main__":
    unittest.main()
