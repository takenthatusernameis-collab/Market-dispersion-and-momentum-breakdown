"""Committed-disk verdict pin for scripts/panel_wave_b_quality_audit.py (H54).

DISP-003-PANELQA-WAVEB-001, EXPLORATORY_ONLY. This closes a single-source-of-
truth gap: the committed wave-B panel quality audit artifact
``panel_wave_b_quality_audit_2026-11-19T185617Z.json`` was previously backed only
by ``CommittedArtifactTests`` in ``test_panel_wave_b_quality_audit.py``, which
checks the artifact's INTERNAL self-consistency (labels, frozen-hash flags,
per-panel sha flags, histogram sums) and never re-derives the verdict from the
REAL committed H53 panels. A drifted or truncated committed audit could
therefore keep passing while no longer matching the panels on disk.

This guard re-runs the SAME read-only pipeline (``qa.run_audit()``) against the
committed H53 panels and H53 normalization audit -- it writes no file -- and
pins the committed artifact's load-bearing fields (audit/experiment/hypothesis
identity, status, verdict, panel count, scope_problems, cross-panel day counts,
thresholds, per-panel sha/row reconciliation, audited-input hash and the frozen-
hash roll-up) to that fresh recomputation. Only ``computed_utc`` may differ. The
committed artifact's sha256 is pinned to an independent literal so a silent
rewrite of the committed bytes is caught, and a synthetic-drift self-test proves
the pin is a real constraint (a flipped committed verdict, or a flipped
committed per-panel sha flag, must not equal a fresh run).

Read-only: no network, no secrets, no trading endpoints. ``run_audit()`` reads
committed panels only.
"""
import hashlib
import json
import unittest
from pathlib import Path

import scripts.panel_wave_b_quality_audit as qa

ROOT = Path(__file__).resolve().parents[1]
QA_DIR = ROOT / "artifacts" / qa.EXP / "qa"

# Independent literal pin for the committed artifact's bytes. If the committed
# audit is ever rewritten (even with identical-looking fields), this fails.
COMMITTED_ARTIFACT_SHA256 = (
    "140ed6bccbb42c63da5ffe298a287870e57c813da27a409d115ed052415a3d82"
)


def _committed_artifact():
    files = sorted(QA_DIR.glob("panel_wave_b_quality_audit_*.json"))
    assert files, "no committed wave-B quality audit artifact found"
    path = files[-1]
    return path, json.loads(path.read_text(encoding="utf-8"))


class CommittedVerdictPinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path, cls.artifact = _committed_artifact()
        cls.rebuilt = qa.run_audit()

    def test_artifact_identity_and_status(self):
        a = self.artifact
        self.assertEqual(a["audit_id"], qa.AUDIT_ID)
        self.assertEqual(a["experiment_id"], qa.EXPERIMENT_ID)
        self.assertEqual(a["hypothesis"], "H54")
        self.assertEqual(a["status"], "EXPLORATORY_ONLY")
        self.assertFalse(a["confirmatory_claim_allowed"])
        self.assertFalse(a["promotion_allowed"])

    def test_committed_artifact_sha256_pinned(self):
        actual = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.assertEqual(
            actual, COMMITTED_ARTIFACT_SHA256,
            "committed wave-B quality audit bytes changed since the pin was set",
        )

    def test_rebuild_matches_committed_artifact(self):
        rebuilt = dict(self.rebuilt)
        committed = dict(self.artifact)
        rebuilt.pop("computed_utc", None)
        committed.pop("computed_utc", None)
        self.assertEqual(
            rebuilt, committed,
            "fresh run_audit() over the committed panels disagrees with the "
            "committed audit artifact (only computed_utc may differ)",
        )

    def test_load_bearing_fields_pinned(self):
        a = self.artifact
        self.assertEqual(a["verdict"], qa.COMPLETE)
        self.assertEqual(a["scope_problems"], [])
        self.assertEqual(len(a["panels"]), 4)
        self.assertEqual(
            a["cross_panel"],
            {
                "n_days_both_assets": 1139,
                "n_days_single_asset": 217,
                "ark_only_days": 0,
                "astr_only_days": 217,
            },
        )
        self.assertEqual(
            a["thresholds"],
            {
                "panel_end_utc": "2026-10-31",
                "max_allowed_staleness_days": 3,
                "min_klines_completeness": 0.98,
                "allowed_funding_intervals_hours": [1.0, 2.0, 4.0, 8.0],
            },
        )
        self.assertEqual(
            a["audited_input_sha256"],
            {
                "h53_audit_file": (
                    "fc95dfd7ea4fb2c036ac273d89750ac8c7c3331d0ea6100786ab4c7b6735587f"
                )
            },
        )
        for panel in a["panels"]:
            with self.subTest(panel=panel["path"]):
                self.assertTrue(panel["sha256_matches_h53"])
                self.assertTrue(panel["row_count_matches_h53"])
                self.assertEqual(panel["issues"], [])

    def test_frozen_hashes_unchanged(self):
        self.assertTrue(self.artifact["frozen_hashes_verified"]["all_match"])
        for name, row in self.artifact["frozen_hashes_verified"]["details"].items():
            with self.subTest(frozen=name):
                self.assertTrue(row["match"], row)
                self.assertEqual(row["actual"], row["expected"])

    def test_pin_is_a_real_constraint_synthetic_drift(self):
        """A flipped committed verdict / per-panel sha flag must not equal a
        fresh run; otherwise the equality pin above would accept anything."""
        fresh = dict(self.rebuilt)
        fresh.pop("computed_utc", None)

        flipped_verdict = dict(self.artifact)
        flipped_verdict.pop("computed_utc", None)
        flipped_verdict["verdict"] = qa.SCOPE_MISMATCH
        self.assertNotEqual(flipped_verdict, fresh)

        flipped_panel = json.loads(json.dumps(self.artifact))
        flipped_panel.pop("computed_utc", None)
        flipped_panel["panels"][0]["sha256_matches_h53"] = False
        self.assertNotEqual(flipped_panel, fresh)


if __name__ == "__main__":
    unittest.main()