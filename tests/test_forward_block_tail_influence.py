import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
AUDIT_PATH = ART / "integrity_audit" / "H004V106_forward_block_tail_influence_20261029.json"
BLOCK_PATH = ART / "forward_block" / "forward_block_evaluation.json"
PREREG_PATH = ART / "preregistrations" / "H004V106_FORWARD_BLOCK_TAIL_INFLUENCE_AUDIT_v1.md"
SCRIPT_PATH = ROOT / "scripts" / "forward_block_tail_influence.py"


class ForwardBlockTailInfluenceAuditTests(unittest.TestCase):
    def test_audit_artifact_exists_and_is_exploratory(self):
        self.assertTrue(AUDIT_PATH.exists(), "tail-influence audit artifact must exist")
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(audit["status"], "EXPLORATORY_ONLY")
        self.assertIn(audit["decision_rule"]["label"], {"TAIL_SENSITIVE", "TAIL_ROBUST"})

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
        self.assertIn("DISP-003-TAILAUDIT-001", text)

    def test_script_exists(self):
        self.assertTrue(SCRIPT_PATH.exists())

    def test_audit_baseline_matches_canonical_block(self):
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        block = json.loads(BLOCK_PATH.read_text(encoding="utf-8"))
        self.assertAlmostEqual(audit["baseline_high_low_diff_net_1x"],
                               block["high_low_diff_net_1x"], places=12)
        self.assertEqual(audit["state_counts"], {"high": 61, "low": 90, "mid": 457})
        self.assertEqual(audit["n_formations"], 608)

    def test_state_stats_are_finite_and_plausible(self):
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        for name in ("high", "low"):
            stats = audit["state_stats"][name]
            self.assertIsInstance(stats["mean"], float)
            self.assertIsInstance(stats["median"], float)
            self.assertTrue(math.isfinite(stats["mean"]), f"{name} mean not finite")
            self.assertTrue(math.isfinite(stats["median"]), f"{name} median not finite")
        self.assertEqual(audit["state_stats"]["high"]["n"], 61)
        self.assertEqual(audit["state_stats"]["low"]["n"], 90)

    def test_decision_rule_matches_predeclared_thresholds(self):
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        rule = audit["decision_rule"]
        self.assertEqual(rule["trim_k3_threshold_frac"], 0.20)
        self.assertEqual(rule["winsor_p010_threshold_frac"], 0.20)
        self.assertEqual(rule["loo_threshold_frac"], 0.10)
        label = rule["label"]
        baseline = audit["baseline_high_low_diff_net_1x"]
        k3_frac = audit["trimming"]["k_3"]["delta_frac_vs_baseline"]
        w_frac = audit["winsorization"]["p_0.1"]["delta_frac_vs_baseline"]
        loo_frac = audit["single_formation_leave_one_out"]["max_abs_delta_frac_vs_baseline"]
        expected = ("TAIL_SENSITIVE"
                    if (abs(k3_frac) > 0.20 or abs(w_frac) > 0.20 or abs(loo_frac) > 0.10)
                    else "TAIL_ROBUST")
        self.assertEqual(label, expected)
        self.assertIsInstance(rule["reasons"], list)

    def test_leave_one_out_covers_high_and_low_only(self):
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        loo = audit["single_formation_leave_one_out"]
        states = {rec["state"] for rec in loo["all_records"]}
        self.assertEqual(states, {"high", "low"})
        self.assertEqual(loo["n_formations_tested"], 61 + 90)
        self.assertIsNotNone(loo["extreme_formation"])
        self.assertIsInstance(loo["max_abs_delta"], float)

    def test_tail_concentration_shares_are_finite(self):
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        for name in ("high", "low"):
            for key, entry in audit["tail_concentration"][name].items():
                self.assertIsInstance(entry["count"], int)
                self.assertIsInstance(entry["share_of_total"], (float, type(None)))


if __name__ == "__main__":
    unittest.main()
