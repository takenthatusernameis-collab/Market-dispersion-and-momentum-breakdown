import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
AUDIT_PATH = ART / "integrity_audit" / "H004V106_rolling_dispersion_window_20261028.json"
BLOCK_PATH = ART / "forward_block" / "forward_block_evaluation.json"
PREREG_PATH = ART / "preregistrations" / "H004V106_ROLLING_DISPERSION_WINDOW_v1.md"


class DispersionRollingWindowTests(unittest.TestCase):
    def test_audit_artifact_exists_and_is_exploratory(self):
        self.assertTrue(AUDIT_PATH.exists(), "rolling-window audit artifact must exist")
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(audit["status"], "EXPLORATORY_ONLY")
        self.assertEqual(audit["experiment_id"],
                         "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-REGIME-002")
        self.assertIn("audited_artifact", audit)
        self.assertIn("conclusion", audit)

    def test_w365_reproduces_anchor_exactly(self):
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        check = audit["anchor_reproduction_check"]
        self.assertTrue(check["match"], "W=365 must reproduce the canonical anchor exactly")
        self.assertEqual(check["W"], 365)
        self.assertAlmostEqual(check["high_low_diff_net_1x"],
                               0.6165223953929935, places=12)

    def test_canonical_block_unchanged(self):
        block = json.loads(BLOCK_PATH.read_text(encoding="utf-8"))
        self.assertEqual(block["anchor_id"], "H004V106")
        self.assertEqual(block["n_formations"], 608)
        self.assertEqual(block["n_high"], 61)
        self.assertEqual(block["n_low"], 90)
        self.assertEqual(block["n_mid"], 457)
        self.assertAlmostEqual(block["high_low_diff_net_1x"],
                               0.6165223953929935, places=12)
        self.assertTrue(block.get("block_sealed"))

    def test_preregistration_exists(self):
        self.assertTrue(PREREG_PATH.exists())
        text = PREREG_PATH.read_text(encoding="utf-8")
        self.assertIn("EXPLORATORY_ONLY", text)
        self.assertIn("REGIME-002", text)
        self.assertIn("W in {30, 90, 180, 270, 365}", text)

    def test_window_labels_follow_predeclared_rules(self):
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        for wr in audit["window_results"]:
            diff = wr["high_low_diff_net_1x"]
            if wr["n_high"] < 5 or wr["n_low"] < 5:
                expected = "SPARSE"
            elif diff is None or diff == 0:
                expected = "SIGN_ZERO"
            elif diff > 0:
                expected = "SIGN_POSITIVE"
            else:
                expected = "SIGN_NEGATIVE"
            self.assertEqual(wr["label"], expected, f"W={wr['W']}")

    def test_overall_label_follows_predeclared_rule(self):
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        adequate = [w for w in audit["window_results"] if w["adequate"]]
        expected = ("ROLLING_ROBUST"
                    if adequate
                    and all(w["label"] == "SIGN_POSITIVE" for w in adequate)
                    and all(
                        w["delta_fraction_vs_full"] is not None
                        and abs(w["delta_fraction_vs_full"]) <= 0.50
                        for w in adequate
                    )
                    else "ROLLING_FRAGILE")
        self.assertEqual(audit["overall_label"], expected)

    def test_windows_cover_predeclared_set(self):
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        self.assertEqual([w["W"] for w in audit["window_results"]], [30, 90, 180, 270, 365])


if __name__ == "__main__":
    unittest.main()
