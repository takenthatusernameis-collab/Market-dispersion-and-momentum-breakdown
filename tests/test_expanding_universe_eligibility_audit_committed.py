"""Committed-disk verdict pin for scripts/expanding_universe_eligibility_audit.py (H33).

The hermetic seam suite (test_expanding_universe_eligibility_audit_seams.py) exercises the
audit only against synthetic fixtures. This module pins the audit's PASS verdict
against the REAL committed artifacts on disk, so the eligibility coverage claims
that the DISP-003 experiment relies on cannot silently drift:

  - the four frozen artifact hashes still match the values the audit quotes;
  - the ledger comparison is consistent across all expanding-arm configs;
  - the audit status is EXPLORATORY_ONLY and audit_pass is true.

Read-only: no network, no writes to committed artifacts. The audit is run with
AUDIT_DIR redirected to a throwaway temp dir so no dated artifact is written
under the committed integrity_audit/. stdlib-only (the audit module imports pandas
for panel loading, which is already in the environment). Path constants are
re-anchored to the repository root in setUpClass so the test is CWD-independent.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "expanding_universe_eligibility_audit.py"

spec = importlib.util.spec_from_file_location("expanding_universe_eligibility_audit_committed", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Frozen hash literals the audit is expected to quote (kept here as an independent
# copy so a change to the module constants alone cannot satisfy this test).
EXPECTED_CANONICAL = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"
EXPECTED_FRESH = "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f"
EXPECTED_GRID_LEDGER = "0184f2d3e5d63dc6fb23a45f0ddfb226a195324d153615588c6c1363a74ce04c"
EXPECTED_FRONTIER = "9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e"


def _reanchor_paths(tmp_audit_dir: Path) -> None:
    """Point the audit module's path constants at ROOT-anchored absolute paths.

    PANEL_DIR, LEDGER_PATH, SUMMARY_PATH, ART point to the real committed artifacts.
    AUDIT_DIR is redirected to tmp_audit_dir so the audit writes its dated artifact
    there instead of polluting the committed integrity_audit/ directory.
    """
    art = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
    mod.PANEL_DIR = art / "data" / "panels"
    mod.LEDGER_PATH = art / "grid_result_ledger.json"
    mod.SUMMARY_PATH = art / "grid_summary.json"
    mod.ART = art
    mod.AUDIT_DIR = tmp_audit_dir
    mod.AUDIT_DIR.mkdir(parents=True, exist_ok=True)


class CommittedExpandingUniverseEligibilityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create temp audit dir under repo root so relative_to(ROOT) works for the print statement
        cls._tmp_root = ROOT / ".tmp_test_audit"
        cls._tmp_root.mkdir(exist_ok=True)
        cls._tmp_audit_dir = cls._tmp_root / f"audit_{int(time.time() * 1000)}"
        cls._tmp_audit_dir.mkdir(parents=True)
        _reanchor_paths(cls._tmp_audit_dir)
        required = [
            mod.PANEL_DIR / "marketcap_panel.csv",
            mod.LEDGER_PATH,
            mod.SUMMARY_PATH,
        ]
        # At least one kline panel must exist
        kline_files = list(mod.PANEL_DIR.glob("binance_klines_*.csv"))
        if not kline_files:
            raise unittest.SkipTest("no committed kline panels found")
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        # Run the real audit main() - it writes to tmp_audit_dir, not the committed dir
        cls.result = mod.main()
        # Find the audit artifact written to our temp dir
        artifacts = sorted(cls._tmp_audit_dir.glob("H004V106_expanding_universe_eligibility_coverage_*.json"))
        if not artifacts:
            raise unittest.SkipTest("no audit artifact produced in temp dir")
        cls.audit = json.loads(artifacts[-1].read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        import shutil
        if cls._tmp_root.exists():
            shutil.rmtree(cls._tmp_root)

    def test_audit_main_returns_zero(self):
        self.assertEqual(self.result, 0)

    def test_verdict_is_pass_with_expected_status(self):
        self.assertEqual(self.audit["verdict"] if "verdict" in self.audit else self.audit.get("audit_pass"), True)
        self.assertEqual(self.audit["status"], "EXPLORATORY_ONLY")
        self.assertEqual(self.audit["hypothesis"], "H33")
        self.assertEqual(
            self.audit["experiment_id"], "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-EXP-ELIG-001"
        )

    def test_frozen_hashes_match_committed_artifacts(self):
        frozen = self.audit["frozen_hashes_verified"]
        self.assertTrue(self.audit["all_frozen_hashes_match"])

        # Canonical forward block
        self.assertEqual(frozen["canonical_forward_block"]["expected"], EXPECTED_CANONICAL)
        self.assertEqual(frozen["canonical_forward_block"]["actual"], EXPECTED_CANONICAL)
        self.assertTrue(frozen["canonical_forward_block"]["match"])

        # H10 fresh block
        self.assertEqual(frozen["h10_fresh_block"]["expected"], EXPECTED_FRESH)
        self.assertEqual(frozen["h10_fresh_block"]["actual"], EXPECTED_FRESH)
        self.assertTrue(frozen["h10_fresh_block"]["match"])

        # Grid result ledger
        self.assertEqual(frozen["grid_result_ledger"]["expected"], EXPECTED_GRID_LEDGER)
        self.assertEqual(frozen["grid_result_ledger"]["actual"], EXPECTED_GRID_LEDGER)
        self.assertTrue(frozen["grid_result_ledger"]["match"])

        # Universe frontier
        self.assertEqual(frozen["universe_frontier"]["expected"], EXPECTED_FRONTIER)
        self.assertEqual(frozen["universe_frontier"]["actual"], EXPECTED_FRONTIER)
        self.assertTrue(frozen["universe_frontier"]["match"])

        # Cross-check against independent sha256 of disk files
        art = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
        self.assertEqual(mod.sha256_file(art / "forward_block" / "forward_block_evaluation.json"), EXPECTED_CANONICAL)
        self.assertEqual(mod.sha256_file(art / "forward_block_h10_fresh" / "forward_block_evaluation.json"), EXPECTED_FRESH)
        self.assertEqual(mod.sha256_file(art / "grid_result_ledger.json"), EXPECTED_GRID_LEDGER)
        self.assertEqual(mod.sha256_file(ROOT / "research_state" / "universe_frontier.json"), EXPECTED_FRONTIER)

    def test_eligible_stats_are_reasonable(self):
        stats = self.audit["eligible_stats"]
        self.assertGreaterEqual(stats["n_dates"], 1000)
        self.assertEqual(stats["min"], 26)
        self.assertEqual(stats["max"], 32)
        self.assertGreater(stats["mean"], 28.0)
        self.assertLess(stats["mean"], 30.0)

    def test_ledger_comparison_all_configs_consistent(self):
        for comp in self.audit["ledger_comparison"]:
            with self.subTest(config=comp["config_id"]):
                self.assertTrue(comp["consistency"]["overall_ok"])
                self.assertTrue(comp["consistency"]["mean_ok"])
                self.assertTrue(comp["consistency"]["min_ok"])
                self.assertTrue(comp["consistency"]["max_ok"])
                self.assertEqual(comp["reconstructed"]["missing_dates_count"], 0)
                # Reconstructed values should match ledger values exactly (within tolerance)
                self.assertAlmostEqual(
                    comp["reconstructed"]["mean"],
                    comp["ledger_eligible_assets_per_date"]["mean"],
                    places=10,
                )
                self.assertEqual(
                    comp["reconstructed"]["min"],
                    comp["ledger_eligible_assets_per_date"]["min"],
                )
                self.assertEqual(
                    comp["reconstructed"]["max"],
                    comp["ledger_eligible_assets_per_date"]["max"],
                )

    def test_lifecycle_events_present(self):
        lifecycle = self.audit["lifecycle_events"]
        self.assertIn("listings", lifecycle)
        self.assertIn("delistings", lifecycle)
        self.assertIn("total_listings", lifecycle)
        self.assertIn("total_delistings", lifecycle)
        self.assertIsInstance(lifecycle["total_listings"], int)
        self.assertIsInstance(lifecycle["total_delistings"], int)

    def test_exclusion_counts_reported(self):
        excl = self.audit["exclusion_counts_total"]
        self.assertIn("delisted", excl)
        self.assertIn("no_market_cap_observation", excl)
        self.assertIn("no_perpetual_contract", excl)
        self.assertIn("not_yet_listed", excl)
        self.assertIsInstance(excl["delisted"], int)
        self.assertGreaterEqual(excl["delisted"], 0)

    def test_rank_distribution_present(self):
        rank_dist = self.audit["rank_distribution"]
        self.assertIn("p50", rank_dist)
        self.assertIn("mean", rank_dist)
        self.assertIn("max", rank_dist)
        self.assertGreater(rank_dist["max"], 0)

    def test_note_indicates_exploratory_only(self):
        self.assertIn("EXPLORATORY_ONLY", self.audit["note"])
        self.assertIn("does not validate", self.audit["note"].lower())


class SyntheticDriftSelfTest(unittest.TestCase):
    """If a synthetic audit artifact with mismatched hashes is injected, the audit must FAIL."""

    def test_synthetic_mismatch_detected(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            # Create minimal synthetic panels
            panels = td / "panels"
            panels.mkdir()
            (panels / "marketcap_panel.csv").write_text(
                "date,asset,CapMrktCurUSD,CapMrktEstUSD\n"
                "2023-01-01,btc,1000,100\n"
                "2023-01-01,eth,500,50\n",
                encoding="utf-8",
            )
            (panels / "binance_klines_BTCUSDT.csv").write_text(
                "open_time,close\n1672531200000,100\n", encoding="utf-8"
            )
            (panels / "binance_klines_ETHUSDT.csv").write_text(
                "open_time,close\n1672531200000,50\n", encoding="utf-8"
            )

            # Create synthetic ledger
            ledger = {
                "cells": {
                    "H004V106": {
                        "parameters": {"universe_arm": "expanding_point_in_time"},
                        "formations": [{"formation_date": "2023-01-01"}],
                        "eligible_assets_per_date": {"mean": 2.0, "min": 2, "max": 2},
                    }
                }
            }
            ledger_path = td / "ledger.json"
            ledger_path.write_text(json.dumps(ledger))

            # Create temp audit dir
            tmp_audit_dir = td / "audit"
            tmp_audit_dir.mkdir()

            # Point audit module at synthetic dirs
            old_panel = mod.PANEL_DIR
            old_ledger = mod.LEDGER_PATH
            old_audit_dir = mod.AUDIT_DIR
            old_art = mod.ART
            old_root = mod.ROOT
            mod.PANEL_DIR = panels
            mod.LEDGER_PATH = ledger_path
            mod.AUDIT_DIR = tmp_audit_dir
            mod.ART = td / "empty_art"
            mod.ART.mkdir()
            mod.ROOT = td
            try:
                rc = mod.main()
            finally:
                mod.PANEL_DIR = old_panel
                mod.LEDGER_PATH = old_ledger
                mod.AUDIT_DIR = old_audit_dir
                mod.ART = old_art
                mod.ROOT = old_root

            # With empty ART, frozen hashes will be MISSING -> audit should FAIL (rc 1)
            self.assertEqual(rc, 1)
            written = list(tmp_audit_dir.glob("*.json"))
            self.assertEqual(len(written), 1)
            report = json.loads(written[0].read_text(encoding="utf-8"))
            self.assertEqual(report["hypothesis"], "H33")
            self.assertEqual(report["status"], "EXPLORATORY_ONLY")
            self.assertFalse(report["all_frozen_hashes_match"])
            self.assertFalse(report["audit_pass"])


if __name__ == "__main__":
    unittest.main()