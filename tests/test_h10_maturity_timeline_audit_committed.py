"""Committed-disk verdict pin for scripts/h10_maturity_timeline_audit.py (H35).

The hermetic seam suite (test_h10_maturity_timeline_audit_seams.py) exercises the
audit only against synthetic fixtures. This module pins the audit's PASS verdict
against the REAL committed artifacts on disk, so the feasibility claims that the
2026-11-30 Option A decision relies on cannot silently drift:

  - the November 2026 vintage cutoff (2026-11-30) yields 31 in-block / 1
    classifiable formation, so the first mature look (M1: n_high>0 AND n_low>0)
    is impossible at that cutoff;
  - the earliest cutoff at which M1 is reachable is 2026-12-01 (needs >=32
    in-block formations);
  - the four frozen artifact hashes still match the values the audit quotes.

Read-only: no network, no writes. stdlib-only (the audit module imports no
numpy/pandas), so it runs in the dep-light environment too. Path constants are
re-anchored to the repository root in setUpClass so the test is CWD-independent.
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "h10_maturity_timeline_audit.py"

spec = importlib.util.spec_from_file_location("h10_maturity_audit_committed", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Frozen hash literals the audit is expected to quote (kept here as an independent
# copy so a change to the module constants alone cannot satisfy this test).
EXPECTED_CANONICAL = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"
EXPECTED_FRESH = "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f"
EXPECTED_GRID_LEDGER = "0184f2d3e5d63dc6fb23a45f0ddfb226a195324d153615588c6c1363a74ce04c"
EXPECTED_FRONTIER = "9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e"
EXPECTED_GRID_CONFIG = "1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176"


def _reanchor_paths() -> None:
    """Point the audit module's path constants at ROOT-anchored absolute paths."""
    art = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
    mod.ARTIFACT_DIR = art
    mod.FRESH_BLOCK_PATH = art / "forward_block_h10_fresh" / "forward_block_evaluation.json"
    mod.PANEL_DIR = art / "data" / "panels"
    mod.KLINES_BTC_PATH = mod.PANEL_DIR / "binance_klines_BTCUSDT.csv"
    mod.CANONICAL_BLOCK_PATH = art / "forward_block" / "forward_block_evaluation.json"
    mod.GRID_LEDGER_PATH = art / "grid_result_ledger.json"
    mod.UNIVERSE_FRONTIER_PATH = ROOT / "research_state" / "universe_frontier.json"
    mod.GRID_CONFIG_PATH = ROOT / "configs" / "dispersion_momentum_grid_v3.json"
    mod.EVAL_SRC_PATH = ROOT / "scripts" / "eval_forward_block.py"


class CommittedMaturityAuditVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _reanchor_paths()
        required = [
            mod.FRESH_BLOCK_PATH,
            mod.KLINES_BTC_PATH,
            mod.CANONICAL_BLOCK_PATH,
            mod.GRID_LEDGER_PATH,
            mod.UNIVERSE_FRONTIER_PATH,
            mod.GRID_CONFIG_PATH,
            mod.EVAL_SRC_PATH,
        ]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.result = mod.audit_h10_maturity_timeline()

    def test_verdict_is_pass_with_no_failed_checks(self):
        res = self.result
        self.assertEqual(res["verdict"], "PASS")
        self.assertEqual(res["checks_failed"], 0)
        self.assertEqual(res["checks_passed"], res["checks_total"])
        self.assertGreaterEqual(res["checks_total"], 42)

    def test_hypothesis_and_status_labels(self):
        res = self.result
        self.assertEqual(res["hypothesis_id"], "H35")
        self.assertEqual(res["status"], "EXPLORATORY_ONLY")
        self.assertEqual(
            res["experiment_id"], "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
        )

    def test_current_block_is_immature(self):
        ms = self.result["milestones"]
        self.assertEqual(ms["current_in_block_formations"], 1)
        self.assertEqual(ms["current_classifiable_formations"], 0)
        # No outcome is estimable yet.
        self.assertIsNone(self.result["milestones"].get("high_low_diff_net_1x"))

    def test_november_2026_vintage_cannot_reach_m1(self):
        nov = self.result["milestones"]["november_2026_vintage"]
        self.assertEqual(nov["cutoff_date"], "2026-11-30")
        self.assertEqual(nov["in_block_formations"], 31)
        self.assertEqual(nov["classifiable_formations"], 1)
        self.assertFalse(nov["m1_possible"])

    def test_m1_earliest_cutoff_is_2026_12_01(self):
        m1 = self.result["milestones"]["M1_first_mature_look"]
        self.assertEqual(m1["condition"], "n_high>0 AND n_low>0")
        self.assertEqual(m1["min_in_block_formations"], 32)
        self.assertEqual(m1["additional_in_block_formations_needed"], 31)
        self.assertEqual(m1["earliest_cutoff_calendar_estimate"], "2026-12-01")

    def test_frozen_hashes_match_committed_artifacts(self):
        # The audit verifies each hash against its module constant; this test also
        # cross-checks those constants against independent literals, so a
        # coordinated change to both the module and a frozen artifact still fails.
        self.assertEqual(mod.sha256_file(mod.CANONICAL_BLOCK_PATH), EXPECTED_CANONICAL)
        self.assertEqual(mod.sha256_file(mod.FRESH_BLOCK_PATH), EXPECTED_FRESH)
        self.assertEqual(mod.sha256_file(mod.GRID_LEDGER_PATH), EXPECTED_GRID_LEDGER)
        self.assertEqual(mod.sha256_file(mod.UNIVERSE_FRONTIER_PATH), EXPECTED_FRONTIER)
        self.assertEqual(mod.sha256_file(mod.GRID_CONFIG_PATH), EXPECTED_GRID_CONFIG)

        # And confirm the audit's own quoted constants agree with those literals.
        self.assertEqual(mod.EXPECTED_CANONICAL_SHA256, EXPECTED_CANONICAL)
        self.assertEqual(mod.EXPECTED_FRESH_BLOCK_SHA256, EXPECTED_FRESH)
        self.assertEqual(mod.EXPECTED_GRID_LEDGER_SHA256, EXPECTED_GRID_LEDGER)
        self.assertEqual(mod.EXPECTED_FRONTIER_SHA256, EXPECTED_FRONTIER)
        self.assertEqual(mod.EXPECTED_GRID_CONFIG_SHA256, EXPECTED_GRID_CONFIG)


if __name__ == "__main__":
    unittest.main()