import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
AUDIT_PATH = ART / "integrity_audit" / "H004V106_forward_block_temporal_stability_20261029.json"
BLOCK_PATH = ART / "forward_block" / "forward_block_evaluation.json"
SCRIPT_PATH = ROOT / "scripts" / "forward_block_temporal_stability.py"


class ForwardBlockTemporalStabilityTests(unittest.TestCase):
    def test_audit_artifact_exists_and_is_exploratory(self):
        self.assertTrue(AUDIT_PATH.exists(), "temporal stability audit artifact must exist")
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(audit["status"], "EXPLORATORY_ONLY")

    def test_audit_does_not_modify_canonical_block(self):
        block = json.loads(BLOCK_PATH.read_text(encoding="utf-8"))
        self.assertEqual(block["anchor_id"], "H004V106")
        self.assertEqual(block["n_formations"], 608)
        self.assertAlmostEqual(block["high_low_diff_net_1x"], 0.6165223953929935, places=12)
        self.assertTrue(block.get("block_sealed"))

    def test_script_exists(self):
        self.assertTrue(SCRIPT_PATH.exists())

    def test_halves_sum_to_full_block(self):
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(audit["n_first_half"] + audit["n_second_half"], audit["n_formations"])

    def test_bootstrap_values_finite_or_null(self):
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        for key in ("first_half", "second_half"):
            bs = audit[key]["bootstrap"]
            if bs["mean"] is not None:
                self.assertTrue(math.isfinite(bs["mean"]))
                self.assertTrue(math.isfinite(bs["se"]))
                self.assertTrue(math.isfinite(bs["ci_lo"]))
                self.assertTrue(math.isfinite(bs["ci_hi"]))
                self.assertIsInstance(bs["ci_includes_zero"], bool)
        self.assertGreater(audit["n_first_half"], 0)
        self.assertGreater(audit["n_second_half"], 0)


if __name__ == "__main__":
    unittest.main()
