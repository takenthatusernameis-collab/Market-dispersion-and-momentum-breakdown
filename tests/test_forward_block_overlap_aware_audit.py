"""Regression tests for the H004V106 sealed forward block overlap-aware
uncertainty audit artifact (scripts/forward_block_overlap_aware_audit.py).

The audit is read-only: it consumes only the sealed canonical forward block and
recomputes its outcome fields plus the formation-month cluster-bootstrap
(overlap-aware) interval into a NEW artifact under integrity_audit/. The sealed
block itself must never be modified by this audit.

All audits here are EXPLORATORY_ONLY development evidence on the frozen
canonical block (a strict subset of the grid ledger's development window that
was already inspected); none promotes H1/H6/H7 or unlocks the confirmatory
track.
"""

import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
AUDIT = ART / "integrity_audit" / "H004V106_forward_block_overlap_aware_audit_20261102.json"
CANONICAL = ART / "forward_block" / "forward_block_evaluation.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ForwardBlockOverlapAwareAuditTests(unittest.TestCase):
    def test_audit_artifact_exists_and_parses(self):
        self.assertTrue(AUDIT.exists(), f"missing audit artifact: {AUDIT}")
        audit = _load(AUDIT)
        self.assertIsNotNone(audit.get("audit_id"))
        self.assertEqual(audit.get("status"), "EXPLORATORY_ONLY")
        self.assertIn("conclusion", audit)
        self.assertIn("EXPLORATORY_ONLY", audit["conclusion"])

    def test_audit_targets_the_canonical_sealed_block(self):
        audit = _load(AUDIT)
        self.assertEqual(
            audit["audited_artifact"],
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json",
        )
        # The audit must not have modified the audited block: its hash still
        # matches the committed blob.
        canonical = hashlib.sha256(
            subprocess.run(
                ["git", "show", "HEAD:artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json"],
                cwd=ROOT, capture_output=True,
            ).stdout
        ).hexdigest()
        self.assertEqual(audit["audited_artifact_sha256"], canonical)
        self.assertEqual(hashlib.sha256(CANONICAL.read_bytes()).hexdigest(), canonical)

    def test_recomputed_outcomes_match_sealed_block(self):
        block = _load(CANONICAL)
        audit = _load(AUDIT)
        r = audit["canonical_recomputed"]
        self.assertEqual(r["n_formations"], block["n_formations"])
        self.assertEqual(r["n_formations"], 608)
        self.assertEqual(r["state_counts"], {"high": block["n_high"], "low": block["n_low"], "mid": block["n_mid"]})
        self.assertEqual(r["state_counts"], {"high": 61, "low": 90, "mid": 457})
        self.assertEqual(r["finite_dispersion_count"], 608)
        self.assertEqual(r["non_finite_dispersion_count"], 0)
        self.assertAlmostEqual(r["high_low_diff_net_recomputed"], block["high_low_diff_net_1x"], places=12)
        self.assertAlmostEqual(r["spread_net_mean_recomputed"], block["spread_net_1x_mean"], places=12)
        self.assertAlmostEqual(r["spread_net_median_recomputed"], block["spread_net_1x_median"], places=12)

    def test_overlap_aware_interval_is_computed_and_reported(self):
        audit = _load(AUDIT)
        oa = audit["overlap_aware"]
        self.assertEqual(oa["status"], "OK")
        self.assertEqual(oa["rng_seed"], 20261102)
        self.assertIsInstance(oa["n_boot"], int)
        self.assertGreater(oa["n_boot"], 0)
        self.assertLessEqual(oa["n_boot"], 2000)
        self.assertGreater(oa["n_months"], 0)
        self.assertIsInstance(oa["ci_includes_zero"], bool)
        self.assertIsNotNone(oa["baseline_high_low_diff_net_1x"])
        self.assertIsNotNone(oa["bootstrap_mean"])
        self.assertIsNotNone(oa["bootstrap_se"])
        self.assertIsNotNone(oa["ci_95_percentile"][0])
        self.assertIsNotNone(oa["ci_95_percentile"][1])
        lo, hi = oa["ci_95_percentile"]
        self.assertLessEqual(lo, hi)
        self.assertAlmostEqual(oa["baseline_high_low_diff_net_1x"], audit["canonical_recomputed"]["high_low_diff_net_recomputed"], places=12)

    def test_reconciliation_flags_are_all_true(self):
        audit = _load(AUDIT)
        rec = audit["reconciliation"]
        for key in (
            "canonical_reported_vs_recomputed_n_formations_match",
            "canonical_reported_vs_recomputed_diff_net_match",
            "canonical_state_counts_match",
            "canonical_finite_dispersion",
        ):
            self.assertTrue(rec[key], msg=f"reconciliation flag {key} is false")
        self.assertIn("net = gross - 0.001", rec["cost_treatment"])
        self.assertIn("formation-month", rec["overlap_dependence_note"])


if __name__ == "__main__":
    unittest.main()
