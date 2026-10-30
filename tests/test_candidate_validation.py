"""Regression tests for the candidate-validation record and the universe frontier.

Two defects found on 2026-10-30 are pinned here so they cannot regress:

1. INVERTED TIMESTAMP BOUNDARIES. ``scripts/validate_candidate_batch.py`` recorded
   ``time_first``/``time_last`` as ``rows[0]``/``rows[-1]`` of the raw CoinMetrics
   payload. The CoinMetrics timeseries endpoint paginates in DESCENDING time
   order (page 1 opens at the request ``end_time`` and walks backwards; only the
   final page is ascending), so those fields were inverted for essentially every
   verified candidate (e.g. alice: time_first 2026-07-16 > time_last 2023-04-02).
   Any downstream point-in-time eligibility check built on them would be wrong.
   The boundaries are now computed after sorting rows by time ascending. The raw
   files themselves are left in API order because they are hashed by the sealed
   forward block and must stay byte-identical.

2. STALE UNIVERSE COUNT. ``universe_frontier.json`` carried
   ``expanding_universe_assets_with_cap_and_binance = 32``, which was the legacy
   refresh-panel asset count, not the point-in-time eligible expanding universe.
   The field now tracks ``len(candidates_verified)``.

These tests only read local files: no network, no secrets, no trading endpoints.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
FRONTIER_PATH = ROOT / "research_state" / "universe_frontier.json"
VAL_PATH = ART / "data" / "panels" / "candidate_batch_validation.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class CandidateValidationTests(unittest.TestCase):
    def test_time_first_is_earlier_than_time_last_for_every_verified_candidate(self):
        """No verified candidate may record an inverted observation window."""
        val = _load(VAL_PATH)
        bad = []
        for e in val["candidates_processed"]:
            if not e.get("eligible"):
                continue
            est = e["metrics"].get("CapMrktEstUSD", {})
            tf, tl = est.get("time_first"), est.get("time_last")
            if tf is None or tl is None:
                continue
            if tf > tl:
                bad.append((e["asset"], tf, tl))
        self.assertFalse(bad, msg=f"inverted time boundaries: {bad[:5]}")

    def test_time_boundaries_match_a_sorted_scan_of_the_raw_payload(self):
        """The recorded boundaries must equal the min/max time in the raw file,
        not the first/last row of the API's descending pagination."""
        val = _load(VAL_PATH)
        mismatches = []
        for e in val["candidates_processed"]:
            if not e.get("eligible"):
                continue
            est = e["metrics"].get("CapMrktEstUSD", {})
            raw_rel = est.get("raw_path")
            if not raw_rel:
                continue
            rows = _load(ROOT / raw_rel)
            times = [r.get("time") for r in rows if r.get("time")]
            if not times:
                continue
            lo, hi = min(times), max(times)
            if est.get("time_first") != lo or est.get("time_last") != hi:
                mismatches.append((e["asset"], est.get("time_first"), lo,
                                   est.get("time_last"), hi))
        self.assertEqual(mismatches, f"boundary mismatch: {mismatches[:5]}")

    def test_time_order_note_records_the_sort(self):
        """The correction must be documented on every verified metric entry so a
        future reader does not assume the raw file is ascending."""
        val = _load(VAL_PATH)
        noted = 0
        for e in val["candidates_processed"]:
            if not e.get("eligible"):
                continue
            est = e["metrics"].get("CapMrktEstUSD", {})
            if "time_order_note" in est:
                noted += 1
        self.assertGreater(noted, 0, "no verified entry carries the time_order_note")

    def test_frontier_universe_count_tracks_the_verified_list(self):
        """The declared expanding-universe size must equal the verified frontier
        list length; a stale hardcoded count is the defect this guards."""
        frontier = _load(FRONTIER_PATH)
        self.assertEqual(
            frontier["expanding_universe_assets_with_cap_and_binance"],
            len(frontier["candidates_verified"]),
            "expanding_universe_assets_with_cap_and_binance must track "
            "candidates_verified",
        )

    def test_frontier_records_why_rank_coverage_is_not_proven(self):
        """historical_rank_coverage_state is NOT_PROVEN_COMPLETE; the reason must
        be recorded rather than left implicit."""
        frontier = _load(FRONTIER_PATH)
        self.assertEqual(frontier["historical_rank_coverage_state"],
                         "NOT_PROVEN_COMPLETE")
        self.assertIn("historical_rank_coverage_reason", frontier)
        self.assertGreater(len(frontier["historical_rank_coverage_reason"]), 50)

    def test_correction_record_exists_for_the_universe_count(self):
        frontier = _load(FRONTIER_PATH)
        corrections = frontier.get("corrections", [])
        self.assertTrue(
            any(c.get("field") == "expanding_universe_assets_with_cap_and_binance"
                for c in corrections),
            "the universe-count correction must be recorded in the frontier",
        )

    def test_committed_universe_is_smaller_than_the_potential_universe(self):
        """Honest labelling: the assets actually present in the committed price
        panel (32 legacy) is a strict subset of the potential point-in-time
        universe (verified candidates), because the 190 verified candidates have
        cap history and an existing Binance symbol but no committed price panel."""
        frontier = _load(FRONTIER_PATH)
        self.assertLess(frontier["current_legacy_asset_count"],
                        frontier["expanding_universe_assets_with_cap_and_binance"])


if __name__ == "__main__":
    unittest.main()