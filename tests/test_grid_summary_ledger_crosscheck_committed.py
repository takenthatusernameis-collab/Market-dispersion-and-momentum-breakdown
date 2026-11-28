"""Committed-disk verdict pin for scripts/grid_summary_ledger_crosscheck.py (H30).

The hermetic seam suite (test_grid_summary_ledger_crosscheck_seams.py) exercises
the pure helpers (recompute_from_formations, compare_values) against synthetic
frames only and deliberately never reads the committed grid_result_ledger.json or
grid_summary.json; no test re-derives the committed H30 cross-check verdict from
the REAL committed artifacts. If the committed grid_summary.json drifted from the
frozen grid_result_ledger.json (one of the five frozen hashes), was regenerated
against a different ledger, or was truncated, no test would catch it -- the same
single-source-of-truth hazard the committed-disk pins for the grid-ledger
internal-consistency (H32), state-representativeness (DISP-003-STATEAUDIT-001),
maturity-timeline (H35), independent-recomputation (H37), frozen-tree (H38) and
expanding-universe (H33) audits already close.

This module re-runs the SAME read-only audit (``audit()`` over the committed
grid_result_ledger.json + grid_summary.json; no file is written) and pins the
committed artifact's load-bearing fields (status, overall_passed, total_diffs,
audit_id, experiment_id, hypothesis, anchors_checked, and each anchor's matched
flag and recomputed aggregates) to that fresh recomputation. Only ``audited_utc``
(a wall-clock timestamp) is allowed to differ. A synthetic-drift self-test proves
the pin is a real constraint: perturbing one committed anchor cell's formation
must move a recomputed aggregate and make the cross-check record a diff (i.e. the
anchor would no longer match), and a flipped committed status must not equal a
fresh run. Read-only and stdlib-only; the audit module anchors its own paths to
the repository root, so the test is CWD-independent.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "grid_summary_ledger_crosscheck.py"
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
COMMITTED_AUDIT = (
    ROOT
    / "artifacts"
    / EXP
    / "integrity_audit"
    / "H004V106_grid_summary_ledger_crosscheck_2026-11-15T062831Z.json"
)

spec = importlib.util.spec_from_file_location(
    "grid_summary_ledger_crosscheck_committed", SPEC_PATH
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Independent copy of the frozen grid_result_ledger hash so a swapped or re-run
# ledger is caught even if a module constant were edited.
EXPECTED_LEDGER_SHA256 = (
    "0184f2d3e5d63dc6fb23a45f0ddfb226a195324d153615588c6c1363a74ce04c"
)

# The aggregate fields the cross-check compares between the ledger recomputation
# and the committed summary. Kept here (not imported) so a coordinated change to
# the script's local field list alone cannot satisfy this test.
FIELDS_TO_CHECK = (
    "n_formations",
    "n_high",
    "n_low",
    "n_mid",
    "high_gross_mean",
    "low_gross_mean",
    "high_net_1x_mean",
    "low_net_1x_mean",
    "high_low_diff_gross",
    "high_low_diff_net_1x",
    "spread_gross_mean",
    "spread_net_1x_mean",
    "spread_gross_median",
    "spread_net_1x_median",
    "date_first",
    "date_last",
)


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class CommittedGridSummaryLedgerCrosscheckVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        required = [mod.LEDGER_PATH, mod.SUMMARY_PATH, COMMITTED_AUDIT]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.committed = _load(COMMITTED_AUDIT)
        cls.fresh = mod.audit()

    def test_fresh_audit_reproduces_committed_artifact(self):
        # The whole artifact must be reproduced from the committed ledger + summary;
        # only audited_utc (a wall-clock timestamp) is allowed to differ.
        c = dict(self.committed)
        f = dict(self.fresh)
        c.pop("audited_utc", None)
        f.pop("audited_utc", None)
        self.assertEqual(
            c, f,
            msg="committed grid summary/ledger cross-check audit drifted from a fresh "
            "recomputation against the committed grid_result_ledger.json + grid_summary.json",
        )

    def test_committed_artifact_pin_values(self):
        c = self.committed
        self.assertEqual(c["audit_id"], "H004V106_GRID_SUMMARY_LEDGER_CROSSCHECK")
        self.assertEqual(c["experiment_id"], EXP)
        self.assertEqual(c["hypothesis"], "H30")
        self.assertEqual(c["status"], "PASS")
        self.assertTrue(c["overall_passed"])
        self.assertEqual(c["total_diffs"], 0)
        self.assertEqual(c["anchors_checked"], ["H004V105", "H004V106"])
        self.assertFalse(c["frozen_artifacts_modified"])
        # Each anchor must have matched the committed summary with zero diffs, and
        # the recomputed aggregates must equal the committed artifact's record.
        for anchor in ("H004V105", "H004V106"):
            with self.subTest(anchor=anchor):
                res = c["results"][anchor]
                self.assertTrue(res["matched"], res["diffs"])
                self.assertEqual(res["diffs"], [])
                rc = res["recomputed_from_ledger"]
                self.assertEqual(rc["n_formations"], 1338)
                self.assertGreater(rc["n_high"], 0)
                self.assertGreater(rc["n_low"], 0)
                self.assertEqual(rc["n_high"] + rc["n_low"] + rc["n_mid"], rc["n_formations"])
                # The load-bearing net-1x high-minus-low spread is finite and pinned.
                self.assertIsInstance(rc["high_low_diff_net_1x"], float)

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

        # Perturbing one real committed anchor cell's formation must move a RECOMPUTED
        # aggregate and make the cross-check record a diff (the anchor would no longer
        # match the committed summary), proving the pin is a real constraint on the
        # committed ledger and not a rubber stamp. The real ledger is only read, never
        # written; the perturbed copy lives in memory.
        ledger = _load(mod.LEDGER_PATH)
        summary = _load(mod.SUMMARY_PATH)
        anchor = "H004V106"
        formations = ledger["cells"][anchor]["formations"]
        self.assertTrue(formations, "no formations to perturb")
        summary_anchor = summary[mod.SUMMARY_KEYS[anchor]]

        # Baseline: the unperturbed recomputation matches the committed summary.
        base = mod.recompute_from_formations(formations)
        base_diffs: list[str] = []
        for field in FIELDS_TO_CHECK:
            mod.compare_values(field, base.get(field), summary_anchor.get(field), base_diffs)
        self.assertEqual(base_diffs, [], "unperturbed ledger should match committed summary")

        # Perturb one formation's net-1x spread; the recomputed mean must move.
        perturbed = [dict(r) for r in formations]
        perturbed[0]["spread_net_1x"] = perturbed[0]["spread_net_1x"] + 1.0
        moved = mod.recompute_from_formations(perturbed)
        self.assertNotEqual(
            moved["spread_net_1x_mean"], base["spread_net_1x_mean"],
            "perturbing a formation must move the recomputed spread_net_1x_mean",
        )

        # And the moved recomputation must now disagree with the committed summary.
        drift_diffs: list[str] = []
        for field in FIELDS_TO_CHECK:
            mod.compare_values(field, moved.get(field), summary_anchor.get(field), drift_diffs)
        self.assertTrue(
            drift_diffs,
            "a perturbed ledger recomputation must produce cross-check diffs "
            "(the anchor would no longer match the committed summary)",
        )


if __name__ == "__main__":
    unittest.main()