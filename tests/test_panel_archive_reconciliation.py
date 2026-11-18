"""Regression tests for scripts/panel_archive_reconciliation.py (H46).

DISP-003-PANELACQ-RECON-001, EXPLORATORY_ONLY. Pins:
  * module import-safe (pure helpers, no network at import);
  * join key construction and window classification on synthetic entries;
  * reconcile() verdict rule (FULLY_BENIGN / HAS_GAPS / JOIN_MISMATCH);
  * the committed artifact's identity, status, join check, absent summary and
    per-asset reconciliation against the committed H41 plan + H43 probe.

Read-only, stdlib-only: no network, no secrets, no trading endpoints. The
committed H41 plan and H43 probe are read to confirm the offline-deterministic
join and classification reproduce the committed artifact.
"""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "panel_archive_reconciliation.py"
RECON_DIR = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-RECON-001"
    / "integrity_audit"
)
H41_PLAN = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001"
    / "integrity_audit"
    / "H004V106_panel_acquisition_plan_20261116T085222Z.json"
)
H43_PROBE = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PROBE-001"
    / "integrity_audit"
    / "H004V106_panel_archive_probe_20261116T142247Z.json"
)

spec = importlib.util.spec_from_file_location(
    "panel_archive_reconciliation", SPEC_PATH
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _committed_artifact():
    files = sorted(RECON_DIR.glob("panel_archive_reconciliation_*.json"))
    assert files, "no committed reconciliation artifact found"
    return files[-1], json.loads(files[-1].read_text(encoding="utf-8"))


def _plan_entry(symbol, kind, month, asset):
    return {
        "symbol": symbol,
        "kind": kind,
        "month": month,
        "asset": asset,
        "provenance_status": "PENDING_ACQUISITION",
        "published_verified": None,
    }


def _probe_entry(symbol, kind, month, asset, status):
    return {
        "symbol": symbol,
        "kind": kind,
        "month": month,
        "asset": asset,
        "http_status": status,
        "error": None,
    }


class HelperTests(unittest.TestCase):
    def test_entry_key(self):
        e = {"symbol": "ARKUSDT", "kind": "klines", "month": "2023-01", "asset": "ark"}
        self.assertEqual(mod.entry_key(e), ("ARKUSDT", "klines", "2023-01"))

    def test_classify_before_first_served(self):
        self.assertEqual(
            mod.classify_absent_month("2023-01", "2023-09", "2026-10"),
            mod.BEFORE_FIRST_SERVED,
        )

    def test_classify_after_last_served(self):
        self.assertEqual(
            mod.classify_absent_month("2026-10", "2023-01", "2025-09"),
            mod.AFTER_LAST_SERVED,
        )

    def test_classify_interior(self):
        self.assertEqual(
            mod.classify_absent_month("2024-06", "2023-01", "2026-10"),
            mod.INTERIOR,
        )

    def test_classify_entirely_absent(self):
        self.assertEqual(
            mod.classify_absent_month("2024-06", None, None),
            mod.ENTIRELY_ABSENT,
        )

    def test_classify_boundaries_are_served_not_absent(self):
        # first_served and last_served months are served, so an absent month at
        # exactly those values cannot occur; interior test uses strict bounds.
        self.assertEqual(
            mod.classify_absent_month("2023-01", "2023-09", "2026-10"),
            mod.BEFORE_FIRST_SERVED,
        )


class ReconcileTests(unittest.TestCase):
    def test_join_mismatch_verdict(self):
        plan = [
            _plan_entry("AAAUSDT", "klines", "2023-01", "aaa"),
            _plan_entry("AAAUSDT", "funding", "2023-01", "aaa"),
        ]
        probe = [
            _probe_entry("AAAUSDT", "klines", "2023-01", "aaa", 200),
            # missing the funding entry -> probe-only / plan-only mismatch
        ]
        result = mod.reconcile(plan, probe)
        self.assertEqual(result["verdict"], mod.VERDICT_JOIN_MISMATCH)
        self.assertFalse(result["join_check"]["ok"])
        self.assertEqual(result["join_check"]["n_plan_only"], 1)

    def test_fully_benign_when_all_absent_pre_listing(self):
        plan = [
            _plan_entry("ARKUSDT", "klines", "2023-01", "ark"),
            _plan_entry("ARKUSDT", "klines", "2023-02", "ark"),
            _plan_entry("ARKUSDT", "klines", "2023-03", "ark"),
        ]
        probe = [
            _probe_entry("ARKUSDT", "klines", "2023-01", "ark", 404),
            _probe_entry("ARKUSDT", "klines", "2023-02", "ark", 404),
            _probe_entry("ARKUSDT", "klines", "2023-03", "ark", 200),
        ]
        result = mod.reconcile(plan, probe)
        self.assertEqual(result["verdict"], mod.VERDICT_FULLY_BENIGN)
        self.assertEqual(result["absent_summary"], {mod.BEFORE_FIRST_SERVED: 2})

    def test_has_gaps_when_trailing_absent(self):
        plan = [
            _plan_entry("ALPHAUSDT", "funding", "2025-08", "alpha"),
            _plan_entry("ALPHAUSDT", "funding", "2025-09", "alpha"),
            _plan_entry("ALPHAUSDT", "funding", "2025-10", "alpha"),
            _plan_entry("ALPHAUSDT", "funding", "2025-11", "alpha"),
        ]
        probe = [
            _probe_entry("ALPHAUSDT", "funding", "2025-08", "alpha", 200),
            _probe_entry("ALPHAUSDT", "funding", "2025-09", "alpha", 200),
            _probe_entry("ALPHAUSDT", "funding", "2025-10", "alpha", 404),
            _probe_entry("ALPHAUSDT", "funding", "2025-11", "alpha", 404),
        ]
        result = mod.reconcile(plan, probe)
        self.assertEqual(result["verdict"], mod.VERDICT_HAS_GAPS)
        self.assertEqual(result["absent_summary"], {mod.AFTER_LAST_SERVED: 2})

    def test_has_gaps_when_interior_absent(self):
        plan = [
            _plan_entry("XXXUSDT", "klines", m, "xxx")
            for m in ("2023-01", "2023-02", "2023-03", "2023-04")
        ]
        probe = [
            _probe_entry("XXXUSDT", "klines", "2023-01", "xxx", 200),
            _probe_entry("XXXUSDT", "klines", "2023-02", "xxx", 404),
            _probe_entry("XXXUSDT", "klines", "2023-03", "xxx", 200),
            _probe_entry("XXXUSDT", "klines", "2023-04", "xxx", 200),
        ]
        result = mod.reconcile(plan, probe)
        self.assertEqual(result["verdict"], mod.VERDICT_HAS_GAPS)
        self.assertEqual(result["absent_summary"], {mod.INTERIOR: 1})

    def test_has_gaps_when_entirely_absent(self):
        plan = [
            _plan_entry("NEWUSDT", "klines", "2023-01", "new"),
            _plan_entry("NEWUSDT", "klines", "2023-02", "new"),
        ]
        probe = [
            _probe_entry("NEWUSDT", "klines", "2023-01", "new", 404),
            _probe_entry("NEWUSDT", "klines", "2023-02", "new", 404),
        ]
        result = mod.reconcile(plan, probe)
        self.assertEqual(result["verdict"], mod.VERDICT_HAS_GAPS)
        self.assertEqual(result["absent_summary"], {mod.ENTIRELY_ABSENT: 2})

    def test_error_entry_not_counted_as_clean_gap(self):
        plan = [
            _plan_entry("ERRUSDT", "klines", "2023-01", "err"),
            _plan_entry("ERRUSDT", "klines", "2023-02", "err"),
        ]
        probe = [
            _probe_entry("ERRUSDT", "klines", "2023-01", "err", None),
            _probe_entry("ERRUSDT", "klines", "2023-02", "err", 200),
        ]
        probe[0]["error"] = "timeout"
        result = mod.reconcile(plan, probe)
        # An errored probe is recorded but is not a clean coverage-gap label.
        self.assertNotIn(mod.AFTER_LAST_SERVED, result["absent_summary"])
        self.assertNotIn(mod.BEFORE_FIRST_SERVED, result["absent_summary"])
        self.assertNotIn(mod.INTERIOR, result["absent_summary"])


class CommittedArtifactTests(unittest.TestCase):
    def test_committed_artifact_identity(self):
        _, audit = _committed_artifact()
        self.assertEqual(audit["experiment_id"], mod.EXPERIMENT_ID)
        self.assertEqual(audit["audit_id"], mod.AUDIT_ID)
        self.assertEqual(audit["hypothesis"], "H46")
        self.assertTrue(audit["exploratory_only"])
        self.assertFalse(audit["promotion_allowed"])

    def test_committed_join_is_clean(self):
        _, audit = _committed_artifact()
        jc = audit["join_check"]
        self.assertTrue(jc["ok"])
        self.assertEqual(jc["n_plan_entries"], 920)
        self.assertEqual(jc["n_probe_entries"], 920)
        self.assertEqual(jc["n_plan_only"], 0)
        self.assertEqual(jc["n_probe_only"], 0)

    def test_committed_absent_total_and_split(self):
        _, audit = _committed_artifact()
        self.assertEqual(audit["n_absent_total"], 31)
        # 18 pre-listing + 13 trailing.
        self.assertEqual(
            audit["absent_summary"],
            {mod.BEFORE_FIRST_SERVED: 18, mod.AFTER_LAST_SERVED: 13},
        )

    def test_committed_verdict_has_gaps(self):
        _, audit = _committed_artifact()
        self.assertEqual(audit["verdict"], mod.VERDICT_HAS_GAPS)

    def test_committed_reproduces_from_plan_and_probe(self):
        """Re-running reconcile() over the committed plan+probe reproduces the
        committed absent set and verdict (offline-deterministic)."""
        _, audit = _committed_artifact()
        plan = json.loads(H41_PLAN.read_text(encoding="utf-8"))
        probe = json.loads(H43_PROBE.read_text(encoding="utf-8"))
        result = mod.reconcile(plan["plan_entries"], probe["per_entry"])
        self.assertEqual(result["verdict"], audit["verdict"])
        self.assertEqual(result["n_absent_total"], audit["n_absent_total"])
        self.assertEqual(result["absent_summary"], audit["absent_summary"])

    def test_committed_gap_assets_are_alpha_ark_astr(self):
        _, audit = _committed_artifact()
        gap_assets = {
            a for a, pa in audit["per_asset"].items() if pa["n_absent"] > 0
        }
        self.assertEqual(gap_assets, {"alpha", "ark", "astr"})
        # ARK + ASTR are benign pre-listing; ALPHA funding is the genuine gap.
        self.assertEqual(
            audit["per_asset"]["ark"]["absent_class_counts"],
            {mod.BEFORE_FIRST_SERVED: 16},
        )
        self.assertEqual(
            audit["per_asset"]["astr"]["absent_class_counts"],
            {mod.BEFORE_FIRST_SERVED: 2},
        )
        self.assertEqual(
            audit["per_asset"]["alpha"]["absent_class_counts"],
            {mod.AFTER_LAST_SERVED: 13},
        )

    def test_committed_alpha_klines_complete_funding_truncated(self):
        _, audit = _committed_artifact()
        alpha = audit["per_asset"]["alpha"]["kinds"]
        self.assertEqual(alpha["klines"]["n_absent"], 0)
        self.assertEqual(alpha["klines"]["first_served"], "2023-01")
        self.assertEqual(alpha["klines"]["last_served"], "2026-10")
        self.assertEqual(alpha["funding"]["n_absent"], 13)
        self.assertEqual(alpha["funding"]["last_served"], "2025-09")


if __name__ == "__main__":
    unittest.main()