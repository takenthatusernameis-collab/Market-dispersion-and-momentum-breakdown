"""Independent recomputation of the H10 maturity calendar from the raw panel.

Both committed maturity tests (``test_h10_maturity_timeline_audit_committed.py``
and ``test_h10_confirm_gate_earliest_calendar_committed.py``) derive every
milestone value through ``scripts/h10_maturity_timeline_audit.py``'s OWN helpers
(``kline_dates_in_window``, ``_in_block_formations``, ``compute_maturity_milestones``
and the module's ``_shift_date`` usage). If any of those helpers carried an
off-by-one or a mis-parsed ``open_time``, both tests would still agree with each
other while being wrong together -- they share the same code path.

AGENTS.md requires an *independent recomputation* of any evidence that gates a
decision. This module supplies it for the feasibility chain that governs the
2026-11-30 Option A decision. It re-derives the merged daily index, the in-block
formation count, the M1/M2 cutoff indices and their calendar dates from first
principles using only the standard library and the raw committed kline CSV, then:

  * cross-checks those independent values against the audit module's output so a
    divergence between the two implementations fails loudly;
  * red-teams the "necessary-condition lower bound" claim by showing that a
    hypothetical forward archive gap pushes each calendar estimate strictly
    later, i.e. the committed dates are lower bounds, not point promises.

Read-only, stdlib-only, no network, no frozen artifact modified.
"""
from __future__ import annotations

import csv
import datetime as _dt
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
KLINES = ART / "data" / "panels" / "binance_klines_BTCUSDT.csv"
FRESH_BLOCK = ART / "forward_block_h10_fresh" / "forward_block_evaluation.json"
SPEC_PATH = ROOT / "scripts" / "h10_maturity_timeline_audit.py"

# Frozen hash literals (independent copy; a coordinated change to a module
# constant and a frozen artifact still fails here).
EXPECTED_CANONICAL = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"
EXPECTED_FRESH = "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f"
EXPECTED_GRID_LEDGER = "0184f2d3e5d63dc6fb23a45f0ddfb226a195324d153615588c6c1363a74ce04c"
EXPECTED_FRONTIER = "9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e"
EXPECTED_GRID_CONFIG = "1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176"

# Frozen implementation constants (mirrored here as independent literals so a
# silent change to the audit module's copies is caught by the cross-check).
MIN_PRIOR_DISPERSIONS = 30
MIN_STATE_FORMATIONS = 5
FORWARD_HORIZON_DAYS = 30


def _load_module():
    spec = importlib.util.spec_from_file_location("h10_maturity_audit_indep", SPEC_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _independent_dates(csv_path: Path) -> list[str]:
    """Sorted unique UTC dates parsed directly from the raw ``open_time`` column.

    Deliberately does NOT call the audit module's ``kline_dates_in_window``.
    """
    out: set[str] = set()
    with csv_path.open("r", newline="") as f:
        for row in csv.DictReader(f):
            ms = int(row["open_time"])
            day = _dt.datetime.fromtimestamp(ms / 1000.0, tz=_dt.timezone.utc)
            out.add(day.strftime("%Y-%m-%d"))
    return sorted(out)


def _in_block(cutoff_index: int, horizon: int, block_start_index: int) -> int:
    """Independent in-block formation count (audit rule re-derived here).

    A formation at merged-index position ``i`` is in-block iff
    ``block_start_index <= i <= cutoff_index - horizon`` (30-day maturity).
    """
    return max(0, cutoff_index - horizon - block_start_index + 1)


def _cutoff_index_for(block_start_index: int, horizon: int, in_block_needed: int) -> int:
    """Smallest cutoff index that yields ``in_block_needed`` in-block formations."""
    return block_start_index + horizon + in_block_needed - 1


def _calendar_estimate(last_date: _dt.date, additional_index_positions: int) -> _dt.date:
    """Necessary-condition calendar estimate assuming one index position per day."""
    return last_date + _dt.timedelta(days=additional_index_positions)


def _calendar_estimate_with_forward_gap(
    last_date: _dt.date, additional_index_positions: int, gap_days: int
) -> _dt.date:
    """Estimate if the forward window contains ``gap_days`` missing calendar days.

    Each missing day is a calendar day with no bar, so it contributes no index
    position; accruing the same number of index positions then needs
    ``additional_index_positions + gap_days`` calendar days.
    """
    return last_date + _dt.timedelta(days=additional_index_positions + gap_days)


class H10MaturityIndependentRecomputeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [str(p) for p in (KLINES, FRESH_BLOCK, SPEC_PATH) if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.dates = _independent_dates(KLINES)
        cls.first_date = _dt.date.fromisoformat(cls.dates[0])
        cls.last_date = _dt.date.fromisoformat(cls.dates[-1])
        cls.block_start = str(cls._fresh_block()["forward_block_start"])
        cls.block_start_index = cls.dates.index(cls.block_start)
        cls.last_index = len(cls.dates) - 1
        cls.horizon = FORWARD_HORIZON_DAYS

    @staticmethod
    def _fresh_block() -> dict:
        import json
        with FRESH_BLOCK.open() as f:
            return json.load(f)

    # --- Raw index geometry (independent of the module) ---------------------

    def test_index_geometry_and_the_single_known_gap(self):
        # The merged daily index has exactly one hole: 2026-10-28. A naive
        # date-range would not notice this; the independent count does.
        calendar_days = (self.last_date - self.first_date).days + 1
        self.assertEqual(calendar_days - len(self.dates), 1)
        self.assertEqual(self.dates[0], "2023-01-01")
        self.assertEqual(self.dates[-1], "2026-10-31")
        have = set(self.dates)
        missing = []
        d = self.first_date
        while d <= self.last_date:
            if d.isoformat() not in have:
                missing.append(d.isoformat())
            d += _dt.timedelta(days=1)
        self.assertEqual(missing, ["2026-10-28"])

    def test_block_start_index_and_current_position(self):
        # 2026-09-30 .. 2026-10-31 is 32 calendar days, minus the 2026-10-28 gap
        # = 30 index positions from block start to the last observed date.
        self.assertEqual(self.block_start, "2026-09-30")
        self.assertEqual(self.last_index - self.block_start_index, 30)

    # --- Current block state (independent) ----------------------------------

    def test_current_block_is_immature(self):
        fresh = self._fresh_block()
        current_in_block = _in_block(self.last_index, self.horizon, self.block_start_index)
        current_classifiable = max(0, current_in_block - MIN_PRIOR_DISPERSIONS)
        self.assertEqual(current_in_block, 1)
        self.assertEqual(current_classifiable, 0)
        self.assertEqual(fresh.get("n_formations"), 1)
        self.assertEqual(fresh.get("n_high"), 0)
        self.assertEqual(fresh.get("n_low"), 0)

    # --- M1 / M2 / M3 calendar, derived from first principles ---------------

    def test_m1_earliest_cutoff_is_2026_12_01(self):
        m1_in_block = MIN_PRIOR_DISPERSIONS + 2  # 32
        cutoff_index = _cutoff_index_for(self.block_start_index, self.horizon, m1_in_block)
        additional = cutoff_index - self.last_index
        date = _calendar_estimate(self.last_date, additional)
        self.assertEqual(m1_in_block, 32)
        self.assertEqual(additional, 31)
        self.assertEqual(date.isoformat(), "2026-12-01")
        # The independent cutoff index must exceed the current position.
        self.assertGreater(cutoff_index, self.last_index)

    def test_m2_hard_lower_bound_earliest_is_2026_12_09(self):
        m2_lb = MIN_PRIOR_DISPERSIONS + 2 * MIN_STATE_FORMATIONS  # 40
        cutoff_index = _cutoff_index_for(self.block_start_index, self.horizon, m2_lb)
        additional = cutoff_index - self.last_index
        date = _calendar_estimate(self.last_date, additional)
        self.assertEqual(m2_lb, 40)
        self.assertEqual(additional, 39)
        self.assertEqual(date.isoformat(), "2026-12-09")

    def test_m2_decile_estimate_is_2027_01_18(self):
        # ~min_state / 0.1 classifiable formations -> ~50, plus min_prior = 80.
        import math
        classifiable_needed = math.ceil(MIN_STATE_FORMATIONS / 0.10)
        m2_est = MIN_PRIOR_DISPERSIONS + classifiable_needed
        cutoff_index = _cutoff_index_for(self.block_start_index, self.horizon, m2_est)
        additional = cutoff_index - self.last_index
        date = _calendar_estimate(self.last_date, additional)
        self.assertEqual(m2_est, 80)
        self.assertEqual(additional, 79)
        self.assertEqual(date.isoformat(), "2027-01-18")
        # Decile estimate must not precede the hard lower bound.
        self.assertGreaterEqual(date, _dt.date.fromisoformat("2026-12-09"))

    def test_november_2026_vintage_cannot_reach_m1(self):
        nov_cutoff_index = self.last_index + 30
        nov_in_block = _in_block(nov_cutoff_index, self.horizon, self.block_start_index)
        nov_classifiable = max(0, nov_in_block - MIN_PRIOR_DISPERSIONS)
        self.assertEqual(
            _calendar_estimate(self.last_date, 30).isoformat(), "2026-11-30"
        )
        self.assertEqual(nov_in_block, 31)
        self.assertEqual(nov_classifiable, 1)
        self.assertLess(nov_classifiable, 2)  # M1 needs >=2 classifiable

    # --- Red-team: the calendar dates are lower bounds, not promises --------

    def test_estimates_are_lower_bounds_shifting_later_with_a_forward_gap(self):
        m1_in_block = MIN_PRIOR_DISPERSIONS + 2
        cutoff_index = _cutoff_index_for(self.block_start_index, self.horizon, m1_in_block)
        additional = cutoff_index - self.last_index
        no_gap = _calendar_estimate(self.last_date, additional)
        one_gap = _calendar_estimate_with_forward_gap(self.last_date, additional, 1)
        # The committed 2026-12-01 estimate is the no-gap lower bound; a single
        # missing forward bar must move it strictly later (2026-12-02).
        self.assertEqual(no_gap.isoformat(), "2026-12-01")
        self.assertEqual(one_gap.isoformat(), "2026-12-02")
        self.assertGreater(one_gap, no_gap)

    def test_estimates_are_sensitive_to_feasibility_constants(self):
        # A shorter horizon needs fewer in-block formations before the cutoff.
        m2_lb = MIN_PRIOR_DISPERSIONS + 2 * MIN_STATE_FORMATIONS
        short_cutoff = _cutoff_index_for(self.block_start_index, 14, m2_lb)
        short_date = _calendar_estimate(self.last_date, short_cutoff - self.last_index)
        self.assertLess(short_date, _dt.date.fromisoformat("2026-12-09"))

    # --- Cross-check: independent derivation agrees with the audit module ----

    def test_independent_values_match_audit_module_output(self):
        mod = _load_module()
        mod.ARTIFACT_DIR = ART
        mod.FRESH_BLOCK_PATH = FRESH_BLOCK
        mod.PANEL_DIR = ART / "data" / "panels"
        mod.KLINES_BTC_PATH = KLINES
        mod.CANONICAL_BLOCK_PATH = ART / "forward_block" / "forward_block_evaluation.json"
        mod.GRID_LEDGER_PATH = ART / "grid_result_ledger.json"
        mod.UNIVERSE_FRONTIER_PATH = ROOT / "research_state" / "universe_frontier.json"
        mod.GRID_CONFIG_PATH = ROOT / "configs" / "dispersion_momentum_grid_v3.json"
        mod.EVAL_SRC_PATH = ROOT / "scripts" / "eval_forward_block.py"

        ms = mod.compute_maturity_milestones(
            block_start=self.block_start,
            last_observed_date=self.dates[-1],
            block_start_index=self.block_start_index,
            last_observed_index=self.last_index,
        )
        self.assertEqual(ms["current_in_block_formations"], 1)
        self.assertEqual(ms["current_classifiable_formations"], 0)
        self.assertEqual(
            ms["M1_first_mature_look"]["earliest_cutoff_calendar_estimate"], "2026-12-01"
        )
        self.assertEqual(
            ms["M2_magnitude_estimable"]["hard_lower_bound_in_block_formations"], 40
        )
        self.assertEqual(
            ms["november_2026_vintage"]["in_block_formations"], 31
        )
        self.assertFalse(ms["november_2026_vintage"]["m1_possible"])

    # --- Frozen hashes -------------------------------------------------------

    def test_frozen_hashes_match_committed_artifacts(self):
        mod = _load_module()
        self.assertEqual(
            mod.sha256_file(ART / "forward_block" / "forward_block_evaluation.json"),
            EXPECTED_CANONICAL,
        )
        self.assertEqual(mod.sha256_file(FRESH_BLOCK), EXPECTED_FRESH)
        self.assertEqual(
            mod.sha256_file(ART / "grid_result_ledger.json"), EXPECTED_GRID_LEDGER
        )
        self.assertEqual(
            mod.sha256_file(ROOT / "research_state" / "universe_frontier.json"),
            EXPECTED_FRONTIER,
        )
        self.assertEqual(
            mod.sha256_file(ROOT / "configs" / "dispersion_momentum_grid_v3.json"),
            EXPECTED_GRID_CONFIG,
        )


if __name__ == "__main__":
    unittest.main()