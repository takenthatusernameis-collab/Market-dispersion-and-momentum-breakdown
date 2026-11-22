"""Committed-disk pin: H10 confirmatory-gate earliest-possible calendar cutoffs.

The maturity-timeline audit (``scripts/h10_maturity_timeline_audit.py``, H35)
pins the M1 (first mature look) calendar estimate (2026-12-01) and expresses M2
(magnitude estimable) / M3 (confirmatory) only as in-block *formation counts*
(M2 hard lower bound 40, decile-based estimate 80). It never converts those
counts into calendar cutoff dates. That missing conversion is exactly what a
next agent needs at the 2026-11-30 date gate: it decides whether a
confirmatory-eligible look is even reachable soon after the gate, and stops the
gate from being misread as "run on 2026-12-01 and confirm".

This test derives the calendar earliest-possible cutoffs from the REAL committed
artifacts, via the audit module's own pure helpers, and pins them:

  * M1  (n_high>0 AND n_low>0, alpha-spend start): >=32 in-block formations
        -> earliest cutoff 2026-12-01.
  * M2  (n_high>=5 AND n_low>=5, magnitude estimable): hard lower bound
        >=40 in-block formations -> earliest cutoff 2026-12-09. This is a
        NECESSARY-condition lower bound only (you cannot have 5 high + 5 low
        with fewer than 10 classifiable formations); the audit's decile-based
        order-of-magnitude estimate (80 in-block) maps to ~2027-01-18, i.e.
        realistically later.
  * M3  (confirmatory claim): gated on M2 -> earliest cutoff >= 2026-12-09.

All dates assume the daily merged-index cadence with no further archive gaps;
the audit labels them necessary-condition lower bounds that shift later with any
gap. Read-only, stdlib-only, no network, no frozen artifact modified.
"""
from __future__ import annotations

import datetime as _dt
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "h10_maturity_timeline_audit.py"

spec = importlib.util.spec_from_file_location("h10_maturity_audit_calendar", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Frozen hash literals the audit is expected to quote (kept here as an
# independent copy so a change to the module constants alone cannot satisfy this
# test).
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


def _shift_date(last_date: str, days: int) -> str:
    return (_dt.date.fromisoformat(last_date) + _dt.timedelta(days=days)).isoformat()


def _m2_hard_lb_cutoff(ms, last_date, block_start_index, last_observed_index, horizon):
    """Calendar cutoff at which the M2 hard lower bound is first met.

    M2 (n_high>=MIN_STATE AND n_low>=MIN_STATE) needs at least
    ``hard_lower_bound`` in-block formations. A formation at cutoff index ``c``
    is in-block iff ``c - horizon - block_start_index + 1 >= hard_lower_bound``,
    i.e. ``c >= block_start_index + horizon + hard_lower_bound - 1``. Returns
    ``(date, additional_index_positions, hard_lower_bound)``.
    """
    hard_lb = ms["M2_magnitude_estimable"]["hard_lower_bound_in_block_formations"]
    cutoff_offset = horizon + hard_lb - 1
    current_offset = last_observed_index - block_start_index
    additional = cutoff_offset - current_offset
    return _shift_date(last_date, additional), additional, hard_lb


def _m2_decile_cutoff(ms, last_date, block_start_index, last_observed_index, horizon):
    """Calendar cutoff for the audit's decile-based M2 estimate (order-of-magnitude)."""
    est = ms["M2_magnitude_estimable"]["decile_based_estimate_in_block_formations"]
    cutoff_offset = horizon + est - 1
    current_offset = last_observed_index - block_start_index
    additional = cutoff_offset - current_offset
    return _shift_date(last_date, additional), additional, est


class H10ConfirmGateEarliestCalendarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _reanchor_paths()
        required = [
            mod.FRESH_BLOCK_PATH,
            mod.KLINES_BTC_PATH,
            mod.GRID_LEDGER_PATH,
            mod.UNIVERSE_FRONTIER_PATH,
            mod.GRID_CONFIG_PATH,
        ]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.fresh = mod.load_json(mod.FRESH_BLOCK_PATH)
        cls.all_dates = mod.kline_dates_in_window(
            mod.KLINES_BTC_PATH, "0000-00-00", "9999-99-99"
        )
        cls.block_start = str(cls.fresh["forward_block_start"])
        cls.block_start_index = cls.all_dates.index(cls.block_start)
        cls.last_observed_index = len(cls.all_dates) - 1
        cls.last_date = cls.all_dates[-1]
        cls.ms = mod.compute_maturity_milestones(
            block_start=cls.block_start,
            last_observed_date=cls.last_date,
            block_start_index=cls.block_start_index,
            last_observed_index=cls.last_observed_index,
        )
        cls.horizon = mod.FORWARD_HORIZON_DAYS

    def test_current_block_is_immature_with_gap_adjusted_geometry(self):
        self.assertEqual(self.last_date, "2026-10-31")
        # 31 calendar days from 2026-09-30..2026-10-31 minus the 2026-10-28 gap.
        self.assertEqual(self.last_observed_index - self.block_start_index, 30)
        self.assertEqual(self.ms["current_in_block_formations"], 1)
        self.assertEqual(self.ms["current_classifiable_formations"], 0)
        self.assertEqual(self.fresh.get("n_high"), 0)
        self.assertEqual(self.fresh.get("n_low"), 0)

    def test_m1_earliest_is_2026_12_01(self):
        m1 = self.ms["M1_first_mature_look"]
        self.assertEqual(m1["min_in_block_formations"], 32)
        self.assertEqual(m1["additional_index_positions_needed"], 31)
        self.assertEqual(m1["earliest_cutoff_calendar_estimate"], "2026-12-01")
        # The calendar date must equal last_date + additional positions.
        self.assertEqual(
            m1["earliest_cutoff_calendar_estimate"],
            _shift_date(self.last_date, m1["additional_index_positions_needed"]),
        )

    def test_m2_hard_lower_bound_earliest_is_2026_12_09(self):
        date, additional, hard_lb = _m2_hard_lb_cutoff(
            self.ms, self.last_date, self.block_start_index,
            self.last_observed_index, self.horizon,
        )
        self.assertEqual(hard_lb, 40)
        self.assertEqual(additional, 39)
        self.assertEqual(date, "2026-12-09")

    def test_m2_decile_estimate_is_2027_01_18(self):
        date, additional, est = _m2_decile_cutoff(
            self.ms, self.last_date, self.block_start_index,
            self.last_observed_index, self.horizon,
        )
        self.assertEqual(est, 80)
        self.assertEqual(additional, 79)
        self.assertEqual(date, "2027-01-18")
        # The decile-based realistic estimate must not be earlier than the hard
        # lower bound.
        self.assertGreaterEqual(date, "2026-12-09")

    def test_m3_is_gated_on_m2_and_not_earlier(self):
        m3 = self.ms["M3_confirmatory_claim"]
        self.assertIn("not reachable until M2", m3["note"])
        m2_date, _, _ = _m2_hard_lb_cutoff(
            self.ms, self.last_date, self.block_start_index,
            self.last_observed_index, self.horizon,
        )
        # M3 requires M2, so its earliest-possible cutoff is the M2 cutoff.
        self.assertEqual(m2_date, "2026-12-09")

    def test_earliest_dates_are_labelled_necessary_lower_bounds(self):
        note = self.ms["M1_first_mature_look"]["earliest_cutoff_note"].lower()
        self.assertIn("necessary-condition", note)
        self.assertIn("shifts later", note)
        self.assertIn("gap", note)

    def test_calendar_conversion_is_sensitive_not_hardcoded(self):
        """Red-team: the derived date must respond to the feasibility constants,
        not be a magic literal. A shorter horizon must move M2 earlier; a larger
        prior-dispersion requirement must move it later."""
        # Shorter horizon (14d) -> fewer formations needed before the cutoff.
        ms_short = mod.compute_maturity_milestones(
            block_start=self.block_start,
            last_observed_date=self.last_date,
            block_start_index=self.block_start_index,
            last_observed_index=self.last_observed_index,
            horizon=14,
        )
        short_date, short_add, _ = _m2_hard_lb_cutoff(
            ms_short, self.last_date, self.block_start_index,
            self.last_observed_index, 14,
        )
        self.assertEqual(short_date, "2026-11-23")
        self.assertLess(short_date, "2026-12-09")

        # Larger MIN_PRIOR_DISPERSIONS (40) -> more in-block formations needed.
        ms_long = mod.compute_maturity_milestones(
            block_start=self.block_start,
            last_observed_date=self.last_date,
            block_start_index=self.block_start_index,
            last_observed_index=self.last_observed_index,
            min_prior=40,
        )
        long_date, long_add, long_lb = _m2_hard_lb_cutoff(
            ms_long, self.last_date, self.block_start_index,
            self.last_observed_index, self.horizon,
        )
        self.assertEqual(long_lb, 50)
        self.assertEqual(long_date, "2026-12-19")
        self.assertGreater(long_date, "2026-12-09")

    def test_frozen_hashes_match_committed_artifacts(self):
        self.assertEqual(mod.sha256_file(mod.CANONICAL_BLOCK_PATH), EXPECTED_CANONICAL)
        self.assertEqual(mod.sha256_file(mod.FRESH_BLOCK_PATH), EXPECTED_FRESH)
        self.assertEqual(mod.sha256_file(mod.GRID_LEDGER_PATH), EXPECTED_GRID_LEDGER)
        self.assertEqual(mod.sha256_file(mod.UNIVERSE_FRONTIER_PATH), EXPECTED_FRONTIER)
        self.assertEqual(mod.sha256_file(mod.GRID_CONFIG_PATH), EXPECTED_GRID_CONFIG)

        self.assertEqual(mod.EXPECTED_CANONICAL_SHA256, EXPECTED_CANONICAL)
        self.assertEqual(mod.EXPECTED_FRESH_BLOCK_SHA256, EXPECTED_FRESH)
        self.assertEqual(mod.EXPECTED_GRID_LEDGER_SHA256, EXPECTED_GRID_LEDGER)
        self.assertEqual(mod.EXPECTED_FRONTIER_SHA256, EXPECTED_FRONTIER)
        self.assertEqual(mod.EXPECTED_GRID_CONFIG_SHA256, EXPECTED_GRID_CONFIG)


if __name__ == "__main__":
    unittest.main()