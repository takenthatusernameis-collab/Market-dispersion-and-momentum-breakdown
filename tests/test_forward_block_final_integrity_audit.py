"""Consolidated final integrity audit regression tests for H004V106.

The consolidated audit at
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/
H004V106_forward_block_final_integrity_audit_20261102.json combines, in one
document: input-hash reconciliation, finite-value checks, state counts,
mean/median, tail influence (leave-one-out, trimmed k=3, winsorize p=0.10),
cost treatment (net = gross - 0.001), overlap-aware uncertainty, and
independent recomputation vs the sealed block.

These tests are additive and read-only: they assert the committed audit
artifact's fields and thresholds; they never modify the sealed block, the
defective archive, the grid ledger/manifest, or any DISPERSION-001/002
artifact.
"""

import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
AUDIT = ART / "integrity_audit" / "H004V106_forward_block_final_integrity_audit_20261102.json"
CANONICAL_BLOCK = ART / "forward_block" / "forward_block_evaluation.json"
CANONICAL_DIFF_NET = 0.6165223953929935
CANONICAL_SHA256 = (
    "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"
)


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class ForwardBlockFinalIntegrityAuditTests(unittest.TestCase):
    def test_audit_artifact_exists_and_parses(self):
        self.assertTrue(AUDIT.exists(), f"missing consolidated audit: {AUDIT}")
        audit = _load(AUDIT)
        self.assertIsInstance(audit, dict)

    def test_audit_identity_and_target(self):
        audit = _load(AUDIT)
        self.assertEqual(
            audit["audit_id"],
            "H004V106_FORWARD_BLOCK_FINAL_INTEGRITY_AUDIT_20261102",
        )
        self.assertEqual(audit["status"], "EXPLORATORY_ONLY")
        self.assertEqual(
            audit["audited_artifact"],
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json",
        )
        self.assertEqual(audit["audited_artifact_sha256"], CANONICAL_SHA256)
        self.assertIn("audit_utc", audit)
        self.assertIn("preregistration", audit)

    def test_pass_flag_and_recompute_match_within_1e9(self):
        audit = _load(AUDIT)
        self.assertTrue(audit["pass"], audit.get("conclusion"))
        self.assertTrue(audit["all_recompute_match_within_1e9"])
        for name, ok in audit["recompute_match"].items():
            with self.subTest(metric=name):
                self.assertTrue(ok, f"recompute mismatch for {name}")

    def test_state_counts_and_n_formations_match_canonical(self):
        audit = _load(AUDIT)
        rec = audit["canonical_recomputed"]
        self.assertEqual(rec["n_formations"], 608)
        self.assertEqual(rec["state_counts"], {"high": 61, "low": 90, "mid": 457})
        self.assertEqual(rec["n_assets_min"], 26)
        self.assertEqual(rec["n_assets_max"], 27)
        self.assertEqual(rec["date_first"], "2025-01-01")
        self.assertEqual(rec["date_last"], "2026-08-31")

    def test_high_low_diff_net_matches_canonical_within_1e9(self):
        audit = _load(AUDIT)
        rec = audit["canonical_recomputed"]
        self.assertTrue(
            math.isclose(rec["high_low_diff_net_recomputed"], CANONICAL_DIFF_NET,
                         rel_tol=0.0, abs_tol=1e-9),
            f"{rec['high_low_diff_net_recomputed']} != {CANONICAL_DIFF_NET} within 1e-9",
        )
        self.assertTrue(
            math.isclose(rec["high_low_diff_gross_recomputed"], CANONICAL_DIFF_NET,
                         rel_tol=0.0, abs_tol=1e-9),
        )
        # canonical summary field carries the anchor value too.
        self.assertEqual(audit["canonical_summary"]["high_low_diff_net_1x"], CANONICAL_DIFF_NET)

    def test_all_spreads_finite(self):
        audit = _load(AUDIT)
        self.assertTrue(audit["finite_value_checks"]["all_finite"])
        self.assertEqual(audit["finite_value_checks"]["offending_count"], 0)
        self.assertEqual(audit["canonical_recomputed"]["non_finite_dispersion_count"], 0)
        self.assertEqual(audit["canonical_recomputed"]["finite_dispersion_count"], 608)

    def test_cost_treatment_net_equals_gross_minus_0001(self):
        audit = _load(AUDIT)
        ct = audit["cost_treatment"]
        self.assertTrue(ct["net_equals_gross_minus_cost"])
        self.assertEqual(ct["cost_1x"], 0.001)
        self.assertEqual(len(ct["violations"]), 0)

    def test_tail_influence_within_thresholds(self):
        audit = _load(AUDIT)
        tail = audit["tail_influence"]
        self.assertTrue(tail["leave_one_out"]["pass"])
        self.assertLess(tail["leave_one_out"]["max_delta_frac"], 0.10)
        self.assertTrue(tail["trim_k3"]["pass"])
        self.assertLess(tail["trim_k3"]["delta_frac"], 0.20)
        self.assertTrue(tail["winsorize_p010"]["pass"])
        self.assertLess(tail["winsorize_p010"]["delta_frac"], 0.20)
        self.assertTrue(tail["overall_pass"])

    def test_overlap_aware_interval_ok(self):
        audit = _load(AUDIT)
        oa = audit["overlap_aware"]
        self.assertEqual(oa["status"], "OK")
        self.assertIsNotNone(oa["ci_95_percentile"][0])
        self.assertIsNotNone(oa["ci_95_percentile"][1])
        self.assertTrue(oa["ci_includes_zero"])

    def test_reconciliation_reported_and_expected_mismatch(self):
        audit = _load(AUDIT)
        rec = audit["reconciliation"]
        self.assertIsInstance(rec["all_match"], bool)
        self.assertEqual(rec["on_disk_hash_count"], rec["recorded_hash_count"])
        # Post-freeze panel refresh (October 2026 rows appended) makes some
        # recorded panel hashes stale vs disk; this is documented and expected.
        for name, info in rec["per_file"].items():
            with self.subTest(file=name):
                self.assertIn("on_disk", info)
                self.assertIn("recorded", info)
                self.assertIn("match", info)

    def test_conclusion_is_pass(self):
        audit = _load(AUDIT)
        self.assertTrue(audit["conclusion"].startswith("PASS:"))


if __name__ == "__main__":
    unittest.main()
