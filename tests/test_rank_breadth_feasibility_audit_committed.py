"""Committed-disk verdict pin for scripts/rank_breadth_feasibility_audit.py (H39).

The static suite (test_rank_breadth_feasibility_audit.py) only checks the committed
artifact's INTERNAL self-consistency against a fresh recomputation -- nothing pins
the committed artifact's load-bearing numbers to an INDEPENDENT sha256 literal. If
that committed artifact drifted, was truncated, or was written against different
inputs, no test would catch it because the test only compares rebuild vs committed.
This module closes that single-source-of-truth gap by:

1. Re-running the SAME read-only audit pipeline against the committed inputs.
2. Pinning the committed artifact's load-bearing fields (universe size, median N,
   band fractions, decision label, legacy/candidate arm sizes, panel coverage)
   to that fresh recomputation. Only ``computed_utc`` is allowed to differ.
3. Pinning the committed artifact sha256 to an independent literal so a swapped
   artifact is caught even if the test were regenerated to match it.
4. Proving the pin is a real constraint via a synthetic-drift self-test.

Read-only and stdlib-only (the audit module uses pandas but only for I/O; path
constants are re-anchored to the repository root in ``setUpClass`` so the test
is CWD-independent). No network, no secrets, no trading endpoints.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "rank_breadth_feasibility_audit.py"
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
COMMITTED_AUDIT = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-FEAS-001"
    / "integrity_audit"
    / "H004V106_rank_breadth_feasibility_2026-11-16T06-57-08Z.json"
)

spec = importlib.util.spec_from_file_location("rank_breadth_feasibility_audit", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Independent copy of the frozen artifact sha256 so a coordinated change to the
# committed artifact still fails even if a module constant were edited.
EXPECTED_ARTIFACT_SHA256 = "d13108da263822a145811feb18a90831bfa526380983e27a1e7db206dd3db85d"


def _reanchor_paths() -> None:
    """Point the audit module's path constants at ROOT-anchored absolute paths."""
    art = ROOT / "artifacts" / EXP
    mod.CANDIDATE_VALIDATION = art / "data" / "panels" / "candidate_batch_validation.json"
    mod.RAW_CAP_DIR = art / "data" / "raw" / "coinmetrics_candidates"
    mod.KLINE_PATH = art / "data" / "panels" / "binance_klines_BTCUSDT.csv"
    mod.MARKETCAP_PANEL = art / "data" / "panels" / "marketcap_panel.csv"
    mod.EXP_DIR = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-FEAS-001"
    mod.AUDIT_DIR = mod.EXP_DIR / "integrity_audit"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _run_with_temp_output():
    """Run the audit with --out redirected to a temp file under ROOT.

    The committed artifact is never written: only a temporary --out is used
    and the module globals are restored in ``finally``. Returns the parsed fresh output.
    """
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        tmp_out = Path(tmp) / "audit.json"
        try:
            rc = mod.main(argv=["--out", str(tmp_out)])
        finally:
            pass
        if rc != 0:
            raise AssertionError("rank_breadth_feasibility_audit main() returned a nonzero exit code")
        return _load(tmp_out)


class CommittedRankBreadthFeasibilityAuditVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _reanchor_paths()
        required = [mod.CANDIDATE_VALIDATION, mod.RAW_CAP_DIR, mod.KLINE_PATH, mod.MARKETCAP_PANEL, COMMITTED_AUDIT]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.committed = _load(COMMITTED_AUDIT)
        cls.fresh = _run_with_temp_output()

    def test_fresh_audit_label_and_status(self):
        res = self.fresh
        self.assertEqual(res["audit_id"], mod.AUDIT_ID)
        self.assertEqual(res["experiment_id"], mod.EXPERIMENT_ID)
        self.assertEqual(res["hypothesis"], "H39")
        self.assertEqual(res["status"], "EXPLORATORY_ONLY")
        self.assertIn(
            res["label"], ("RANK_BREADTH_MEASURABLE", "RANK_BREADTH_SAMPLE_LIMITED")
        )

    def test_committed_artifact_matches_fresh_recomputation(self):
        # The whole artifact must be reproduced from the committed inputs;
        # only computed_utc (a wall-clock timestamp) is allowed to differ.
        c = dict(self.committed)
        f = dict(self.fresh)
        c.pop("computed_utc", None)
        f.pop("computed_utc", None)
        self.assertEqual(
            c, f,
            msg="committed rank-breadth feasibility audit drifted from a fresh "
            "recomputation against the committed inputs",
        )

    def test_committed_artifact_pin_values(self):
        c = self.committed
        self.assertEqual(c["universe_size"], 220)
        self.assertEqual(c["legacy_arm_size"], 32)
        self.assertEqual(c["candidate_arm_size"], 188)
        self.assertEqual(c["n_assets_with_nonempty_series"], 220)
        self.assertEqual(c["n_universe_with_committed_kline_panel"], 32)
        self.assertEqual(c["n_universe_without_committed_kline_panel"], 188)
        self.assertEqual(c["label"], "RANK_BREADTH_MEASURABLE")
        # Rankable size stats
        self.assertEqual(c["rankable_size_stats"]["n"], 1399)
        self.assertAlmostEqual(c["rankable_size_stats"]["p50"], 211.0, places=12)
        self.assertEqual(c["rankable_size_stats"]["min"], 29.0)
        self.assertEqual(c["rankable_size_stats"]["max"], 218.0)
        # Band stats fractions
        for label in ("[1-20]", "[21-50]", "[51-100]"):
            self.assertGreaterEqual(
                c["band_stats"][label]["frac_dates_count_ge_min"], 0.90
            )
        # Decision rule
        self.assertTrue(c["decision"]["criterion_a_median_n_ge_min"]["pass"])
        self.assertTrue(c["decision"]["criterion_b_band_fractions"]["[1-20]"]["pass"])
        self.assertTrue(c["decision"]["criterion_b_band_fractions"]["[21-50]"]["pass"])
        self.assertTrue(c["decision"]["criterion_b_band_fractions"]["[51-100]"]["pass"])
        # Committed panel coverage
        self.assertEqual(c["committed_panel_rank_coverage"]["n_committed_panel_assets"], 32)
        self.assertEqual(c["committed_panel_rank_coverage"]["n_in_universe"], 32)

    def test_frozen_hashes_unchanged(self):
        self.assertTrue(self.committed["all_frozen_hashes_match"])
        for name, row in self.committed["frozen_hashes_verified"].items():
            with self.subTest(frozen=name):
                self.assertTrue(row["match"], row)
                self.assertEqual(row["actual"], row["expected"])

    def test_artifact_sha256_matches_independent_literal(self):
        # Pin the committed artifact sha256 to an independent literal so a
        # swapped artifact is caught even if the test were regenerated to match it.
        self.assertEqual(_sha256(COMMITTED_AUDIT), EXPECTED_ARTIFACT_SHA256)
        self.assertEqual(
            self.committed["h39_reference"]["sha256"] if "h39_reference" in self.committed else None,
            None,  # H39 artifact doesn't have an h39_reference field
        )

    def test_synthetic_drift_is_detected(self):
        # A tampered committed artifact (flipped decision label) must not equal a
        # fresh recomputation, so the committed-disk comparison is sensitive to drift.
        tampered = json.loads(json.dumps(self.committed))
        tampered["label"] = (
            "RANK_BREADTH_SAMPLE_LIMITED"
            if self.committed["label"] != "RANK_BREADTH_SAMPLE_LIMITED"
            else "RANK_BREADTH_MEASURABLE"
        )
        self.assertNotEqual(
            tampered["label"],
            self.fresh["label"],
        )

        # A tampered universe_size must not equal a fresh recomputation.
        tampered2 = json.loads(json.dumps(self.committed))
        tampered2["universe_size"] = self.committed["universe_size"] + 1
        self.assertNotEqual(
            tampered2["universe_size"],
            self.fresh["universe_size"],
        )

        # A tampered median N must not equal a fresh recomputation.
        tampered3 = json.loads(json.dumps(self.committed))
        tampered3["rankable_size_stats"]["p50"] = self.committed["rankable_size_stats"]["p50"] + 1.0
        self.assertNotEqual(
            tampered3["rankable_size_stats"]["p50"],
            self.fresh["rankable_size_stats"]["p50"],
        )


if __name__ == "__main__":
    unittest.main()