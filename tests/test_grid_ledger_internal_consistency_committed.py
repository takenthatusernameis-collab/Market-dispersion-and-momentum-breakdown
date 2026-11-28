"""Committed-disk verdict pin for scripts/grid_ledger_internal_consistency.py (H32).

The hermetic seam suite (test_grid_ledger_internal_consistency_seams.py) exercises the
per-cell accounting / aggregate recomputation (implied_costs, recompute_aggregates,
_num_eq, check_cell, check_ledger) against synthetic ledgers only and deliberately
never reads the committed 71 MB grid_result_ledger.json; no test re-derives the
committed internal-consistency verdict from the REAL committed ledger. If that committed
artifact drifted, was truncated, or was written against a different ledger, no test would
catch it -- the same single-source-of-truth hazard the committed-disk pins for the
state-representativeness (DISP-003-STATEAUDIT-001), maturity-timeline (H35),
independent-recomputation (H37), frozen-tree (H38) and expanding-universe (H33) audits
already close.

This module re-runs the SAME read-only audit (``audit()`` -> ``check_ledger`` over the
committed grid_result_ledger.json; no file is written) and pins the committed artifact's
load-bearing fields (status, n_cells_checked, cells_with_violations, total_violations,
global_violations, status_counts, holm_rejected_true, overall_passed) to that fresh
recomputation. Only ``generated_utc`` (a wall-clock timestamp) is allowed to differ. A
synthetic-drift self-test proves the pin is a real constraint: perturbing one committed
cell's formation must make ``check_ledger`` fail, and a flipped committed status must not
equal a fresh run. Read-only and stdlib-only; the audit module anchors its own paths to
the repository root, so the test is CWD-independent.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "grid_ledger_internal_consistency.py"
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
COMMITTED_AUDIT = (
    ROOT
    / "artifacts"
    / EXP
    / "integrity_audit"
    / "H004V106_grid_ledger_internal_consistency_2026-11-15T084959Z.json"
)

spec = importlib.util.spec_from_file_location("grid_ledger_internal_consistency_committed", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Independent copy of the frozen grid_result_ledger hash so a coordinated change to the
# committed ledger still fails even if a module constant were edited.
EXPECTED_LEDGER_SHA256 = (
    "0184f2d3e5d63dc6fb23a45f0ddfb226a195324d153615588c6c1363a74ce04c"
)


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class CommittedGridLedgerInternalConsistencyVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        required = [mod.LEDGER_PATH, COMMITTED_AUDIT]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.committed = _load(COMMITTED_AUDIT)
        cls.fresh = mod.audit()

    def test_fresh_audit_reproduces_committed_artifact(self):
        # The whole artifact must be reproduced from the committed ledger; only
        # generated_utc (a wall-clock timestamp) is allowed to differ.
        c = dict(self.committed)
        f = dict(self.fresh)
        c.pop("generated_utc", None)
        f.pop("generated_utc", None)
        self.assertEqual(
            c, f,
            msg="committed grid-ledger internal-consistency audit drifted from a fresh "
            "recomputation against the committed grid_result_ledger.json",
        )

    def test_committed_artifact_pin_values(self):
        c = self.committed
        self.assertEqual(c["audit_id"], "H004V106_GRID_LEDGER_INTERNAL_CONSISTENCY")
        self.assertEqual(c["experiment_id"], EXP)
        self.assertEqual(c["hypothesis"], "H32")
        self.assertEqual(c["status"], "PASS")
        self.assertEqual(c["n_cells_checked"], 216)
        self.assertEqual(c["cells_with_violations"], 0)
        self.assertEqual(c["total_violations"], 0)
        self.assertEqual(c["global_violations"], [])
        self.assertEqual(c["cell_violations"], [])
        self.assertEqual(
            c["status_counts"],
            {"OK": 216, "BLOCKED": 0, "INVALID": 0, "FAILED": 0, "NOT_RUN": 0},
        )
        self.assertEqual(c["holm_rejected_true"], 0)
        self.assertTrue(c["overall_passed"])
        self.assertFalse(c["frozen_artifacts_modified"])

    def test_ledger_hash_matches_independent_literal(self):
        # Pin the committed ledger's sha256 to an independent literal so a swapped or
        # re-run ledger is caught even if the committed artifact were regenerated.
        self.assertEqual(_sha256(mod.LEDGER_PATH), EXPECTED_LEDGER_SHA256)

    def test_synthetic_drift_is_detected(self):
        # A tampered committed artifact (a flipped status) must not equal a fresh run,
        # so the committed-disk comparison is sensitive to drift.
        tampered = json.loads(json.dumps(self.committed))
        tampered["status"] = "FAIL" if self.committed["status"] != "FAIL" else "PASS"
        self.assertNotEqual(tampered["status"], self.fresh["status"])

        # Perturbing one real committed cell's formation must move a RECOMPUTED field
        # and make check_ledger fail, proving the pin is a real constraint on the
        # committed ledger and not a rubber stamp. The real ledger is only read, never
        # written; the perturbed copy lives in memory.
        ledger = _load(mod.LEDGER_PATH)
        cells = ledger["cells"]
        target_id = None
        for cid in sorted(cells):
            if cells[cid].get("formations"):
                target_id = cid
                break
        self.assertIsNotNone(target_id, "no cell with formations to perturb")
        cells[target_id]["formations"][0]["spread_net_1x"] = (
            cells[target_id]["formations"][0]["spread_net_1x"] + 1.0
        )
        drifted = mod.check_ledger(ledger)
        self.assertFalse(drifted["passed"])
        self.assertTrue(drifted["cell_violations"])
        self.assertIn(
            target_id, {v["config_id"] for v in drifted["cell_violations"]}
        )


if __name__ == "__main__":
    unittest.main()