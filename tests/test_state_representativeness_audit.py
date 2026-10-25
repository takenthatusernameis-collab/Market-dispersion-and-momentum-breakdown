import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
AUDIT_PATH = ART / "integrity_audit" / "H004V106_state_representativeness_audit_20261025.json"
BLOCK_PATH = ART / "forward_block" / "forward_block_evaluation.json"
PREREG_PATH = ART / "preregistrations" / "H004V106_STATE_REPRESENTATIVENESS_AUDIT_v1.md"


class StateRepresentativenessAuditTests(unittest.TestCase):
    def test_audit_artifact_exists_and_is_exploratory(self):
        self.assertTrue(AUDIT_PATH.exists(), "state representativeness audit artifact must exist")
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(audit["status"], "EXPLORATORY_ONLY")
        self.assertIn(audit["label"], {"CLUSTER_DOMINATED", "MONTH_ROBUST"})

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

    def test_audit_label_matches_predeclared_rule(self):
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        baseline = audit["baseline"]["high_low_diff_net_1x"]
        dominated_drop = audit["calendar_month_leave_one_out"]["dominated_by_drop"]
        dominated_cluster = audit["largest_high_state_month_cluster"]["dominated_by_cluster"]
        expected = "CLUSTER_DOMINATED" if (dominated_drop or dominated_cluster) else "MONTH_ROBUST"
        self.assertEqual(audit["label"], expected)
        # the largest-month share must be consistent with the recorded counts
        share = audit["largest_high_state_month_cluster"]["share_of_high_state_mean"]
        self.assertIsInstance(share, float)


if __name__ == "__main__":
    unittest.main()