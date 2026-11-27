"""Committed-disk verdict pin for scripts/h10_fresh_block_integrity_audit.py (H10 fresh block).

The hermetic seam suite (test_h10_fresh_block_integrity_audit_seams.py) exercises
the audit's pure seams (``finite_value_checks``, ``cost_treatment_check``,
``state_consistency_check``, ``reconcile_inputs``) against synthetic fixtures, but
nothing pins the COMMITTED audit artifact on disk
(``H004V106_H10_fresh_forward_block_integrity_audit_2026-11-15T072518Z.json``) to
a fresh recomputation. If that committed artifact drifted, was truncated, or was
written against a different fresh block, no test would catch it -- the same
single-source-of-truth hazard the committed-disk pins for the maturity-timeline
(H35), independent-recomputation (H37), frozen-tree (H38), expanding-universe
(H33) and prereg-compliance (H34) audits already close. The H10 fresh block is the
exploratory evidence the 2026-11-30 Option A execution re-uses, so its integrity
audit verdict must not silently drift.

The audit's ``main()`` writes a NEW dated artifact, so this pin re-derives the
verdict through the SAME read-only pipeline (``load_h10_fresh`` -> ``reconcile_inputs``
-> ``recompute_h10_fresh`` -> ``finite_value_checks`` -> ``cost_treatment_check``
-> ``state_consistency_check`` -> ``build_artifact``) without writing anything, and
pins the committed artifact's load-bearing fields (verdict, status, audited-block
sha256, recompute-match map, canonical summary/recomputed, finite/cost/state checks)
to that fresh recomputation. The per-file input-hash reconciliation is deliberately
NOT pinned: the audit's own conclusion documents that panel hashes are expected to
change when new public data is appended before the gate, so pinning them would make
this guard fail on the intended data append rather than on real drift.

Read-only: no network, no writes. Path constants are re-anchored to the repository
root in ``setUpClass`` so the test is CWD-independent.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "h10_fresh_block_integrity_audit.py"
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
INTEGRITY_AUDIT_DIR = ART / "integrity_audit"

# The audit imports eval_forward_block, which lives beside it in scripts/.
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("h10_fresh_integrity_committed", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Independent copy of the frozen fresh-block hash so a coordinated change to the
# module constant AND a frozen artifact still fails.
EXPECTED_FRESH = "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f"


def _reanchor_paths() -> None:
    """Point the audit module's path constants at ROOT-anchored absolute paths."""
    mod.ART = ART
    mod.H10_FRESH_BLOCK = ART / "forward_block_h10_fresh" / "forward_block_evaluation.json"
    mod.OUT_DIR = INTEGRITY_AUDIT_DIR


def _committed_audit_artifact() -> Path:
    matches = sorted(INTEGRITY_AUDIT_DIR.glob(
        "H004V106_H10_fresh_forward_block_integrity_audit_*.json"
    ))
    return matches[-1] if matches else Path("/nonexistent")


def _fresh_read_only_artifact() -> dict:
    """Re-derive the audit verdict without writing any dated artifact."""
    canonical = mod.load_h10_fresh()
    reconciliation = mod.reconcile_inputs(canonical)
    recomputed = mod.recompute_h10_fresh(canonical)
    finite_checks = mod.finite_value_checks(recomputed["formation_records"])
    cost_check = mod.cost_treatment_check(recomputed["formation_records"])
    state_check = mod.state_consistency_check(canonical, recomputed)
    return mod.build_artifact(canonical, recomputed, reconciliation, finite_checks,
                              cost_check, state_check)


class CommittedH10FreshIntegrityVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _reanchor_paths()
        required = [mod.H10_FRESH_BLOCK, _committed_audit_artifact()]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.fresh = _fresh_read_only_artifact()
        cls.committed = json.loads(_committed_audit_artifact().read_text())

    def test_fresh_audit_verdict_is_pass(self):
        res = self.fresh
        self.assertTrue(res["pass"])
        self.assertEqual(res["status"], "EXPLORATORY_ONLY")
        self.assertEqual(
            res["audit_id"], "H004V106_H10_FRESH_FORWARD_BLOCK_INTEGRITY_AUDIT"
        )
        self.assertTrue(res["all_recompute_match_within_1e9"])
        self.assertTrue(res["finite_value_checks"]["all_finite"])
        self.assertTrue(res["cost_treatment"]["net_equals_gross_minus_cost"])
        self.assertTrue(res["state_consistency"]["all_consistent"])

    def test_fresh_block_is_immature(self):
        summary = self.fresh["canonical_summary"]
        self.assertEqual(summary["n_formations"], 1)
        self.assertEqual(summary["n_high"], 0)
        self.assertEqual(summary["n_low"], 0)
        self.assertEqual(summary["n_mid"], 1)
        self.assertIsNone(summary["high_low_diff_net_1x"])
        self.assertFalse(summary["confirmatory_claim_allowed"])
        self.assertEqual(
            summary["sequential_look_number"], 1
        )
        self.assertEqual(summary["sequential_alpha_k"], 0.025)

    def test_frozen_hash_matches_committed_artifact(self):
        self.assertEqual(mod.sha256_file(mod.H10_FRESH_BLOCK), EXPECTED_FRESH)
        self.assertEqual(mod.H10_FRESH_BLOCK_SHA256, EXPECTED_FRESH)
        self.assertEqual(self.committed["audited_artifact_sha256"], EXPECTED_FRESH)
        self.assertEqual(self.fresh["audited_artifact_sha256"], EXPECTED_FRESH)

    def test_committed_artifact_matches_fresh_recomputation(self):
        c, f = self.committed, self.fresh
        for key in (
            "status",
            "audit_id",
            "audited_artifact_sha256",
            "all_recompute_match_within_1e9",
            "recompute_match",
            "canonical_summary",
            "canonical_recomputed",
            "finite_value_checks",
            "cost_treatment",
            "state_consistency",
        ):
            self.assertEqual(
                c.get(key), f.get(key),
                msg=f"committed {key!r} drifted from fresh recomputation",
            )
        self.assertTrue(c["pass"])
        self.assertTrue(f["pass"])

    def test_committed_artifact_pin_values(self):
        c = self.committed
        self.assertEqual(c["canonical_summary"]["n_formations"], 1)
        self.assertEqual(c["canonical_summary"]["n_high"], 0)
        self.assertEqual(c["canonical_summary"]["n_low"], 0)
        self.assertEqual(c["canonical_summary"]["n_mid"], 1)
        self.assertEqual(c["canonical_recomputed"]["date_first"], "2026-09-30")
        self.assertEqual(c["canonical_recomputed"]["date_last"], "2026-09-30")
        self.assertEqual(c["canonical_recomputed"]["n_assets_min"], 26)
        self.assertEqual(c["canonical_recomputed"]["n_assets_max"], 26)
        self.assertTrue(
            all(c["recompute_match"].values()),
            "committed artifact carries a failed recompute-match check",
        )

    def test_synthetic_drift_is_detected(self):
        # A fresh block whose header n_high disagrees with its formations must FAIL
        # the state-consistency check, so the committed PASS verdict is a real
        # constraint and not a rubber stamp.
        canonical = mod.load_h10_fresh()
        canonical["n_high"] = 1
        recomputed = mod.recompute_h10_fresh(canonical)
        state = mod.state_consistency_check(canonical, recomputed)
        self.assertFalse(state["all_consistent"])
        self.assertTrue(any("n_high mismatch" in i for i in state["issues"]))
        # A tampered committed artifact (a flipped pass flag) must not equal a fresh
        # recomputation, so the committed-disk comparison is sensitive to drift.
        tampered = json.loads(json.dumps(self.committed))
        tampered["pass"] = False
        self.assertNotEqual(tampered["pass"], self.fresh["pass"])


if __name__ == "__main__":
    unittest.main()