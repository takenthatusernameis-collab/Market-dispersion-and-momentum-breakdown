"""Committed-disk verdict pin for scripts/forward_block_independent_recomputation_audit.py (H37).

The hermetic seam suite (test_forward_block_independent_recomputation_audit_seams.py)
exercises the audit only against synthetic fixtures. This module pins the audit's
PASS verdict against the REAL committed artifacts on disk, so the feasibility claims
that the 2026-11-30 Option A decision relies on cannot silently drift:

  - the canonical H004V106 forward block (608 formations, cutoff 2026-09-30) is
    internally consistent under independent recomputation from its formations array;
  - all 19 predeclared checks pass (exact match on n_formations/state_counts,
    1e-9 on means, 1e-12 on high-low differences);
  - the frozen artifact hashes still match the values the audit quotes.

Read-only: no network, no writes. stdlib-only (the audit module imports no
numpy/pandas), so it runs in the dep-light environment too. Path constants are
re-anchored to the repository root in setUpClass so the test is CWD-independent.
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "forward_block_independent_recomputation_audit.py"

spec = importlib.util.spec_from_file_location("forward_block_recompute_audit_committed", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Frozen hash literal the audit is expected to quote (kept here as an independent
# copy so a change to the module constant alone cannot satisfy this test).
EXPECTED_CANONICAL = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"


def _reanchor_paths() -> None:
    """Point the audit module's path constants at ROOT-anchored absolute paths."""
    art = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
    mod.ARTIFACT_DIR = art
    mod.CANONICAL_BLOCK_PATH = art / "forward_block" / "forward_block_evaluation.json"
    mod.ADDENDUM_PATH = art / "integrity_audit" / "forward_block_independent_recomputation_20261028.json"
    mod.OUT_DIR = art / "integrity_audit"
    # The module constant CANONICAL_SHA256 is used directly in the audit; we also
    # cross-check it against our independent literal in the test.


class CommittedRecomputationAuditVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _reanchor_paths()
        required = [
            mod.CANONICAL_BLOCK_PATH,
            mod.ADDENDUM_PATH,
        ]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.result = mod.audit_forward_block_independent_recomputation()

    def test_verdict_is_pass_with_no_failed_checks(self):
        res = self.result
        self.assertEqual(res["verdict"], "PASS")
        self.assertEqual(res["checks_failed"], 0)
        self.assertEqual(res["checks_passed"], res["checks_total"])
        self.assertEqual(res["checks_total"], 19)

    def test_hypothesis_and_status_labels(self):
        res = self.result
        self.assertEqual(res["hypothesis_id"], "H37")
        self.assertEqual(res["status"], "EXPLORATORY_ONLY")
        self.assertEqual(
            res["experiment_id"], "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
        )

    def test_canonical_block_identity_checks(self):
        res = self.result
        # The audit verifies the canonical block's sha256 and key header fields.
        # Find the relevant checks in the results.
        checks_by_name = {c["check"]: c for c in res["checks"]}
        self.assertTrue(checks_by_name["canonical_block_sha256"]["passed"])
        self.assertTrue(checks_by_name["anchor_id"]["passed"])
        self.assertTrue(checks_by_name["block_sealed"]["passed"])
        self.assertTrue(checks_by_name["data_cutoff_utc"]["passed"])
        self.assertTrue(checks_by_name["date_last"]["passed"])

    def test_n_formations_and_state_counts_exact_match(self):
        res = self.result
        checks_by_name = {c["check"]: c for c in res["checks"]}
        self.assertTrue(checks_by_name["n_formations_exact"]["passed"])
        self.assertTrue(checks_by_name["state_counts_exact"]["passed"])
        # Verify the expected values from the canonical block.
        self.assertEqual(res["recomputed"]["n_formations"], 608)
        self.assertEqual(res["recomputed"]["state_counts"], {"high": 61, "mid": 457, "low": 90})

    def test_finite_checks_all_pass(self):
        res = self.result
        checks_by_name = {c["check"]: c for c in res["checks"]}
        self.assertTrue(checks_by_name["all_spread_net_finite"]["passed"])
        self.assertTrue(checks_by_name["all_spread_gross_finite"]["passed"])
        self.assertTrue(checks_by_name["any_non_finite"]["passed"])

    def test_metrics_within_tolerance(self):
        res = self.result
        checks_by_name = {c["check"]: c for c in res["checks"]}
        metric_checks = [
            "spread_net_mean",
            "spread_net_median",
            "spread_gross_mean",
            "spread_gross_median",
            "high_net_mean",
            "low_net_mean",
            "high_low_diff_net",
            "high_low_diff_gross",
        ]
        for check_name in metric_checks:
            self.assertTrue(
                checks_by_name[check_name]["passed"],
                f"metric check {check_name} failed: {checks_by_name[check_name]}",
            )

    def test_reference_value_spot_check(self):
        res = self.result
        checks_by_name = {c["check"]: c for c in res["checks"]}
        self.assertTrue(checks_by_name["ref_high_low_diff_net_1x"]["passed"])

    def test_frozen_hash_matches_committed_artifact(self):
        # The audit verifies the canonical block sha256 against its module constant;
        # this test also cross-checks that constant against an independent literal,
        # so a coordinated change to both the module and a frozen artifact still fails.
        self.assertEqual(mod.sha256_file(mod.CANONICAL_BLOCK_PATH), EXPECTED_CANONICAL)
        self.assertEqual(mod.CANONICAL_SHA256, EXPECTED_CANONICAL)
        # And confirm the audit's own quoted constant agrees with the literal.
        self.assertEqual(self.result["canonical_sha256"], EXPECTED_CANONICAL)


if __name__ == "__main__":
    unittest.main()