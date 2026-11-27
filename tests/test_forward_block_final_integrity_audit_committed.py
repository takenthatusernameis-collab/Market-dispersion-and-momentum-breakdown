"""Committed-disk verdict pin for scripts/forward_block_final_integrity_audit.py.

The consolidated final integrity audit
(``H004V106_forward_block_final_integrity_audit_20261102.json``) is the single
most load-bearing audit of the canonical H004V106 sealed forward block: it
combines input-hash reconciliation, finite-value checks, state counts,
mean/median, tail influence, cost treatment, overlap-aware uncertainty and an
independent recomputation from RAW PANELS. The existing
``test_forward_block_final_integrity_audit.py`` only pins the committed JSON's
static fields to hardcoded constants; it never re-derives the verdict from the
panels. That leaves a single-source-of-truth gap: if the committed artifact
drifted, was truncated, or was written against a different panel vintage, no
test would catch it.

This module closes that gap the same way the committed-disk pins for the
maturity-timeline (H35), independent-recomputation (H37), frozen-tree (H38),
expanding-universe (H33), prereg-compliance (H34), h10-fresh-integrity and
self-consistency audits already do: it re-runs the SAME read-only pipeline
(``load_canonical`` -> ``reconcile_inputs`` -> ``recompute_block`` ->
``finite_value_checks`` -> ``cost_treatment_check`` -> ``tail_influence`` ->
``overlap_aware_interval`` -> ``build_artifact``) without writing any dated
artifact, and pins the committed artifact's load-bearing fields (pass, status,
audited-block sha256, recompute-match map, canonical summary/recomputed,
finite/cost/tail/overlap checks) to that fresh recomputation.

The per-file input-hash reconciliation is deliberately NOT pinned: the audit's
own conclusion documents that panel hashes are expected to change when new
public data is appended before the gate, so pinning them would make this guard
fail on the intended data append rather than on real drift.

Read-only: no network, no writes. Path constants are re-anchored to the
repository root in ``setUpClass`` so the test is CWD-independent.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "forward_block_final_integrity_audit.py"
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
INTEGRITY_AUDIT_DIR = ART / "integrity_audit"
COMMITTED_AUDIT = INTEGRITY_AUDIT_DIR / "H004V106_forward_block_final_integrity_audit_20261102.json"

# The audit imports eval_forward_block, which lives beside it in scripts/.
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("final_integrity_committed", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Independent copy of the frozen canonical-block hash so a coordinated change to
# the module constant AND a frozen artifact still fails.
EXPECTED_CANONICAL = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"


def _reanchor_paths() -> None:
    """Point the audit module's path constants at ROOT-anchored absolute paths."""
    mod.ART = ART
    mod.CANONICAL_BLOCK = ART / "forward_block" / "forward_block_evaluation.json"
    mod.OUT_DIR = INTEGRITY_AUDIT_DIR


def _fresh_read_only_artifact() -> dict:
    """Re-derive the audit verdict without writing any dated artifact.

    Mirrors ``main()`` exactly (same pipeline, same N_BOOT/RNG_SEED) but returns
    the artifact in memory instead of writing it to ``OUT_DIR``.
    """
    canonical = mod.load_canonical()
    reconciliation = mod.reconcile_inputs(canonical)
    recomputed = mod.recompute_block()
    finite_checks = mod.finite_value_checks(recomputed["formation_records"])
    cost_check = mod.cost_treatment_check(recomputed["formation_records"])
    tail = mod.tail_influence(recomputed["formation_records"])
    overlap_aware = mod.efb.overlap_aware_interval(
        recomputed["formation_records"], n_boot=mod.N_BOOT, rng_seed=mod.RNG_SEED
    )
    artifact = mod.build_artifact(canonical, recomputed, reconciliation,
                                  finite_checks, cost_check, tail, overlap_aware)
    pass_all = (
        recomputed["non_finite_dispersion_count"] == 0
        and finite_checks["all_finite"]
        and cost_check["net_equals_gross_minus_cost"]
        and tail["overall_pass"]
        and overlap_aware.get("status") == "OK"
        and artifact["all_recompute_match_within_1e9"]
    )
    artifact["pass"] = bool(pass_all)
    return artifact


class CommittedFinalIntegrityVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _reanchor_paths()
        required = [mod.CANONICAL_BLOCK, COMMITTED_AUDIT]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.fresh = _fresh_read_only_artifact()
        cls.committed = json.loads(COMMITTED_AUDIT.read_text())

    def test_fresh_audit_verdict_is_pass(self):
        res = self.fresh
        self.assertTrue(res["pass"])
        self.assertEqual(res["status"], "EXPLORATORY_ONLY")
        self.assertEqual(
            res["audit_id"], "H004V106_FORWARD_BLOCK_FINAL_INTEGRITY_AUDIT_20261102"
        )
        self.assertTrue(res["all_recompute_match_within_1e9"])
        self.assertTrue(res["finite_value_checks"]["all_finite"])
        self.assertTrue(res["cost_treatment"]["net_equals_gross_minus_cost"])
        self.assertTrue(res["tail_influence"]["overall_pass"])
        self.assertEqual(res["overlap_aware"]["status"], "OK")

    def test_fresh_recompute_matches_sealed_block(self):
        rec = self.fresh["canonical_recomputed"]
        self.assertEqual(rec["n_formations"], 608)
        self.assertEqual(rec["state_counts"], {"high": 61, "low": 90, "mid": 457})
        self.assertEqual(rec["n_assets_min"], 26)
        self.assertEqual(rec["n_assets_max"], 27)
        self.assertEqual(rec["finite_dispersion_count"], 608)
        self.assertEqual(rec["non_finite_dispersion_count"], 0)
        self.assertEqual(rec["date_first"], "2025-01-01")
        self.assertEqual(rec["date_last"], "2026-08-31")
        self.assertAlmostEqual(
            rec["high_low_diff_net_recomputed"], 0.6165223953929935, places=12
        )

    def test_frozen_hash_matches_committed_artifact(self):
        self.assertEqual(mod.sha256_file(mod.CANONICAL_BLOCK), EXPECTED_CANONICAL)
        self.assertEqual(mod.CANONICAL_SHA256, EXPECTED_CANONICAL)
        self.assertEqual(self.committed["audited_artifact_sha256"], EXPECTED_CANONICAL)
        self.assertEqual(self.fresh["audited_artifact_sha256"], EXPECTED_CANONICAL)

    def test_committed_artifact_matches_fresh_recomputation(self):
        c, f = self.committed, self.fresh
        # ``reconciliation`` and ``audit_utc`` are intentionally excluded: panel
        # hashes are expected to change on the pre-gate data append, and the UTC
        # timestamp is wall-clock. Everything else must be reproducible.
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
            "tail_influence",
            "overlap_aware",
            "pass",
        ):
            self.assertEqual(
                c.get(key), f.get(key),
                msg=f"committed {key!r} drifted from fresh recomputation",
            )
        self.assertTrue(c["pass"])
        self.assertTrue(f["pass"])
        self.assertTrue(c["conclusion"].startswith("PASS:"))

    def test_committed_artifact_pin_values(self):
        c = self.committed
        self.assertEqual(c["canonical_summary"]["n_formations"], 608)
        self.assertEqual(c["canonical_summary"]["n_high"], 61)
        self.assertEqual(c["canonical_summary"]["n_low"], 90)
        self.assertEqual(c["canonical_summary"]["n_mid"], 457)
        self.assertEqual(c["canonical_recomputed"]["date_first"], "2025-01-01")
        self.assertEqual(c["canonical_recomputed"]["date_last"], "2026-08-31")
        self.assertEqual(c["canonical_recomputed"]["n_assets_min"], 26)
        self.assertEqual(c["canonical_recomputed"]["n_assets_max"], 27)
        self.assertTrue(
            all(c["recompute_match"].values()),
            "committed artifact carries a failed recompute-match check",
        )
        self.assertEqual(c["finite_value_checks"]["offending_count"], 0)
        self.assertEqual(c["cost_treatment"]["cost_1x"], 0.001)
        self.assertEqual(len(c["cost_treatment"]["violations"]), 0)

    def test_synthetic_drift_is_detected(self):
        # A canonical block whose header n_high disagrees with a fresh panel
        # recomputation must FAIL the recompute-match state-counts check, so the
        # committed PASS verdict is a real constraint and not a rubber stamp.
        canonical = mod.load_canonical()
        canonical["n_high"] = 999
        recomputed = mod.recompute_block()
        artifact = mod.build_artifact(
            canonical, recomputed, mod.reconcile_inputs(canonical),
            mod.finite_value_checks(recomputed["formation_records"]),
            mod.cost_treatment_check(recomputed["formation_records"]),
            mod.tail_influence(recomputed["formation_records"]),
            {"status": "OK"},
        )
        self.assertFalse(artifact["recompute_match"]["state_counts_match"])
        self.assertFalse(artifact["all_recompute_match_within_1e9"])
        # A tampered committed artifact (a flipped pass flag) must not equal a
        # fresh recomputation, so the committed-disk comparison is sensitive to
        # drift.
        tampered = json.loads(json.dumps(self.committed))
        tampered["pass"] = not self.committed["pass"]
        self.assertNotEqual(tampered["pass"], self.fresh["pass"])


if __name__ == "__main__":
    unittest.main()