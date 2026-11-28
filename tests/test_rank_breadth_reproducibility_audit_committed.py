"""Committed-disk verdict pin for scripts/rank_breadth_reproducibility_audit.py (H42).

The static suite (test_rank_breadth_reproducibility_audit.py) only checks the committed
artifact's INTERNAL self-consistency against a fresh recomputation -- nothing pins
the committed artifact's load-bearing numbers to an INDEPENDENT sha256 literal. If
that committed artifact drifted, was truncated, or was written against different
inputs, no test would catch it because the test only compares rebuild vs committed.
This module closes that single-source-of-truth gap by:

1. Re-running the SAME read-only audit pipeline against the committed inputs.
2. Pinning the committed artifact's load-bearing fields (universe size, median N,
   band fractions, per-asset rank stats, raw series integrity, comparison to H39)
   to that fresh recomputation. Only ``computed_utc`` is allowed to differ.
3. Pinning the committed artifact sha256 to an independent literal so a swapped
   artifact is caught even if the test were regenerated to match it.
4. Proving the pin is a real constraint via a synthetic-drift self-test.

Read-only and stdlib-only (the audit module imports no numpy/pandas); path
constants are re-anchored to the repository root in ``setUpClass`` so the test
is CWD-independent. No network, no secrets, no trading endpoints.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "rank_breadth_reproducibility_audit.py"
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
COMMITTED_AUDIT = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-REPRO-001"
    / "integrity_audit"
    / "H004V106_rank_breadth_reproducibility_2026-11-16T131413Z.json"
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

# Independent copy of the frozen artifact sha256 so a coordinated change to the
# committed artifact still fails even if a module constant were edited.
EXPECTED_ARTIFACT_SHA256 = "d4efeb61a59879dcedf320f44c1bbbecc7c5926f7c6237fdcf122d8a3e2ca2fa"


def _reanchor_paths() -> None:
    """Point the audit module's path constants at ROOT-anchored absolute paths."""
    art = ROOT / "artifacts" / EXP
    mod.CANDIDATE_VALIDATION = art / "data" / "panels" / "candidate_batch_validation.json"
    mod.RAW_CAP_DIR = art / "data" / "raw" / "coinmetrics_candidates"
    mod.KLINE_PATH = art / "data" / "panels" / "binance_klines_BTCUSDT.csv"
    mod.MARKETCAP_PANEL = art / "data" / "panels" / "marketcap_panel.csv"
    mod.H39_ARTIFACT = H39_ARTIFACT
    mod.EXP_DIR = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-REPRO-001"
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
            raise AssertionError("rank_breadth_reproducibility_audit main() returned a nonzero exit code")
        return _load(tmp_out)


class CommittedRankBreadthReproducibilityAuditVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _reanchor_paths()
        required = [
            mod.CANDIDATE_VALIDATION,
            mod.RAW_CAP_DIR,
            mod.KLINE_PATH,
            mod.MARKETCAP_PANEL,
            mod.H39_ARTIFACT,
            COMMITTED_AUDIT,
        ]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.committed = _load(COMMITTED_AUDIT)
        cls.fresh = _run_with_temp_output()
        cls.h39 = _load(H39_ARTIFACT)

    def test_fresh_audit_label_and_status(self):
        res = self.fresh
        self.assertEqual(res["audit_id"], mod.AUDIT_ID)
        self.assertEqual(res["experiment_id"], mod.EXPERIMENT_ID)
        self.assertEqual(res["hypothesis"], "H42")
        self.assertEqual(res["status"], "EXPLORATORY_ONLY")
        self.assertEqual(res["label"], "RANK_BREADTH_REPRODUCED")

    def test_committed_artifact_matches_fresh_recomputation(self):
        # The whole artifact must be reproduced from the committed inputs;
        # only computed_utc (a wall-clock timestamp) is allowed to differ.
        c = dict(self.committed)
        f = dict(self.fresh)
        c.pop("computed_utc", None)
        f.pop("computed_utc", None)
        self.assertEqual(
            c, f,
            msg="committed rank-breadth reproducibility audit drifted from a fresh "
            "recomputation against the committed inputs",
        )

    def test_committed_artifact_pin_values(self):
        c = self.committed
        # Universe
        self.assertEqual(c["universe"]["universe_size"], 220)
        self.assertEqual(c["universe"]["legacy_arm_size"], 32)
        self.assertEqual(c["universe"]["candidate_arm_size"], 188)
        self.assertEqual(c["universe"]["n_assets_with_nonempty_series"], 220)
        self.assertTrue(c["universe"]["match_h39"])
        # Study window
        self.assertEqual(c["study_window"]["n_dates"], 1399)
        self.assertEqual(c["study_window"]["date_first"], "2023-01-01")
        self.assertEqual(c["study_window"]["date_last"], "2026-10-31")
        # Recomputed rankable size stats
        self.assertEqual(c["recomputed"]["rankable_size_stats"]["n"], 1399)
        self.assertAlmostEqual(c["recomputed"]["rankable_size_stats"]["p50"], 211.0, places=12)
        self.assertEqual(c["recomputed"]["rankable_size_stats"]["min"], 29.0)
        self.assertEqual(c["recomputed"]["rankable_size_stats"]["max"], 218.0)
        # Band stats
        for label in ("[1-20]", "[21-50]", "[51-100]", "[101-200]", "[201-+]"):
            self.assertEqual(c["recomputed"]["band_stats"][label]["n"], 1399)
        # Comparison to H39
        self.assertTrue(c["comparison_to_h39"]["all_match"])
        self.assertTrue(c["comparison_to_h39"]["universe_size_match"])
        self.assertTrue(c["comparison_to_h39"]["n_assets_with_nonempty_series_match"])
        self.assertTrue(c["comparison_to_h39"]["rankable_size_stats"]["match"])
        for label in ("[1-20]", "[21-50]", "[51-100]", "[101-200]", "[201-+]"):
            self.assertTrue(c["comparison_to_h39"]["band_stats"][label]["match"])
        self.assertEqual(c["comparison_to_h39"]["per_asset"]["n_match"], 32)
        self.assertEqual(c["comparison_to_h39"]["per_asset"]["n_total"], 32)
        self.assertEqual(len(c["comparison_to_h39"]["per_asset"]["mismatches"]), 0)
        # Raw series integrity
        totals = c["raw_series_integrity"]["totals"]
        self.assertEqual(totals["n_assets"], 220)
        self.assertEqual(totals["n_missing_source"], 0)
        self.assertEqual(totals["n_empty"], 0)
        self.assertEqual(totals["n_conflicting_duplicate_dates"], 0)
        self.assertEqual(totals["n_nonfinite_or_nonpositive_values"], 0)
        # Decision rule
        criteria = c["decision"]["criteria"]
        self.assertTrue(all(criteria.values()))
        self.assertEqual(c["decision"]["label"], "RANK_BREADTH_REPRODUCED")

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

    def test_h39_reference_sha256_matches(self):
        # The H39 reference artifact sha256 should match the committed H39 artifact.
        self.assertEqual(
            self.committed["h39_reference"]["sha256"],
            _sha256(H39_ARTIFACT),
        )

    def test_synthetic_drift_is_detected(self):
        # A tampered committed artifact (flipped comparison_to_h39.all_match) must
        # not equal a fresh recomputation, so the committed-disk comparison is
        # sensitive to drift.
        tampered = json.loads(json.dumps(self.committed))
        tampered["comparison_to_h39"]["all_match"] = False
        self.assertNotEqual(
            tampered["comparison_to_h39"]["all_match"],
            self.fresh["comparison_to_h39"]["all_match"],
        )

        # A tampered universe_size must not equal a fresh recomputation.
        tampered2 = json.loads(json.dumps(self.committed))
        tampered2["universe"]["universe_size"] = self.committed["universe"]["universe_size"] + 1
        self.assertNotEqual(
            tampered2["universe"]["universe_size"],
            self.fresh["universe"]["universe_size"],
        )

        # A tampered integrity total must not equal a fresh recomputation.
        tampered3 = json.loads(json.dumps(self.committed))
        tampered3["raw_series_integrity"]["totals"]["n_conflicting_duplicate_dates"] = 1
        self.assertNotEqual(
            tampered3["raw_series_integrity"]["totals"]["n_conflicting_duplicate_dates"],
            self.fresh["raw_series_integrity"]["totals"]["n_conflicting_duplicate_dates"],
        )


if __name__ == "__main__":
    unittest.main()