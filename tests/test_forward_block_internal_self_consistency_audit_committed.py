"""Committed-disk verdict pin for scripts/forward_block_internal_self_consistency_audit.py (H38).

The hermetic seam suite (test_forward_block_internal_self_consistency_audit_seams.py)
exercises the audit's pure seams against synthetic fixtures and calls ``audit()``
once against the live canonical block, but nothing pins the COMMITTED audit
artifact on disk
(``H004V106_forward_block_self_consistency_2026-11-15T15-20-24Z.json``) to a fresh
recomputation. If that committed artifact drifted, was truncated, or was written
against a different canonical block, no test would catch it -- the same
single-source-of-truth hazard the committed-disk pins for the maturity-timeline
(H35), independent-recomputation (H37), frozen-tree (H38) and expanding-universe
(H33) audits already close.

This module re-derives the audit verdict from the REAL committed canonical block
and pins the committed artifact's load-bearing fields (verdict, check counts,
per-check expected/actual values, canonical sha256) to that fresh recomputation.
It is read-only and stdlib-only (the audit module imports no numpy/pandas): it
parses the committed JSON and re-runs the pure audit, touches no artifact and
makes no network call. Path constants are re-anchored to the repository root in
``setUpClass`` so the test is CWD-independent.
"""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "forward_block_internal_self_consistency_audit.py"
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
COMMITTED_AUDIT = (
    ROOT
    / "artifacts"
    / EXP
    / "integrity_audit"
    / "H004V106_forward_block_self_consistency_2026-11-15T15-20-24Z.json"
)

spec = importlib.util.spec_from_file_location("fb_selfcheck_audit_committed", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Independent copy of the frozen canonical hash so a coordinated change to the
# module constant AND a frozen artifact still fails.
EXPECTED_CANONICAL = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"


def _reanchor_paths() -> None:
    """Point the audit module's path constants at ROOT-anchored absolute paths."""
    art = ROOT / "artifacts" / EXP
    mod.ARTIFACT_DIR = art
    mod.CANONICAL_BLOCK_PATH = art / "forward_block" / "forward_block_evaluation.json"
    mod.OUT_DIR = art / "integrity_audit"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class CommittedSelfConsistencyAuditVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _reanchor_paths()
        required = [mod.CANONICAL_BLOCK_PATH, COMMITTED_AUDIT]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.fresh = mod.audit()
        cls.committed = _load(COMMITTED_AUDIT)

    def test_fresh_audit_verdict_is_pass_with_all_checks(self):
        res = self.fresh
        self.assertEqual(res["verdict"], "PASS")
        self.assertTrue(res["sha256_match"])
        self.assertTrue(res["header_ok"])
        self.assertEqual(res["checks_failed"], 0)
        self.assertEqual(res["checks_passed"], res["checks_total"])
        self.assertEqual(res["checks_total"], 12)

    def test_hypothesis_and_status_labels(self):
        res = self.fresh
        self.assertEqual(res["hypothesis_id"], "H38")
        self.assertEqual(res["status"], "EXPLORATORY_ONLY")
        self.assertEqual(
            res["experiment_id"], "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
        )
        self.assertEqual(res["frozen_artifacts_modified"], [])

    def test_committed_artifact_matches_fresh_recomputation(self):
        c, f = self.committed, self.fresh
        for key in (
            "verdict",
            "checks_total",
            "checks_passed",
            "checks_failed",
            "canonical_sha256",
            "actual_sha256",
            "header_ok",
            "sha256_match",
            "hypothesis_id",
            "status",
            "scope",
        ):
            self.assertEqual(
                c.get(key), f.get(key),
                msg=f"committed {key!r} drifted from fresh recomputation",
            )
        # The per-check rows must be identical (same checks, same expected/actual,
        # same pass/fail); only generated_utc is allowed to differ between the
        # committed artifact and a fresh run.
        self.assertEqual(c["checks"], f["checks"])

    def test_committed_artifact_pin_values(self):
        c = self.committed
        checks = {row["check"]: row for row in c["checks"]}
        self.assertEqual(checks["n_formations_equals_array_len"]["actual"], 608)
        self.assertEqual(checks["n_high_equals_array_state_count"]["actual"], 61)
        self.assertEqual(checks["n_low_equals_array_state_count"]["actual"], 90)
        self.assertEqual(checks["n_mid_equals_array_state_count"]["actual"], 457)
        self.assertEqual(checks["date_first_equals_array_min"]["actual"], "2025-01-01")
        self.assertEqual(checks["date_last_equals_array_max"]["actual"], "2026-08-31")
        self.assertEqual(checks["eligible_min_equals_array_min"]["actual"], 26)
        self.assertEqual(checks["eligible_max_equals_array_max"]["actual"], 27)
        self.assertTrue(
            all(row["passed"] for row in c["checks"]),
            "committed artifact carries a failed check",
        )

    def test_frozen_hash_matches_committed_artifact(self):
        self.assertEqual(mod.sha256_file(mod.CANONICAL_BLOCK_PATH), EXPECTED_CANONICAL)
        self.assertEqual(mod.CANONICAL_SHA256, EXPECTED_CANONICAL)
        self.assertEqual(self.committed["canonical_sha256"], EXPECTED_CANONICAL)
        self.assertEqual(self.committed["actual_sha256"], EXPECTED_CANONICAL)

    def test_synthetic_drift_is_detected(self):
        # A block whose header n_high disagrees with its formations array must FAIL,
        # so the committed PASS verdict is a real constraint and not a rubber stamp.
        block = mod.load_json(mod.CANONICAL_BLOCK_PATH)
        block["n_high"] = block.get("n_high", 0) + 1
        res = mod.run_checks(block)
        self.assertEqual(res["verdict"], "FAIL")
        failed = [c["check"] for c in res["checks"] if not c["passed"]]
        self.assertIn("n_high_equals_array_state_count", failed)
        # A tampered committed artifact (a flipped pass flag) must not equal a fresh
        # recomputation, so the committed-disk comparison is sensitive to drift.
        tampered = json.loads(json.dumps(self.committed))
        tampered["checks"][0]["passed"] = False
        self.assertNotEqual(tampered["checks"], self.fresh["checks"])


if __name__ == "__main__":
    unittest.main()