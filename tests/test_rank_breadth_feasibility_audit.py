"""Regression tests for scripts/rank_breadth_feasibility_audit.py (H39).

DISP-003-RANKBREADTH-FEAS-001, EXPLORATORY_ONLY. Pins:
  * the module is import-safe (pure helpers import without side effects);
  * the pure helpers (band labelling, rank assignment, percentile, decision rule)
    behave deterministically on synthetic inputs;
  * build_audit() reproduces the committed artifact exactly (apart from the
    wall-clock computed_utc), so the committed evidence cannot silently drift;
  * the committed artifact parses, carries its registered experiment id and
    audit id, is EXPLORATORY_ONLY, and reports all frozen hashes unchanged.

Read-only: no network, no secrets, no trading endpoints. build_audit() reads
committed panels/candidate archive only.
"""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "rank_breadth_feasibility_audit.py"
AUDIT_DIR = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-FEAS-001"
    / "integrity_audit"
)

spec = importlib.util.spec_from_file_location("rank_breadth_feasibility_audit", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _committed_artifact():
    files = sorted(AUDIT_DIR.glob("H004V106_rank_breadth_feasibility_*.json"))
    assert files, "no committed rank-breadth feasibility artifact found"
    return files[-1], json.loads(files[-1].read_text(encoding="utf-8"))


class PureHelperTests(unittest.TestCase):
    def test_band_label_boundaries(self):
        self.assertEqual(mod.band_label(1), "[1-20]")
        self.assertEqual(mod.band_label(20), "[1-20]")
        self.assertEqual(mod.band_label(21), "[21-50]")
        self.assertEqual(mod.band_label(50), "[21-50]")
        self.assertEqual(mod.band_label(51), "[51-100]")
        self.assertEqual(mod.band_label(100), "[51-100]")
        self.assertEqual(mod.band_label(101), "[101-200]")
        self.assertEqual(mod.band_label(200), "[101-200]")
        self.assertEqual(mod.band_label(201), "[201-+]")
        self.assertEqual(mod.band_label(10_000), "[201-+]")

    def test_assign_ranks_tie_break_by_asset_id(self):
        caps = {"b": 10.0, "a": 10.0, "c": 5.0}
        ranked = mod.assign_ranks(caps)
        self.assertEqual([a for a, _, _ in ranked], ["a", "b", "c"])
        self.assertEqual([r for _, _, r in ranked], [1, 2, 3])

    def test_assign_ranks_descending_by_cap(self):
        caps = {"a": 1.0, "b": 30.0, "c": 20.0}
        ranked = mod.assign_ranks(caps)
        self.assertEqual([a for a, _, _ in ranked], ["b", "c", "a"])

    def test_percentile_linear_interpolation(self):
        self.assertAlmostEqual(mod._percentile([1.0, 2.0, 3.0, 4.0], 50), 2.5)
        self.assertEqual(mod._percentile([5.0], 50), 5.0)
        self.assertAlmostEqual(mod._percentile([1.0, 2.0, 3.0, 4.0], 0), 1.0)
        self.assertAlmostEqual(mod._percentile([1.0, 2.0, 3.0, 4.0], 100), 4.0)

    def test_distribution_empty(self):
        d = mod._distribution([])
        self.assertEqual(d["n"], 0)
        self.assertIsNone(d["p50"])

    def _fake_computed(self, median_n, band_fracs):
        return {
            "rankable_size_stats": {"p50": median_n},
            "band_stats": {
                label: {"frac_dates_count_ge_min": frac}
                for label, frac in band_fracs.items()
            },
        }

    def test_decision_measurable(self):
        computed = self._fake_computed(
            180.0, {"[1-20]": 0.99, "[21-50]": 0.99, "[51-100]": 0.99}
        )
        label, _ = mod.decide_label(computed)
        self.assertEqual(label, "RANK_BREADTH_MEASURABLE")

    def test_decision_sample_limited_low_median(self):
        computed = self._fake_computed(
            50.0, {"[1-20]": 1.0, "[21-50]": 1.0, "[51-100]": 1.0}
        )
        label, _ = mod.decide_label(computed)
        self.assertEqual(label, "RANK_BREADTH_SAMPLE_LIMITED")

    def test_decision_sample_limited_band_fraction(self):
        computed = self._fake_computed(
            180.0, {"[1-20]": 1.0, "[21-50]": 1.0, "[51-100]": 0.5}
        )
        label, _ = mod.decide_label(computed)
        self.assertEqual(label, "RANK_BREADTH_SAMPLE_LIMITED")


class CommittedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path, cls.artifact = _committed_artifact()
        cls.rebuilt = mod.build_audit()

    def test_artifact_identity_and_status(self):
        a = self.artifact
        self.assertEqual(a["audit_id"], mod.AUDIT_ID)
        self.assertEqual(a["experiment_id"], mod.EXPERIMENT_ID)
        self.assertEqual(a["hypothesis"], "H39")
        self.assertEqual(a["status"], "EXPLORATORY_ONLY")
        self.assertIn(a["label"], ("RANK_BREADTH_MEASURABLE", "RANK_BREADTH_SAMPLE_LIMITED"))

    def test_rebuild_matches_committed_artifact(self):
        rebuilt = dict(self.rebuilt)
        committed = dict(self.artifact)
        rebuilt.pop("computed_utc", None)
        committed.pop("computed_utc", None)
        self.assertEqual(rebuilt, committed)

    def test_frozen_hashes_unchanged(self):
        self.assertTrue(self.artifact["all_frozen_hashes_match"])
        for name, row in self.artifact["frozen_hashes_verified"].items():
            with self.subTest(frozen=name):
                self.assertTrue(row["match"], row)
                self.assertEqual(row["actual"], row["expected"])

    def test_universe_size_matches_frontier(self):
        # The merged cap universe (legacy 32 + candidate arm) reconciles with the
        # frontier's expanding_universe_assets_with_cap_and_binance = 220.
        frontier = json.loads(
            (ROOT / "research_state" / "universe_frontier.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            self.artifact["universe_size"],
            frontier["expanding_universe_assets_with_cap_and_binance"],
        )
        self.assertEqual(self.artifact["legacy_arm_size"], 32)

    def test_only_legacy_arm_has_committed_price_panels(self):
        self.assertEqual(
            self.artifact["n_universe_with_committed_kline_panel"], 32
        )
        self.assertEqual(
            self.artifact["n_universe_without_committed_kline_panel"],
            self.artifact["universe_size"] - 32,
        )


if __name__ == "__main__":
    unittest.main()