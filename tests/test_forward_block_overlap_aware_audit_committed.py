"""Committed-disk verdict pin for scripts/forward_block_overlap_aware_audit.py (H004V106).

The hermetic seam coverage exercises overlap_aware_interval against synthetic
fixtures, but nothing re-derives the committed artifact
``H004V106_forward_block_overlap_aware_audit_20261102.json`` from the REAL
committed canonical block. If that committed artifact drifted, was truncated, or
was written against a different canonical block, no test would catch it -- the
same single-source-of-truth hazard the committed-disk pins for the
state-representativeness (DISP-003-STATEAUDIT-001), maturity-timeline (H35),
independent-recomputation (H37), frozen-tree (H38), expanding-universe (H33),
final-integrity and H10-fresh-integrity audits already close.

This module re-runs the SAME read-only audit pipeline against the committed
canonical block (writing only to a temp dir under ROOT, never the committed
artifact) and pins the committed artifact's load-bearing fields (status, audit_id,
audited_artifact_sha256, canonical_summary, canonical_recomputed, reconciliation,
overlap_aware, conclusion) to that fresh recomputation. Only ``audit_utc`` (a
wall-clock timestamp) is allowed to differ. Read-only; no frozen artifact, grid
ledger, DISPERSION-001/002 file or forward-block input is modified. Path
constants are re-anchored to the repository root in ``setUpClass`` so the test is
CWD-independent.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "forward_block_overlap_aware_audit.py"
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
AUDIT_FILENAME = "H004V106_forward_block_overlap_aware_audit_20261102.json"
COMMITTED_AUDIT = (
    ROOT
    / "artifacts"
    / EXP
    / "integrity_audit"
    / AUDIT_FILENAME
)

spec = importlib.util.spec_from_file_location("overlap_aware_audit_committed", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Independent copy of the frozen canonical hash so a coordinated change to a frozen
# artifact still fails even if a module constant were edited.
EXPECTED_CANONICAL = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"


def _reanchor_paths() -> None:
    """Point the audit module's path constants at ROOT-anchored absolute paths."""
    art = ROOT / "artifacts" / EXP
    mod.CANONICAL = art / "forward_block" / "forward_block_evaluation.json"
    mod.AUDIT_DIR = art / "integrity_audit"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _run_with_block(block_path: Path):
    """Run the audit against ``block_path`` writing only to a temp dir under ROOT.

    The committed artifact is never written: AUDIT_DIR is redirected to a
    temporary directory (created inside ROOT so ``relative_to(ROOT)`` inside the
    module keeps working) and the module globals are restored in ``finally``.
    Returns the parsed fresh output.
    """
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        tmp = Path(tmp)
        out_name = AUDIT_FILENAME
        old_canonical, old_audit_dir = mod.CANONICAL, mod.AUDIT_DIR
        try:
            mod.CANONICAL = block_path
            mod.AUDIT_DIR = tmp
            rc = mod.main()
        finally:
            mod.CANONICAL, mod.AUDIT_DIR = old_canonical, old_audit_dir
        if rc != 0:
            raise AssertionError("overlap-aware audit main() returned a nonzero exit code")
        return _load(tmp / out_name)


class CommittedForwardBlockOverlapAwareAuditVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _reanchor_paths()
        required = [mod.CANONICAL, COMMITTED_AUDIT]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.committed = _load(COMMITTED_AUDIT)
        cls.fresh = _run_with_block(mod.CANONICAL)

    def test_fresh_audit_label_and_status(self):
        res = self.fresh
        self.assertEqual(res["status"], "EXPLORATORY_ONLY")
        self.assertEqual(
            res["audit_id"],
            "H004V106_FORWARD_BLOCK_OVERLAP_AWARE_AUDIT_20261102",
        )
        self.assertEqual(res["audited_artifact"],
                         "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json")

    def test_committed_artifact_matches_fresh_recomputation(self):
        # The whole artifact must be reproduced from the committed canonical block;
        # only audit_utc (a wall-clock timestamp) is allowed to differ.
        c = dict(self.committed)
        f = dict(self.fresh)
        c.pop("audit_utc", None)
        f.pop("audit_utc", None)
        self.assertEqual(
            c, f,
            msg="committed forward-block overlap-aware audit drifted from a fresh "
            "recomputation against the committed canonical block",
        )

    def test_committed_artifact_pin_values(self):
        c = self.committed
        s = c["canonical_summary"]
        self.assertEqual(s["n_formations"], 608)
        self.assertEqual(s["n_high"], 61)
        self.assertEqual(s["n_low"], 90)
        self.assertEqual(s["n_mid"], 457)
        self.assertEqual(s["date_first"], "2025-01-01")
        self.assertEqual(s["date_last"], "2026-08-31")
        self.assertEqual(s["data_cutoff_utc"], "2026-09-30T00:00:00Z")
        self.assertTrue(s["block_sealed"])
        self.assertIsNone(s["overlap_aware_uncertainty"])
        self.assertAlmostEqual(
            s["high_low_diff_net_1x"], 0.6165223953929935, places=12
        )
        self.assertAlmostEqual(
            s["high_low_diff_gross"], 0.6165223953929935, places=12
        )
        r = c["canonical_recomputed"]
        self.assertEqual(r["n_formations"], 608)
        self.assertEqual(r["state_counts"], {"high": 61, "low": 90, "mid": 457})
        self.assertEqual(r["finite_dispersion_count"], 608)
        self.assertEqual(r["non_finite_dispersion_count"], 0)
        self.assertAlmostEqual(
            r["high_low_diff_net_recomputed"], 0.6165223953929936, places=12
        )
        rec = c["reconciliation"]
        self.assertTrue(rec["canonical_reported_vs_recomputed_n_formations_match"])
        self.assertTrue(rec["canonical_reported_vs_recomputed_diff_net_match"])
        self.assertTrue(rec["canonical_state_counts_match"])
        self.assertTrue(rec["canonical_finite_dispersion"])
        ov = c["overlap_aware"]
        self.assertEqual(ov["status"], "OK")
        self.assertEqual(ov["n_boot"], 1999)
        self.assertEqual(ov["n_months"], 20)
        self.assertEqual(ov["n_clusters_with_both_states"], 2)
        self.assertTrue(ov["ci_includes_zero"])
        self.assertAlmostEqual(
            ov["baseline_high_low_diff_net_1x"], 0.6165223953929937, places=12
        )
        self.assertEqual(c["audited_artifact_sha256"], EXPECTED_CANONICAL)
        self.assertEqual(c["status"], "EXPLORATORY_ONLY")

    def test_frozen_hash_matches_committed_artifact(self):
        # The audit reads the committed canonical block; pin its sha256 to an
        # independent literal so a swapped block is caught even if the committed
        # artifact were regenerated to match it.
        self.assertEqual(_sha256(mod.CANONICAL), EXPECTED_CANONICAL)
        self.assertEqual(
            self.committed["audited_artifact_sha256"],
            self.fresh["audited_artifact_sha256"],
        )

    def test_synthetic_drift_is_detected(self):
        # A tampered committed artifact (a flipped status) must not equal a fresh
        # recomputation, so the committed-disk comparison is sensitive to drift.
        tampered = json.loads(json.dumps(self.committed))
        tampered["status"] = (
            "CONFIRMATORY" if self.committed["status"] != "CONFIRMATORY"
            else "EXPLORATORY_ONLY"
        )
        self.assertNotEqual(tampered["status"], self.fresh["status"])

        # A block whose high-state spreads are perturbed must move a RECOMPUTED
        # field (high_low_diff_net_recomputed), proving the pin is a real
        # constraint on the committed canonical block and not a rubber stamp.
        block = _load(mod.CANONICAL)
        for row in block["formations"]:
            if row["state"] == "high":
                row["spread_net_1x"] = row["spread_net_1x"] + 1.0
                break
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            drift_block = Path(tmp) / "block.json"
            drift_block.write_text(json.dumps(block), encoding="utf-8")
            drifted = _run_with_block(drift_block)
        self.assertNotEqual(
            drifted["canonical_recomputed"]["high_low_diff_net_recomputed"],
            self.committed["canonical_recomputed"]["high_low_diff_net_recomputed"],
        )


if __name__ == "__main__":
    unittest.main()
