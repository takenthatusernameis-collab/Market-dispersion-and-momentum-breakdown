"""Committed-disk verdict pin for scripts/audit_f1_grid_execution_state.py (H26).

The hermetic seam suite (test_audit_f1_grid_execution_state.py) exercises every pure
helper (cell_partition, max_date, tail_formation_contrast, drift_summary, sha256_file)
against synthetic fixtures and never calls ``audit()`` or reads a committed artifact.
That leaves the committed F1 execution-state audit
``f1_grid_execution_state_audit_2026-11-14T043410Z.json`` -- the load-bearing record of
WHY the DISP-003-F1GRID-001 grid is blocked (the preregistered fidelity anchor is
unsatisfiable on the current panel vintage, so the run aborts and writes no comparison)
-- backed only by internal self-consistency. If that artifact drifted, was truncated, or
was written against a different checkpoint/ledger vintage, no test would catch it: the
same single-source-of-truth hazard the committed-disk pins for the state-representativeness
(DISP-003-STATEAUDIT-001), point-in-time eligibility (H57), maturity-timeline (H35),
independent-recomputation (H37), frozen-tree (H38), expanding-universe (H33), final-integrity
and H10-fresh-integrity audits already close.

This module re-runs the SAME read-only audit pipeline (``audit()``) against the committed
arm A checkpoint, committed 216-cell ledger, preregistration and frozen blocks (no file is
written; ``audit()`` only reads) and pins the committed artifact's load-bearing fields
(verdict, status, fidelity drift summary, arm A cell partition, committed-ledger counts,
frozen-hash verdict, disposition) to that fresh recomputation. Only ``audited_utc`` (a
wall-clock timestamp) and the panel-dependent ``evidence.panel_vintage`` /
``vintage_mismatch.panel_max_kline_date`` fields are allowed to differ, because the
committed panels are legitimately appended before the 2026-11-30 gate; the pinned verdict
and fidelity fields are derived from the checkpoint and committed ledger, not from the
live panels, so they are stable. Read-only and stdlib-only; the audit module derives its
path constants from ``__file__`` so the test is CWD-independent.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "audit_f1_grid_execution_state.py"
COMMITTED_AUDIT = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-001"
    / "integrity_audit"
    / "f1_grid_execution_state_audit_2026-11-14T043410Z.json"
)

spec = importlib.util.spec_from_file_location("f1_grid_exec_committed", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Independent copy of the frozen canonical hash so a coordinated change to a frozen
# artifact still fails even if a module constant were edited.
EXPECTED_CANONICAL = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"

# Fields that legitimately differ between the committed artifact and a fresh run:
#   - audited_utc: wall-clock timestamp of the run.
#   - evidence.panel_vintage / vintage_mismatch.panel_max_kline_date: derived from the
#     live panels, which are appended before the 2026-11-30 gate. The pinned verdict
#     and fidelity fields do NOT depend on the live panels.
PANEL_DEPENDENT = ("audited_utc", "panel_vintage", "panel_max_kline_date")


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _strip_panel_dependent(report: dict) -> dict:
    """Return a deep copy of ``report`` with the panel-dependent fields removed so the
    committed artifact can be compared to a fresh run on its load-bearing fields only."""
    clone = json.loads(json.dumps(report))
    clone.pop("audited_utc", None)
    clone.get("evidence", {}).pop("panel_vintage", None)
    clone.get("vintage_mismatch", {}).pop("panel_max_kline_date", None)
    return clone


class CommittedF1GridExecutionStateAuditVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        required = [
            COMMITTED_AUDIT,
            mod.ARM_A_CKPT,
            ROOT / "artifacts" / mod.OLD_EXP / "grid_result_ledger.json",
        ]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.committed = _load(COMMITTED_AUDIT)
        cls.fresh = mod.audit()

    def test_fresh_audit_verdict_and_status(self):
        res = self.fresh
        self.assertEqual(res["audit_id"], "F1GRID-001-EXECUTION-STATE")
        self.assertEqual(res["experiment_id"], mod.NEW_EXP)
        self.assertEqual(res["hypothesis"], "H26")
        self.assertEqual(res["verdict"], "BLOCKED_FIDELITY_ANCHOR_UNSATISFIABLE")
        self.assertEqual(res["status"], "BLOCKED_SPECIFICATION_GATE")
        self.assertFalse(res["fidelity"]["fidelity_passed"])
        self.assertEqual(res["fidelity"]["compared_cells"], 216)
        self.assertEqual(res["fidelity"]["drift_count"], 3812)

    def test_committed_artifact_matches_fresh_recomputation(self):
        # The whole artifact must be reproduced from the committed checkpoint, ledger,
        # preregistration and frozen blocks; only the panel-dependent fields and the
        # wall-clock timestamp may differ.
        self.assertEqual(
            _strip_panel_dependent(self.committed),
            _strip_panel_dependent(self.fresh),
            msg="committed F1 grid execution-state audit drifted from a fresh "
            "recomputation against the committed inputs",
        )

    def test_committed_artifact_pin_values(self):
        c = self.committed
        self.assertEqual(c["verdict"], "BLOCKED_FIDELITY_ANCHOR_UNSATISFIABLE")
        self.assertEqual(c["status"], "BLOCKED_SPECIFICATION_GATE")
        self.assertFalse(c["fidelity"]["fidelity_passed"])
        self.assertEqual(c["fidelity"]["drift_count"], 3812)
        self.assertEqual(c["fidelity"]["compared_cells"], 216)
        self.assertEqual(c["fidelity"]["cells_with_different_date_last"], 216)
        self.assertEqual(c["fidelity"]["cells_with_different_n_formations"], 216)
        self.assertEqual(
            c["evidence"]["arm_a_cells"],
            {"cells": 216, "ok": 216, "blocked": 0, "failed": 0},
        )
        self.assertEqual(c["evidence"]["committed_ledger_cells_ok"], 216)
        self.assertEqual(c["evidence"]["committed_ledger_holm_rejected_count"], 0)
        self.assertEqual(c["evidence"]["arm_a_max_date_last"], "2026-10-30")
        self.assertEqual(c["evidence"]["committed_ledger_max_date_last"], "2026-09-29")
        self.assertFalse(c["evidence"]["outputs"]["ledger_present"])
        self.assertFalse(c["evidence"]["outputs"]["summary_present"])
        self.assertFalse(c["disposition"]["frozen_artifacts_modified"])
        self.assertFalse(c["disposition"]["committed_panels_modified"])
        self.assertFalse(c["disposition"]["comparison_written"])
        for rel, entry in c["frozen_artifacts"].items():
            self.assertTrue(
                entry["matches_declared_constant"],
                f"committed audit reports frozen mismatch for {rel}",
            )

    def test_frozen_hash_matches_committed_artifact(self):
        # The audit reads the committed canonical block; pin its sha256 to an
        # independent literal so a swapped block is caught even if the committed
        # artifact were regenerated to match it.
        canonical = ROOT / "artifacts" / mod.OLD_EXP / "forward_block" / "forward_block_evaluation.json"
        self.assertEqual(_sha256(canonical), EXPECTED_CANONICAL)
        self.assertEqual(
            self.committed["frozen_artifacts"]["forward_block/forward_block_evaluation.json"]["sha256"],
            EXPECTED_CANONICAL,
        )
        self.assertEqual(
            self.committed["frozen_artifacts"],
            self.fresh["frozen_artifacts"],
        )

    def test_synthetic_drift_is_detected(self):
        # A tampered committed artifact (a flipped verdict) must not equal a fresh
        # recomputation, so the committed-disk comparison is sensitive to drift.
        tampered = json.loads(json.dumps(self.committed))
        tampered["verdict"] = (
            "PASS_EXECUTION_COMPLETE"
            if self.committed["verdict"] != "PASS_EXECUTION_COMPLETE"
            else "BLOCKED_FIDELITY_ANCHOR_UNSATISFIABLE"
        )
        self.assertNotEqual(
            _strip_panel_dependent(tampered),
            _strip_panel_dependent(self.fresh),
        )

        # A perturbed input (a missing arm A checkpoint) must move RECOMPUTED fields,
        # proving the pin is a real constraint on the committed checkpoint and not a
        # rubber stamp. The real checkpoint is only read, never written.
        original = mod.ARM_A_CKPT
        try:
            mod.ARM_A_CKPT = mod.ROOT / "artifacts" / "__nonexistent_armA__.json"
            drifted = mod.audit()
        finally:
            mod.ARM_A_CKPT = original
        self.assertEqual(drifted["verdict"], "NOT_RUN")
        self.assertNotEqual(drifted["verdict"], self.committed["verdict"])
        self.assertEqual(
            drifted["evidence"]["arm_a_cells"],
            {"cells": 0, "ok": 0, "blocked": 0, "failed": 0},
        )
        # The module must be fully restored after the perturbation.
        self.assertEqual(mod.audit()["verdict"], self.committed["verdict"])


if __name__ == "__main__":
    unittest.main()