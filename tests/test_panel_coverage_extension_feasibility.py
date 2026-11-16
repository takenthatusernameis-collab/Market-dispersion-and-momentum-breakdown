"""Regression tests for scripts/panel_coverage_extension_feasibility.py (H40).

DISP-003-PANELCOV-FEAS-001, EXPLORATORY_ONLY. Pins:
  * module import-safe (pure helpers);
  * decision rule behavior on synthetic aggregates;
  * build_audit() reproduces committed artifact (excluding wall-clock computed_utc)
    and the committed artifact is EXPLORATORY_ONLY with all frozen hashes matching;
  * build_audit(out_path=None) is hermetic -- it writes no artifact.

Read-only: no network, no secrets, no trading endpoints.
"""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "panel_coverage_extension_feasibility.py"
AUDIT_DIR = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-FEAS-001"
    / "integrity_audit"
)

spec = importlib.util.spec_from_file_location("panel_coverage_extension_feasibility", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _committed_artifact():
    files = sorted(AUDIT_DIR.glob("H004V106_panel_coverage_extension_feasibility_*.json"))
    assert files, "no committed panel-coverage feasibility artifact found"
    return files[-1], json.loads(files[-1].read_text(encoding="utf-8"))


class DecisionRuleTests(unittest.TestCase):
    def _agg(self, **overrides):
        base = {
            "n_assets": 188,
            "n_in_candidate_validation": 188,
            "n_binance_exists_true": 188,
            "n_status_verified": 188,
            "n_missing_symbol_mapping": 0,
            "n_with_cap_obs_in_study_window": 188,
            "n_with_committed_raw_kline_dir": 0,
            "n_with_committed_raw_funding_dir": 0,
            "n_with_committed_kline_panel": 0,
            "n_with_committed_funding_panel": 0,
        }
        base.update(overrides)
        return base

    def test_feasible_when_all_conditions_hold(self):
        label, _ = mod.decide_label(self._agg())
        self.assertEqual(label, "PANEL_EXTENSION_FEASIBLE_IN_PRINCIPLE")

    def test_limited_when_validation_missing(self):
        label, _ = mod.decide_label(self._agg(n_status_verified=187))
        self.assertEqual(label, "PANEL_EXTENSION_LIMITED")

    def test_limited_when_cap_missing(self):
        label, _ = mod.decide_label(self._agg(n_with_cap_obs_in_study_window=187))
        self.assertEqual(label, "PANEL_EXTENSION_LIMITED")

    def test_limited_when_gap_already_filled(self):
        label, _ = mod.decide_label(self._agg(n_with_committed_kline_panel=1))
        self.assertEqual(label, "PANEL_EXTENSION_LIMITED")

    def test_limited_when_symbol_missing(self):
        label, _ = mod.decide_label(self._agg(n_missing_symbol_mapping=1))
        self.assertEqual(label, "PANEL_EXTENSION_LIMITED")


class CommittedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path, cls.artifact = _committed_artifact()
        cls.rebuilt = mod.build_audit(out_path=None)

    def test_artifact_identity_and_status(self):
        a = self.artifact
        self.assertEqual(a["audit_id"], mod.AUDIT_ID)
        self.assertEqual(a["experiment_id"], mod.EXPERIMENT_ID)
        self.assertEqual(a["hypothesis"], "H40")
        self.assertEqual(a["status"], "EXPLORATORY_ONLY")
        self.assertEqual(a["label"], "PANEL_EXTENSION_FEASIBLE_IN_PRINCIPLE")

    def test_rebuild_matches_committed_artifact(self):
        rebuilt = dict(self.rebuilt)
        committed = dict(self.artifact)
        # exclude wall-clock and transient output path
        for k in ("computed_utc", "_output_path"):
            rebuilt.pop(k, None)
            committed.pop(k, None)
        self.assertEqual(rebuilt, committed)

    def test_frozen_hashes_unchanged(self):
        self.assertTrue(self.artifact["all_frozen_hashes_match"])
        for name, row in self.artifact["frozen_hashes_verified"].items():
            with self.subTest(frozen=name):
                self.assertTrue(row["match"], row)

    def test_aggregate_scope(self):
        agg = self.artifact["aggregate"]
        self.assertEqual(agg["n_assets"], 188)
        self.assertEqual(agg["n_in_candidate_validation"], 188)
        self.assertEqual(agg["n_binance_exists_true"], 188)
        self.assertEqual(agg["n_with_cap_obs_in_study_window"], 188)
        self.assertEqual(agg["n_with_committed_kline_panel"], 0)
        self.assertEqual(agg["n_study_months"], 46)

    def test_h39_input_consistency(self):
        h39 = json.loads(
            (ROOT / "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-FEAS-001/"
             "integrity_audit/H004V106_rank_breadth_feasibility_2026-11-16T06-57-08Z.json").read_text()
        )
        self.assertEqual(
            sorted(h39["universe_assets_without_committed_kline_panel"]),
            sorted(r["asset"] for r in self.artifact["per_asset"]),
        )


class HermeticBuildTests(unittest.TestCase):
    """build_audit(out_path=None) must be a pure read -- no artifact write.

    Regression guard: the test suite previously called build_audit(out_path=None)
    while the function still wrote a fresh timestamped artifact into the tracked
    artifacts/ tree, so every ``unittest discover`` run dirtied the working tree
    and checkpoint commits accumulated duplicate PANELCOV-FEAS-001 artifacts.
    """

    def test_none_out_path_writes_nothing(self):
        before = set(p.name for p in AUDIT_DIR.glob("H004V106_panel_coverage_extension_feasibility_*.json"))
        rebuilt = mod.build_audit(out_path=None)
        after = set(p.name for p in AUDIT_DIR.glob("H004V106_panel_coverage_extension_feasibility_*.json"))
        self.assertEqual(after, before, "build_audit(out_path=None) must not write an artifact")
        self.assertNotIn("_output_path", rebuilt)


if __name__ == "__main__":
    unittest.main()
