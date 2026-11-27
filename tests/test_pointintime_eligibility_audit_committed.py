"""Committed-disk verdict pin for scripts/pointintime_eligibility_audit.py (H57).

The hermetic seam suite (test_pointintime_eligibility_audit.py) exercises every pure
helper against synthetic fixtures, and its CommittedAuditIntegrationTests only checks
the committed artifact's INTERNAL self-consistency (status, symbol resolution, frozen
hashes, rank provenance, min breadth) -- nothing re-derives the committed artifact's
load-bearing verdict from the REAL committed cap panels and klines inventory. If that
committed artifact drifted, was truncated, or was written against a different data
vintage, no test would catch it -- the same single-source-of-truth hazard the
committed-disk pins for the state-representativeness (DISP-003-STATEAUDIT-001),
maturity-timeline (H35), independent-recomputation (H37), frozen-tree (H38),
expanding-universe (H33), final-integrity and H10-fresh-integrity audits already close.

This module re-runs the SAME read-only audit pipeline (``build_audit``) against the
committed inputs (no file is written; ``build_audit`` never touches disk for output)
and pins the committed artifact's load-bearing fields (label, status, window,
inventory counts, strict/as-of breadth distributions, rank-provenance label, decision,
frozen-hash verdict) to that fresh recomputation. Only ``computed_utc`` is allowed to
differ between the committed artifact and a fresh run. Read-only and stdlib-only; the
audit module derives its path constants from ``__file__`` so the test is CWD-independent.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "pointintime_eligibility_audit.py"
COMMITTED_AUDIT = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-POINTINTIME-ELIG-001"
    / "integrity_audit"
    / "H004V106_pointintime_eligibility_2026-11-22T04-55-46Z.json"
)

spec = importlib.util.spec_from_file_location("pit_elig_committed", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Independent copy of the frozen canonical hash so a coordinated change to a frozen
# artifact still fails even if a module constant were edited.
EXPECTED_CANONICAL = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


class CommittedPointInTimeEligibilityAuditVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        required = [mod.MARKETCAP_PANEL, COMMITTED_AUDIT]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.committed = _load(COMMITTED_AUDIT)
        cls.fresh = mod.build_audit()

    def test_fresh_audit_label_and_status(self):
        res = self.fresh
        self.assertEqual(res["status"], "EXPLORATORY_ONLY")
        self.assertTrue(res["exploratory_only"])
        self.assertFalse(res["confirmatory_claim_allowed"])
        self.assertFalse(res["promotion_allowed"])
        self.assertEqual(res["label"], "POINT_IN_TIME_ELIGIBLE")
        self.assertEqual(
            res["experiment_id"],
            "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-POINTINTIME-ELIG-001",
        )
        self.assertEqual(res["audit_id"], "H004V106_POINTINTIME_ELIG_001")

    def test_committed_artifact_matches_fresh_recomputation(self):
        # The whole artifact must be reproduced from the committed cap panels and
        # klines inventory; only computed_utc (a wall-clock timestamp) may differ.
        c = dict(self.committed)
        f = dict(self.fresh)
        c.pop("computed_utc", None)
        f.pop("computed_utc", None)
        self.assertEqual(
            c, f,
            msg="committed point-in-time eligibility audit drifted from a fresh "
            "recomputation against the committed inputs",
        )

    def test_committed_artifact_pin_values(self):
        c = self.committed
        self.assertEqual(c["label"], "POINT_IN_TIME_ELIGIBLE")
        self.assertEqual(c["window"]["month_first"], "2025-01")
        self.assertEqual(c["window"]["month_last"], "2026-10")
        self.assertEqual(c["window"]["n_months"], 22)
        self.assertEqual(c["inventory"]["n_symbols"], 41)
        self.assertEqual(c["inventory"]["assets_without_cap"], [])
        self.assertEqual(c["inventory"]["snapshot_like_assets"], [])
        self.assertEqual(
            c["inventory"]["partial_klines_assets"],
            ["1INCHUSDT", "AAVEUSDT", "ACHUSDT", "AGLDUSDT", "EOSUSDT", "MATICUSDT"],
        )
        strict = c["summary"]["strict_breadth_stats"]
        asof = c["summary"]["asof_breadth_stats"]
        self.assertEqual(strict["min"], 29.0)
        self.assertEqual(asof["min"], 29.0)
        self.assertEqual(strict["n"], 22)
        self.assertEqual(c["summary"]["n_months_strict_ge_min"], 22)
        self.assertEqual(c["summary"]["n_months_asof_ge_min"], 22)
        self.assertEqual(c["summary"]["min_breadth_required"], 20)
        self.assertEqual(c["rank_provenance"]["label"], "NOT_PROVEN_COMPLETE")
        self.assertIsNone(c["rank_provenance"]["last_verified_historical_rank"])
        self.assertEqual(c["decision"]["label"], "POINT_IN_TIME_ELIGIBLE")
        self.assertTrue(c["all_frozen_hashes_match"])

    def test_frozen_hash_matches_committed_artifact(self):
        # The audit reads the committed canonical block; pin its sha256 to an
        # independent literal so a swapped block is caught even if the committed
        # artifact were regenerated to match it.
        canonical_path, expected = mod.FROZEN_EXPECTED["canonical_forward_block"]
        self.assertEqual(_sha256(canonical_path), EXPECTED_CANONICAL)
        self.assertEqual(expected, EXPECTED_CANONICAL)
        self.assertEqual(
            self.committed["all_frozen_hashes_match"],
            self.fresh["all_frozen_hashes_match"],
        )

    def test_synthetic_drift_is_detected(self):
        # A tampered committed artifact (a flipped label) must not equal a fresh
        # recomputation, so the committed-disk comparison is sensitive to drift.
        tampered = json.loads(json.dumps(self.committed))
        tampered["label"] = (
            "POINT_IN_TIME_LIMITED"
            if self.committed["label"] != "POINT_IN_TIME_LIMITED"
            else "POINT_IN_TIME_ELIGIBLE"
        )
        self.assertNotEqual(tampered["label"], self.fresh["label"])

        # A perturbed cap input (empty legacy cap panel) must move RECOMPUTED fields,
        # proving the pin is a real constraint on the committed cap data and not a
        # rubber stamp. The real panel files are only read, never written.
        original = mod.load_legacy_cap
        try:
            mod.load_legacy_cap = lambda *a, **k: {}
            drifted = mod.build_audit()
        finally:
            mod.load_legacy_cap = original
        self.assertNotEqual(drifted["label"], self.committed["label"])
        self.assertNotEqual(
            drifted["inventory"]["assets_without_cap"],
            self.committed["inventory"]["assets_without_cap"],
        )
        self.assertNotEqual(
            drifted["summary"]["strict_breadth_stats"]["min"],
            self.committed["summary"]["strict_breadth_stats"]["min"],
        )
        # The module must be fully restored after the perturbation.
        self.assertEqual(mod.build_audit()["label"], self.committed["label"])


if __name__ == "__main__":
    unittest.main()