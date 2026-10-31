#!/usr/bin/env python3
"""Regression tests for Binance panel manifest provenance.

Two defects are pinned here, both of which slipped through because no test ever
checked the manifest's boundary/rows fields against the panel CSVs they claim to
describe:

1. Funding panels truncated to the final month. ``repair_funding_panels.py``
   wrote one output file per zip, so each panel was overwritten by the last zip
   in iteration order -- 90 rows for 2026-09-01..2026-09-29 instead of the full
   45-month window. The manifest's ``date_first`` for funding series then read
   2026-09-01 rather than 2023-01-01.

2. Manifest ``rows`` counting raw-archive newlines (including each monthly
   header row) instead of the data rows actually written to the panel CSV.

These tests read only the CSV/JSON artifacts (stdlib csv + json), so they run in
environments where pandas/numpy are unavailable.
"""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
PANELS = ROOT / "artifacts" / EXP / "data" / "panels"
MANIFEST_PATH = PANELS / "binance_panel_manifest.json"

KIND_COL = {"klines": "open_time", "funding": "calc_time"}


def panel_stats(kind: str, symbol: str) -> tuple[int, int, int]:
    path = PANELS / f"binance_{kind}_{symbol}.csv"
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        col = header.index(KIND_COL[kind])
        rows = list(reader)
    ts = [int(r[col]) for r in rows]
    return min(ts), max(ts), len(rows)


class BinancePanelManifestProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST_PATH.read_text())
        cls.series = {f"{s['kind']}:{s['symbol']}": s for s in cls.manifest["series"]}

    def test_manifest_boundaries_match_panel_csvs(self):
        for key, s in self.series.items():
            kind, symbol = key.split(":")
            first, last, n = panel_stats(kind, symbol)
            self.assertEqual(
                int(s["date_first"]), first,
                f"{key}: manifest date_first {s['date_first']} != panel min {first}",
            )
            self.assertEqual(
                int(s["date_last"]), last,
                f"{key}: manifest date_last {s['date_last']} != panel max {last}",
            )
            self.assertEqual(
                s["rows"], n,
                f"{key}: manifest rows {s['rows']} != panel data rows {n}",
            )

    def test_funding_panels_span_full_window_not_final_month(self):
        """The truncated-panel bug made funding date_first == 2026-09-01.

        The manifest window starts 2023-01-01 (1672531200000); the truncation
        bug instead recorded the final month's first observation
        (1788220800005 = 2026-09-01). Pin the exact window start so a regression
        cannot slip through as a different but still-wrong value.
        """
        for key, s in self.series.items():
            if not key.startswith("funding:"):
                continue
            self.assertEqual(
                int(s["date_first"]), 1672531200000,
                f"{key}: funding date_first {s['date_first']} is not the window "
                f"start 2023-01-01 (1672531200000); the panel is truncated to the "
                f"final month (would be 1788220800005 = 2026-09-01)",
            )

    def test_funding_panel_row_count_exceeds_single_month_rows(self):
        """A single Binance funding month has ~90 rows; the full window has ~4100."""
        for key, s in self.series.items():
            if not key.startswith("funding:"):
                continue
            self.assertGreater(
                s["rows"], 1000,
                f"{key}: funding rows {s['rows']} looks like a single month, "
                f"not the full 45-month window",
            )

    def test_manifest_series_covers_both_kinds_and_assets(self):
        kinds = {s["kind"] for s in self.manifest["series"]}
        symbols = {s["symbol"] for s in self.manifest["series"]}
        self.assertEqual(kinds, {"klines", "funding"})
        self.assertEqual(symbols, {"BTCUSDT", "ETHUSDT"})
        self.assertEqual(len(self.manifest["series"]), 4)


if __name__ == "__main__":
    unittest.main()