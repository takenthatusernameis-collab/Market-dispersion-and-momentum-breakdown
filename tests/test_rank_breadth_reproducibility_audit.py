"""Regression tests for scripts/rank_breadth_reproducibility_audit.py (H42).

DISP-003-RANKBREADTH-REPRO-001, EXPLORATORY_ONLY. Pins:
  * the module is import-safe (pure helpers import without side effects);
  * pure helpers (rank assignment, percentile, band labelling, distribution
    comparison) behave deterministically on synthetic inputs;
  * the integrity scan flags conflicting duplicate dates, non-finite/
    non-positive values and page-chunked (non-monotonic) file ordering on
    synthetic fixtures;
  * build_audit() independently reproduces the H39 RANK_BREADTH_MEASURABLE
    verdict and reproduces the committed artifact exactly (apart from the
    wall-clock computed_utc), so the committed evidence cannot silently drift;
  * the committed artifact carries its registered experiment id and audit id,
    is EXPLORATORY_ONLY, and reports all frozen hashes unchanged.

Read-only: no network, no secrets, no trading endpoints.
"""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "rank_breadth_reproducibility_audit.py"
AUDIT_DIR = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-REPRO-001"
    / "integrity_audit"
)
H39_ARTIFACT = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-FEAS-001"
    / "integrity_audit"
    / "H004V106_rank_breadth_feasibility_2026-11-16T06-57-08Z.json"
)

spec = importlib.util.spec_from_file_location("rank_breadth_reproducibility_audit", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _committed_artifact():
    files = sorted(AUDIT_DIR.glob("H004V106_rank_breadth_reproducibility_*.json"))
    assert files, "no committed rank-breadth reproducibility artifact found"
    return files[-1], json.loads(files[-1].read_text(encoding="utf-8"))


class PureHelperTests(unittest.TestCase):
    def test_band_label_boundaries(self):
        self.assertEqual(mod.band_label(1), "[1-20]")
        self.assertEqual(mod.band_label(20), "[1-20]")
        self.assertEqual(mod.band_label(21), "[21-50]")
        self.assertEqual(mod.band_label(100), "[51-100]")
        self.assertEqual(mod.band_label(200), "[101-200]")
        self.assertEqual(mod.band_label(201), "[201-+]")

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
        self.assertIsNone(mod._percentile([], 50))

    def test_distribution_empty(self):
        d = mod._distribution([])
        self.assertEqual(d["n"], 0)
        self.assertIsNone(d["p50"])

    def test_dist_close_and_match(self):
        self.assertTrue(mod._dist_close(1.0, 1.0 + 1e-12))
        self.assertFalse(mod._dist_close(1.0, 1.1))
        self.assertTrue(mod._dist_close(None, None))
        self.assertFalse(mod._dist_close(None, 1.0))
        self.assertTrue(mod._dist_close(3, 3))
        m = mod._dist_match(
            {"min": 1.0, "p50": 2.0, "n": 4},
            {"min": 1.0, "p50": 2.0, "n": 4},
        )
        self.assertTrue(m["match"])
        m2 = mod._dist_match({"p50": 2.0}, {"p50": 3.0})
        self.assertFalse(m2["match"])

    def test_groups_to_cap_last_wins_and_skips_nonfinite(self):
        groups = {
            "a": [("2023-01-01", "1.0"), ("2023-01-02", "2.0"), ("2023-01-02", "3.0")],
            "b": [("2023-01-01", "nan"), ("2023-01-02", "4.0")],
            "c": [("2023-01-01", "not-a-number")],
        }
        cap = mod.groups_to_cap(groups)
        self.assertEqual(cap["a"]["2023-01-02"], 3.0)
        self.assertEqual(cap["b"], {"2023-01-02": 4.0})
        self.assertNotIn("c", cap)

    def test_series_integrity_flags_hazards_on_synthetic_fixture(self):
        groups = {
            "clean": [("2023-01-01", "1"), ("2023-01-02", "2"), ("2023-01-03", "3")],
            "chunked": [("2023-01-03", "3"), ("2023-01-01", "1"), ("2023-01-02", "2")],
            "conflict": [("2023-01-01", "1"), ("2023-01-01", "2")],
            "bad": [("2023-01-01", "nan"), ("2023-01-02", "-5"), ("2023-01-03", "0")],
        }
        result = mod.series_integrity(groups, sorted(groups))
        per = result["per_asset"]
        totals = result["totals"]
        self.assertTrue(per["clean"]["strictly_increasing"])
        self.assertEqual(per["clean"]["n_descents"], 0)
        self.assertFalse(per["chunked"]["strictly_increasing"])
        self.assertGreater(per["chunked"]["n_descents"], 0)
        self.assertEqual(per["conflict"]["n_conflicting_dates"], 1)
        self.assertEqual(per["conflict"]["n_duplicate_date_rows"], 1)
        self.assertEqual(per["bad"]["n_nonfinite_or_nonpositive"], 3)
        self.assertEqual(totals["n_conflicting_duplicate_dates"], 1)
        self.assertEqual(totals["n_nonfinite_or_nonpositive_values"], 3)
        self.assertEqual(totals["n_missing_source"], 0)

    def test_series_integrity_missing_source(self):
        result = mod.series_integrity({}, ["ghost"])
        self.assertEqual(result["totals"]["n_missing_source"], 1)
        self.assertFalse(result["per_asset"]["ghost"]["source_present"])

    def test_frozen_hash_status_all_match(self):
        status, all_ok = mod.frozen_hash_status()
        self.assertTrue(all_ok)
        for name, row in status.items():
            with self.subTest(frozen=name):
                self.assertTrue(row["match"], row)
                self.assertEqual(row["actual"], row["expected"])


class CommittedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path, cls.artifact = _committed_artifact()
        cls.rebuilt = mod.build_audit()
        cls.h39 = json.loads(H39_ARTIFACT.read_text(encoding="utf-8"))

    def test_artifact_identity_and_status(self):
        a = self.artifact
        self.assertEqual(a["audit_id"], mod.AUDIT_ID)
        self.assertEqual(a["experiment_id"], mod.EXPERIMENT_ID)
        self.assertEqual(a["hypothesis"], "H42")
        self.assertEqual(a["status"], "EXPLORATORY_ONLY")
        self.assertIn(
            a["label"], ("RANK_BREADTH_REPRODUCED", "RANK_BREADTH_REPRODUCTION_FAILED")
        )

    def test_label_is_reproduced(self):
        self.assertEqual(self.artifact["label"], "RANK_BREADTH_REPRODUCED")
        self.assertTrue(self.artifact["comparison_to_h39"]["all_match"])
        self.assertTrue(all(self.artifact["decision"]["criteria"].values()))

    def test_independent_recomputation_matches_h39(self):
        rebuilt = self.rebuilt
        self.assertEqual(
            rebuilt["universe"]["universe_size"], self.h39["universe_size"]
        )
        self.assertEqual(
            rebuilt["recomputed"]["rankable_size_stats"]["p50"],
            self.h39["rankable_size_stats"]["p50"],
        )
        for label, ref in self.h39["band_stats"].items():
            self.assertAlmostEqual(
                rebuilt["recomputed"]["band_stats"][label]["frac_dates_count_ge_min"],
                ref["frac_dates_count_ge_min"],
                places=12,
            )
        self.assertEqual(
            rebuilt["comparison_to_h39"]["per_asset"]["n_match"],
            rebuilt["comparison_to_h39"]["per_asset"]["n_total"],
        )
        self.assertEqual(rebuilt["comparison_to_h39"]["per_asset"]["n_total"], 32)

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

    def test_integrity_clean_on_committed_inputs(self):
        totals = self.artifact["raw_series_integrity"]["totals"]
        self.assertEqual(totals["n_assets"], 220)
        self.assertEqual(totals["n_missing_source"], 0)
        self.assertEqual(totals["n_conflicting_duplicate_dates"], 0)
        self.assertEqual(totals["n_nonfinite_or_nonpositive_values"], 0)
        # The candidate-arm cap files are page-chunked, so a large share of the
        # union is non-monotonic in file order; the loader must not assume order.
        self.assertGreater(totals["n_assets_not_strictly_increasing"], 0)

    def test_universe_matches_frontier(self):
        frontier = json.loads(
            (ROOT / "research_state" / "universe_frontier.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            self.artifact["universe"]["universe_size"],
            frontier["expanding_universe_assets_with_cap_and_binance"],
        )
        self.assertEqual(self.artifact["universe"]["legacy_arm_size"], 32)

    def test_availability_no_forward_fill(self):
        self.assertFalse(self.artifact["availability"]["forward_fill_used"])


if __name__ == "__main__":
    unittest.main()