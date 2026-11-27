"""Committed-disk verdict pin for scripts/state_representativeness_audit.py (DISP-003-STATEAUDIT-001).

The hermetic seam suite (test_state_representativeness_audit_seams.py) exercises the
month-leave-one-out and largest-cluster computations against synthetic fixtures, and
test_state_representativeness_audit.py only checks the committed artifact's INTERNAL
self-consistency (its label matches its own dominated flags) -- nothing re-derives the
committed artifact's load-bearing numbers from the REAL committed canonical block. If
that committed artifact drifted, was truncated, or was written against a different
canonical block, no test would catch it -- the same single-source-of-truth hazard the
committed-disk pins for the maturity-timeline (H35), independent-recomputation (H37),
frozen-tree (H38), expanding-universe (H33), final-integrity and H10-fresh-integrity
audits already close.

This module re-runs the SAME read-only audit pipeline against the committed canonical
block (writing only to a temp path, never the committed artifact) and pins the committed
artifact's load-bearing fields (label, status, baseline, per-month leave-one-out deltas,
largest-cluster share/counts, calendar counts, conclusion) to that fresh recomputation.
Only ``computed_utc`` is allowed to differ between the committed artifact and a fresh
run. Read-only and stdlib-only (the audit module imports no numpy/pandas); path constants
are re-anchored to the repository root in ``setUpClass`` so the test is CWD-independent.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "state_representativeness_audit.py"
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
COMMITTED_AUDIT = (
    ROOT
    / "artifacts"
    / EXP
    / "integrity_audit"
    / "H004V106_state_representativeness_audit_20261025.json"
)

spec = importlib.util.spec_from_file_location("state_audit_committed", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Independent copy of the frozen canonical hash so a coordinated change to a frozen
# artifact still fails even if a module constant were edited.
EXPECTED_CANONICAL = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"


def _reanchor_paths() -> None:
    """Point the audit module's path constants at ROOT-anchored absolute paths."""
    art = ROOT / "artifacts" / EXP
    mod.BLOCK_PATH = art / "forward_block" / "forward_block_evaluation.json"
    mod.OUT_PATH = (
        art / "integrity_audit" / "H004V106_state_representativeness_audit_20261025.json"
    )


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _run_with_block(block_path: Path):
    """Run the audit against ``block_path`` with OUT_PATH redirected to a temp file.

    The committed artifact is never written: only a temporary OUT_PATH is used and
    the module globals are restored in ``finally``. Returns the parsed fresh output.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_out = Path(tmp) / "audit.json"
        old_block, old_out = mod.BLOCK_PATH, mod.OUT_PATH
        try:
            mod.BLOCK_PATH = block_path
            mod.OUT_PATH = tmp_out
            rc = mod.main()
        finally:
            mod.BLOCK_PATH, mod.OUT_PATH = old_block, old_out
        if rc != 0:
            raise AssertionError("state audit main() returned a nonzero exit code")
        return _load(tmp_out)


class CommittedStateRepresentativenessAuditVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _reanchor_paths()
        required = [mod.BLOCK_PATH, COMMITTED_AUDIT]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.committed = _load(COMMITTED_AUDIT)
        cls.fresh = _run_with_block(mod.BLOCK_PATH)

    def test_fresh_audit_label_and_status(self):
        res = self.fresh
        self.assertEqual(res["status"], "EXPLORATORY_ONLY")
        self.assertEqual(res["label"], "CLUSTER_DOMINATED")
        self.assertEqual(
            res["experiment_id"],
            "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-STATEAUDIT-001",
        )
        self.assertEqual(
            res["audit_id"], "H004V106_STATE_REPRESENTATIVENESS_AUDIT_20261025"
        )

    def test_committed_artifact_matches_fresh_recomputation(self):
        # The whole artifact must be reproduced from the committed canonical block;
        # only computed_utc (a wall-clock timestamp) is allowed to differ.
        c = dict(self.committed)
        f = dict(self.fresh)
        c.pop("computed_utc", None)
        f.pop("computed_utc", None)
        self.assertEqual(
            c, f,
            msg="committed state-representativeness audit drifted from a fresh "
            "recomputation against the committed canonical block",
        )

    def test_committed_artifact_pin_values(self):
        c = self.committed
        b = c["baseline"]
        self.assertEqual(b["n_formations"], 608)
        self.assertEqual(b["n_high"], 61)
        self.assertEqual(b["n_low"], 90)
        self.assertEqual(b["n_mid"], 457)
        self.assertEqual(b["date_first"], "2025-01-01")
        self.assertEqual(b["date_last"], "2026-08-31")
        self.assertEqual(b["data_cutoff_utc"], "2026-09-30T00:00:00Z")
        self.assertAlmostEqual(
            b["high_low_diff_net_1x"], 0.6165223953929935, places=12
        )
        self.assertEqual(c["label"], "CLUSTER_DOMINATED")
        self.assertTrue(c["calendar_month_leave_one_out"]["dominated_by_drop"])
        self.assertEqual(
            c["calendar_month_leave_one_out"]["threshold_frac"], 0.5
        )
        cluster = c["largest_high_state_month_cluster"]
        self.assertEqual(cluster["month"], "2025-10")
        self.assertEqual(cluster["n"], 31)
        self.assertTrue(cluster["dominated_by_cluster"])
        self.assertAlmostEqual(
            cluster["share_of_high_state_mean"], 1.9378011030650497, places=12
        )
        self.assertEqual(
            c["high_state_calendar_counts"],
            {"2025-04": 1, "2025-07": 18, "2025-08": 1, "2025-09": 2,
             "2025-10": 31, "2025-11": 8},
        )
        self.assertEqual(c["last_high_state_formation_date"], "2025-11-15")

    def test_frozen_hash_matches_committed_artifact(self):
        # The audit reads the committed canonical block; pin its sha256 to an
        # independent literal so a swapped block is caught even if the committed
        # artifact were regenerated to match it.
        self.assertEqual(_sha256(mod.BLOCK_PATH), EXPECTED_CANONICAL)
        self.assertEqual(
            self.committed["baseline"]["high_low_diff_net_1x"],
            self.fresh["baseline"]["high_low_diff_net_1x"],
        )

    def test_synthetic_drift_is_detected(self):
        # A tampered committed artifact (a flipped label) must not equal a fresh
        # recomputation, so the committed-disk comparison is sensitive to drift.
        tampered = json.loads(json.dumps(self.committed))
        tampered["label"] = (
            "MONTH_ROBUST" if self.committed["label"] != "MONTH_ROBUST"
            else "CLUSTER_DOMINATED"
        )
        self.assertNotEqual(tampered["label"], self.fresh["label"])

        # A block whose high-state spreads are perturbed must move a RECOMPUTED
        # field, proving the pin is a real constraint on the committed canonical
        # block and not a rubber stamp. The baseline is copied from the block
        # header, but the largest-cluster share is recomputed from the formations,
        # so it must move. The real block file is only read, never written.
        block = _load(mod.BLOCK_PATH)
        for row in block["formations"]:
            if row["state"] == "high":
                row["spread_net_1x"] = row["spread_net_1x"] + 1.0
                break
        with tempfile.TemporaryDirectory() as tmp:
            drift_block = Path(tmp) / "block.json"
            drift_block.write_text(json.dumps(block), encoding="utf-8")
            drifted = _run_with_block(drift_block)
        self.assertNotEqual(
            drifted["largest_high_state_month_cluster"]["share_of_high_state_mean"],
            self.committed["largest_high_state_month_cluster"]["share_of_high_state_mean"],
        )


if __name__ == "__main__":
    unittest.main()