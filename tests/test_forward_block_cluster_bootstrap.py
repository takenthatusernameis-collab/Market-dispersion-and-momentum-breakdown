import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
AUDIT_PATH = ART / "integrity_audit" / "H004V106_forward_block_cluster_bootstrap_20261029.json"
BLOCK_PATH = ART / "forward_block" / "forward_block_evaluation.json"
SCRIPT_PATH = ROOT / "scripts" / "forward_block_cluster_bootstrap.py"


class ForwardBlockClusterBootstrapTests(unittest.TestCase):
    def test_audit_artifact_exists_and_is_exploratory(self):
        self.assertTrue(AUDIT_PATH.exists(), "cluster bootstrap audit artifact must exist")
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

    def test_audit_baseline_matches_canonical_block(self):
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        block = json.loads(BLOCK_PATH.read_text(encoding="utf-8"))
        self.assertAlmostEqual(audit["baseline_high_low_diff_net_1x"],
                               block["high_low_diff_net_1x"], places=12)
        self.assertEqual(audit["n_formations"], 608)

    def test_bootstrap_values_finite(self):
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        self.assertTrue(math.isfinite(audit["bootstrap_mean"]))
        self.assertTrue(math.isfinite(audit["bootstrap_se"]))
        self.assertTrue(math.isfinite(audit["ci_95_percentile"][0]))
        self.assertTrue(math.isfinite(audit["ci_95_percentile"][1]))
        self.assertGreater(audit["n_boot"], 1000)
        self.assertGreater(audit["n_months"], 0)
        self.assertIsInstance(audit["ci_includes_zero"], bool)


if __name__ == "__main__":
    unittest.main()
