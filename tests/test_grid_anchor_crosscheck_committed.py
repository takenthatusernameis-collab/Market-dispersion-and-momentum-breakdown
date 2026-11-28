"""Committed-disk verdict pin for scripts/grid_anchor_crosscheck.py (H004V106).

DISP-003 grid anchor cross-check, EXPLORATORY_ONLY. This closes a
single-source-of-truth gap: the committed cross-check artifact
``H004V106_grid_anchor_crosscheck_20261115.json`` was previously backed only by
``test_grid_anchor_crosscheck_seams.py``, which tests the pure comparison seams
on SYNTHETIC data and deliberately never reads any committed artifact. A drifted
or truncated committed audit could therefore keep passing the synthetic seams
while no longer matching the three real committed artifacts it claims to
cross-check (grid_summary.json, grid_checkpoints/cell_checkpoint.json,
grid_result_ledger.json).

This guard re-runs the SAME read-only pipeline (the module's loaders plus
``compare_formations`` / ``compare_summaries`` / ``check_data_integrity`` /
``build_artifact``) against the committed artifacts -- it writes no file, so the
committed audit bytes are never touched -- and pins the committed artifact's
load-bearing fields (audit identity, status, pass verdict, per-pair
formation/summary match flags and compared counts, per-artifact integrity
roll-up, audited-input sha256 map and conclusion) to that fresh recomputation.
Only ``audit_utc`` may differ. The committed artifact's sha256 is pinned to an
independent literal so a silent rewrite of the committed bytes is caught, and a
synthetic-drift self-test proves the pin is a real constraint (a flipped
committed pass flag, or a perturbed audited-input sha, must not equal a fresh
run).

Read-only: no network, no secrets, no trading endpoints. The loaders read
committed artifacts only; nothing is written.
"""
import hashlib
import json
import unittest
from pathlib import Path

import scripts.grid_anchor_crosscheck as gac

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "artifacts" / gac.EXP / "integrity_audit"
COMMITTED_ARTIFACT = AUDIT_DIR / "H004V106_grid_anchor_crosscheck_20261115.json"

# Independent literal pin for the committed artifact's bytes. If the committed
# audit is ever rewritten (even with identical-looking fields), this fails.
COMMITTED_ARTIFACT_SHA256 = (
    "502aef68037cef32ee87c71738be21bd3466c49471d1cdf4990d3af1b2b2cbd4"
)


def _run_readonly_pipeline() -> dict:
    """Re-derive the cross-check artifact from the committed inputs without
    writing anything (mirrors ``main()`` minus the file write)."""
    gs = gac.load_grid_summary()
    cc = gac.load_cell_checkpoint()
    grl = gac.load_grid_result_ledger()

    formation_checks = {
        "grid_summary_vs_cell_checkpoint": gac.compare_formations(
            gs["formations"], cc["formations"], "grid_summary", "cell_checkpoint"
        ),
        "grid_summary_vs_grid_result_ledger": gac.compare_formations(
            gs["formations"], grl["formations"], "grid_summary", "grid_result_ledger"
        ),
        "cell_checkpoint_vs_grid_result_ledger": gac.compare_formations(
            cc["formations"], grl["formations"], "cell_checkpoint", "grid_result_ledger"
        ),
    }
    summary_checks = {
        "grid_summary_vs_cell_checkpoint": gac.compare_summaries(
            gs, cc, "grid_summary", "cell_checkpoint"
        ),
        "grid_summary_vs_grid_result_ledger": gac.compare_summaries(
            gs, grl, "grid_summary", "grid_result_ledger"
        ),
        "cell_checkpoint_vs_grid_result_ledger": gac.compare_summaries(
            cc, grl, "cell_checkpoint", "grid_result_ledger"
        ),
    }
    integrity_checks = {
        "grid_summary": gac.check_data_integrity(gs["formations"], "grid_summary"),
        "cell_checkpoint": gac.check_data_integrity(cc["formations"], "cell_checkpoint"),
        "grid_result_ledger": gac.check_data_integrity(grl["formations"], "grid_result_ledger"),
    }
    return gac.build_artifact(
        gs, cc, grl, formation_checks, summary_checks, integrity_checks
    )


class CommittedVerdictPinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = json.loads(COMMITTED_ARTIFACT.read_text(encoding="utf-8"))
        cls.rebuilt = _run_readonly_pipeline()

    def test_committed_artifact_exists(self):
        self.assertTrue(
            COMMITTED_ARTIFACT.exists(),
            "committed grid-anchor cross-check artifact is missing",
        )

    def test_artifact_identity_and_status(self):
        a = self.artifact
        self.assertEqual(a["audit_id"], "H004V106_GRID_ANCHOR_CROSSCHECK_20261115")
        self.assertEqual(a["status"], "EXPLORATORY_ONLY")
        self.assertEqual(
            a["preregistration"],
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/"
            "preregistrations/H004V106_GRID_ANCHOR_CROSSCHECK_v1.md",
        )
        self.assertEqual(
            a["audited_artifacts"],
            [
                "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/grid_summary.json",
                "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/"
                "grid_checkpoints/cell_checkpoint.json",
                "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/grid_result_ledger.json",
            ],
        )

    def test_committed_artifact_sha256_pinned(self):
        actual = hashlib.sha256(COMMITTED_ARTIFACT.read_bytes()).hexdigest()
        self.assertEqual(
            actual, COMMITTED_ARTIFACT_SHA256,
            "committed grid-anchor cross-check bytes changed since the pin was set",
        )

    def test_rebuild_matches_committed_artifact(self):
        rebuilt = dict(self.rebuilt)
        committed = dict(self.artifact)
        rebuilt.pop("audit_utc", None)
        committed.pop("audit_utc", None)
        self.assertEqual(
            rebuilt, committed,
            "fresh read-only pipeline over the committed artifacts disagrees with "
            "the committed cross-check artifact (only audit_utc may differ)",
        )

    def test_load_bearing_fields_pinned(self):
        a = self.artifact
        self.assertTrue(a["pass"])
        self.assertIn("PASS:", a["conclusion"])
        # Every pairwise formation check matched all 1338 formations.
        self.assertEqual(
            {k: v["n_compared"] for k, v in a["formation_checks"].items()},
            {
                "grid_summary_vs_cell_checkpoint": 1338,
                "grid_summary_vs_grid_result_ledger": 1338,
                "cell_checkpoint_vs_grid_result_ledger": 1338,
            },
        )
        for name, row in a["formation_checks"].items():
            with self.subTest(formation_check=name):
                self.assertTrue(row["match"])
                self.assertEqual(row["mismatches"], [])
        for name, row in a["summary_checks"].items():
            with self.subTest(summary_check=name):
                self.assertTrue(row["match"])
                self.assertEqual(row["mismatches"], [])
        for name, row in a["integrity_checks"].items():
            with self.subTest(integrity_check=name):
                self.assertTrue(row["all_ok"])
                self.assertEqual(row["issues"], [])
                self.assertEqual(row["n_formations"], 1338)
                self.assertEqual(row["unique_dates"], 1338)

    def test_audited_input_hashes_pinned(self):
        # The committed audit pins the exact bytes of the three cross-checked
        # artifacts; the grid_result_ledger hash is the frozen canonical hash.
        self.assertEqual(
            self.artifact["artifact_sha256"],
            {
                "grid_summary.json": (
                    "d6c408142f118bba3e4c52143e9067385382e941febda370ed27e81617d181bd"
                ),
                "grid_checkpoints/cell_checkpoint.json": (
                    "89bd70964fa17e8573b252351897cc59409b05b947fd7674ff9cc0822b233ecd"
                ),
                "grid_result_ledger.json": (
                    "0184f2d3e5d63dc6fb23a45f0ddfb226a195324d153615588c6c1363a74ce04c"
                ),
            },
        )
        # The freshly recomputed artifact must carry the same input hashes.
        self.assertEqual(
            self.rebuilt["artifact_sha256"], self.artifact["artifact_sha256"]
        )

    def test_pin_is_a_real_constraint_synthetic_drift(self):
        """A flipped committed pass flag / perturbed audited-input sha must not
        equal a fresh run; otherwise the equality pin would accept anything."""
        fresh = dict(self.rebuilt)
        fresh.pop("audit_utc", None)

        flipped_pass = dict(self.artifact)
        flipped_pass.pop("audit_utc", None)
        flipped_pass["pass"] = False
        self.assertNotEqual(flipped_pass, fresh)

        flipped_sha = json.loads(json.dumps(self.artifact))
        flipped_sha.pop("audit_utc", None)
        flipped_sha["artifact_sha256"]["grid_result_ledger.json"] = "0" * 64
        self.assertNotEqual(flipped_sha, fresh)


if __name__ == "__main__":
    unittest.main()