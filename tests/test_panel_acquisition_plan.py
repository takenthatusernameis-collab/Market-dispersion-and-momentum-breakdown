"""Regression tests for scripts/panel_acquisition_plan.py (H41).

DISP-003-PANELACQ-PLAN-001, EXPLORATORY_ONLY. Pins:
  * module import-safe (pure helpers);
  * deterministic subset selection and plan-entry construction;
  * decision rule behavior on synthetic inputs;
  * build_audit() reproduces committed artifact (excluding wall-clock computed_utc
    and _output_path) and committed artifact is EXPLORATORY_ONLY with frozen hashes.

Read-only: no network, no secrets, no trading endpoints.
"""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "panel_acquisition_plan.py"
AUDIT_DIR = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001"
    / "integrity_audit"
)

spec = importlib.util.spec_from_file_location("panel_acquisition_plan", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _committed_artifact():
    files = sorted(AUDIT_DIR.glob("H004V106_panel_acquisition_plan_*.json"))
    assert files, "no committed panel-acquisition plan artifact found"
    return files[-1], json.loads(files[-1].read_text(encoding="utf-8"))


class PureHelperTests(unittest.TestCase):
    def _rec(self, asset, obs, cov=0.99, **kw):
        base = {
            "asset": asset,
            "symbol": asset.upper() + "USDT",
            "binance_exists": True,
            "validation_status": "verified",
            "in_candidate_validation": True,
            "cap_obs_in_study_window": obs,
            "cap_coverage_frac": cov,
            "committed_kline_panel": False,
            "committed_funding_panel": False,
            "required_study_months": ["2023-01", "2023-02"],
        }
        base.update(kw)
        return base

    def test_select_subset_deterministic_order(self):
        recs = [
            self._rec("b", 100, 0.9),
            self._rec("a", 100, 0.9),
            self._rec("c", 120, 0.8),
            self._rec("d", 100, 0.95),
        ]
        sel = mod.select_subset(recs, n=3)
        self.assertEqual([r["asset"] for r in sel], ["c", "d", "a"])

    def test_select_subset_filters_ineligible(self):
        recs = [
            self._rec("a", 100),
            self._rec("b", 100, committed_kline_panel=True),
            self._rec("c", 0),
            self._rec("d", 100, validation_status="blocked"),
        ]
        sel = mod.select_subset(recs, n=10)
        self.assertEqual([r["asset"] for r in sel], ["a"])

    def test_plan_entries_bounded_and_unique(self):
        rec = self._rec("alice", 1392)
        rec["symbol"] = "ALICEUSDT"
        rec["required_study_months"] = ["2023-01", "2023-02", "2023-03"]
        entries = mod.plan_entries_for_asset(rec)
        self.assertEqual(len(entries), 6)
        keys = [(e["symbol"], e["kind"], e["month"]) for e in entries]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(all(e["sha256"] is None for e in entries))
        self.assertTrue(all(e["provenance_status"] == "PENDING_ACQUISITION" for e in entries))
        self.assertTrue(all("ALICEUSDT" in e["archive_url"] for e in entries))


class DecisionRuleTests(unittest.TestCase):
    def test_limited_when_subset_short(self):
        frozen = {k: {"match": True} for k in mod.FROZEN_EXPECTED}
        label, checks = mod.decide_label([], 0, frozen)
        self.assertEqual(label, "PANEL_ACQUISITION_PLAN_LIMITED")
        self.assertFalse(checks["subset_size_ok"])

    def test_limited_when_frozen_mismatch(self):
        rec = {
            "asset": "a", "symbol": "AUSDT", "binance_exists": True,
            "validation_status": "verified", "in_candidate_validation": True,
            "cap_obs_in_study_window": 1, "cap_coverage_frac": 1.0,
            "committed_kline_panel": False, "committed_funding_panel": False,
            "required_study_months": ["2023-01"],
        }
        subset = [rec] * 10
        frozen = {k: {"match": True} for k in mod.FROZEN_EXPECTED}
        frozen["canonical_forward_block"] = {"match": False}
        total = sum(len(r["required_study_months"]) * len(mod.SERIES_KINDS) for r in subset)
        label, _ = mod.decide_label(subset, total, frozen)
        self.assertEqual(label, "PANEL_ACQUISITION_PLAN_LIMITED")


class CommittedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path, cls.artifact = _committed_artifact()
        cls.rebuilt = mod.build_audit(out_path=None)

    def test_artifact_identity_and_status(self):
        a = self.artifact
        self.assertEqual(a["audit_id"], mod.AUDIT_ID)
        self.assertEqual(a["experiment_id"], mod.EXPERIMENT_ID)
        self.assertEqual(a["hypothesis"], "H41")
        self.assertEqual(a["status"], "EXPLORATORY_ONLY")
        self.assertEqual(a["label"], "PANEL_ACQUISITION_PLAN_READY")

    def test_rebuild_matches_committed_artifact(self):
        rebuilt = dict(self.rebuilt)
        committed = dict(self.artifact)
        for k in ("computed_utc", "_output_path"):
            rebuilt.pop(k, None)
            committed.pop(k, None)
        self.assertEqual(rebuilt, committed)

    def test_frozen_hashes_unchanged(self):
        self.assertTrue(self.artifact["all_frozen_hashes_match"])
        for name, row in self.artifact["frozen_hashes_verified"].items():
            with self.subTest(frozen=name):
                self.assertTrue(row["match"], row)

    def test_subset_and_plan_counts(self):
        self.assertEqual(self.artifact["subset_selection"]["subset_size"], 10)
        self.assertEqual(
            self.artifact["plan_totals"]["n_planned_entries"],
            self.artifact["plan_totals"]["n_unique_symbol_kind_month"],
        )
        self.assertGreater(self.artifact["plan_totals"]["n_planned_entries"], 0)
        self.assertEqual(len(self.artifact["plan_entries"]), self.artifact["plan_totals"]["n_planned_entries"])

    def test_no_network_or_outcome_claims(self):
        self.assertIn("no_network_fetch_performed", self.artifact["non_claims"])
        self.assertIn("no_outcome_or_inference", self.artifact["non_claims"])
        self.assertTrue(all(e["sha256"] is None for e in self.artifact["plan_entries"]))
        self.assertTrue(all(e["published_verified"] is None for e in self.artifact["plan_entries"]))


if __name__ == "__main__":
    unittest.main()
