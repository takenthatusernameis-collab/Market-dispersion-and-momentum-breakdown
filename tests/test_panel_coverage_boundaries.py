#!/usr/bin/env python3
"""Regression tests for the descriptive panel-coverage fields in the universe
frontier.

2026-11-08 finding: ``research_state/universe_frontier.json`` carried

    "current_panel_date_end":   "2026-10-31",
    "current_panel_date_start": "2010-07-18",

i.e. the end boundary was correct (the CoinMetrics cap panel and the Binance
kline panels both end 2026-10-31) but the start boundary described a date
(2010-07-18) that appears in NO committed panel. The CoinMetrics Community API
asset-metrics endpoint was never fetched before 2023-01-01 for this
experiment, and every committed Binance kline panel opens at 2023-01-01
(1672531200000). The 2010-07-18 value was a stale hand-written placeholder that
survived the 2026-11-02T22:14Z refresh, which corrected ``current_panel_date_end``
from 2026-10-23 to 2026-10-31 but left its start counterpart untouched -- the
same single-source-of-truth hazard class as the inverted CoinMetrics provenance
boundaries (2026-10-31) and the stale canonical-block sha256 (2026-11-02): a
descriptive field that contradicts the artifact it describes, invisible because
no test compared them.

This is a descriptive coverage field, NOT a forward-block input and NOT a gate
decision: the canonical H004V106 block (cutoff 2026-09-30) is byte-unchanged and
the H10 fresh block is unaffected. The guard below pins both boundaries against
the panel CSVs on disk so a future refresh or hand-edit cannot reintroduce a
boundary that no panel actually spans.

Read-only: no files are written. stdlib csv + json + hashlib only, so it runs
in environments where pandas/numpy are unavailable.
"""
import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
PANELS = ROOT / "artifacts" / EXP / "data" / "panels"
FRONTIER = ROOT / "research_state" / "universe_frontier.json"

KLINE_COL = "open_time"


def _kline_first_last() -> tuple[int, int]:
    """Earliest and latest open_time across every committed kline panel."""
    first = None
    last = None
    for p in sorted(PANELS.glob("binance_klines_*.csv")):
        with open(p, newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                ts = int(row[KLINE_COL])
                if first is None or ts < first:
                    first = ts
                if last is None or ts > last:
                    last = ts
    return first, last


def _cm_first_last() -> tuple[str, str]:
    with (PANELS / "marketcap_panel.csv").open(newline="", encoding="utf-8") as fh:
        dates = [r["date"] for r in csv.DictReader(fh) if r.get("date")]
    return min(dates), max(dates)


class PanelCoverageBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frontier = json.loads(FRONTIER.read_text(encoding="utf-8"))
        cls.k_first, cls.k_last = _kline_first_last()
        cls.cm_first, cls.cm_last = _cm_first_last()

    def test_frontier_declares_both_boundaries(self):
        self.assertIn("current_panel_date_end", self.frontier)
        self.assertIn("current_panel_date_start", self.frontier)

    @staticmethod
    def _day(ts_or_str) -> str:
        """Normalise a panel boundary to a YYYY-MM-DD string.

        The CoinMetrics cap panel stores ISO-8601 strings while the Binance
        kline panels store millisecond epoch ints; both helpers return the
        same type so the two boundaries can be compared. Slicing an int was
        the bug that made every boundary assertion raise TypeError.
        """
        if isinstance(ts_or_str, int):
            import datetime
            return datetime.datetime.fromtimestamp(
                ts_or_str / 1000, datetime.timezone.utc
            ).strftime("%Y-%m-%d")
        return ts_or_str[:10]

    def test_panel_date_end_matches_panel_csvs(self):
        """The declared end must equal the latest observation in the panels.

        The binding input for the forward block is the Binance kline panels, so
        the declared end is pinned to the kline last exactly. The CoinMetrics
        cap panel is refreshed on an independent schedule and may extend
        *ahead* of the klines (it reached 2026-11-03 while the kline panels end
        2026-10-31); the guard therefore also asserts the declared end never
        exceeds the cap panel, so a future refresh cannot forward-date the
        boundary past a panel that actually exists. Demanding equality with
        both panels assumed the two series always end on the same day, which
        stopped being true once the cap panel was refreshed ahead of the
        October 2026 Binance archive.
        """
        end = self._day(self.k_last)
        self.assertEqual(self.frontier["current_panel_date_end"], end)
        self.assertLessEqual(
            self.frontier["current_panel_date_end"], self._day(self.cm_last),
            msg="current_panel_date_end must not exceed the cap panel's last row",
        )

    def test_panel_date_start_matches_panel_csvs(self):
        """The declared start must equal the earliest observation in the panels.

        Guards the 2026-11-08 repair: the stale 2010-07-18 placeholder was
        replaced by 2023-01-01, which is the true first date of both the
        CoinMetrics cap panel and the Binance kline panels.
        """
        start = self._day(self.cm_first)
        self.assertEqual(self.frontier["current_panel_date_start"], start)
        self.assertEqual(self.frontier["current_panel_date_start"], self._day(self.k_first))

    def test_panel_start_is_not_before_any_panel_observation(self):
        """A start boundary earlier than every committed observation is the
        defect class this guard exists to catch (the stale 2010-07-18 value
        predated the panels by over 12 years)."""
        start = self.frontier["current_panel_date_start"]
        self.assertGreaterEqual(start, self._day(self.cm_first),
                                msg=f"current_panel_date_start {start} predates the "
                                    f"cap panel {self._day(self.cm_first)}")
        self.assertGreaterEqual(start, self._day(self.k_first),
                                msg=f"current_panel_date_start {start} predates the "
                                    f"kline panels {self._day(self.k_first)}")

    def test_panel_start_not_after_panel_end(self):
        self.assertLessEqual(
            self.frontier["current_panel_date_start"],
            self.frontier["current_panel_date_end"],
            msg="current_panel_date_start must not exceed current_panel_date_end",
        )

    def test_marketcap_panel_sha256_matches_frontier_provenance(self):
        """The frontier's refresh note quotes the cap panel span; pin the panel
        sha256 recorded in the refresh provenance against the CSV on disk so the
        note cannot describe a panel that has since been rewritten."""
        prov = json.loads((PANELS / "data_refresh_provenance.json").read_text(encoding="utf-8"))
        actual = hashlib.sha256((PANELS / "marketcap_panel.csv").read_bytes()).hexdigest()
        self.assertEqual(prov["coinmetrics"]["panel_sha256"], actual)


if __name__ == "__main__":
    unittest.main()