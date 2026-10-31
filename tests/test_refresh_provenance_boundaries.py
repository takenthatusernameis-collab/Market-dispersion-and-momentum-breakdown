#!/usr/bin/env python3
"""Regression tests for data_refresh_provenance.json boundary fields.

2026-10-31 finding: ``scripts/refresh_free_data.py`` wrote the
``data_refresh_provenance.json`` coinmetrics summary as

    "date_first": cm_manifest[...]["CapMrktEstUSD"]["time_first"],
    "date_last":  max(... CapMrktEstUSD time_last ...)

i.e. it copied the manifest's already-corrected per-metric boundaries. Those
fields are correct in the manifest (they are computed after sorting rows by time
ascending -- see ``time_order_note`` in marketcap_panel_manifest.json), but the
two series are *different* assets: ``date_first`` came from the alphabetically
first asset in the panel (``1inch``) while ``date_last`` came from the asset with
the maximum CapMrktEstUSD time_last across all assets. The committed file read

    date_first 2026-07-16  (1inch's time_last, i.e. the LATEST observation)
    date_last  2023-04-04  (some other asset's time_first, i.e. the EARLIEST)

an inverted boundary that contradicted the panel CSV on disk, which actually
spans 2023-01-01..2026-10-23. The same class of defect as the CoinMetrics
manifest boundary inversion repaired 2026-10-30 and the Binance funding-panel
truncation repaired 2026-10-31: a provenance field describing a boundary that
did not match the artifact it claimed to describe, invisible because no test
compared them.

This test pins the provenance summary against the artifacts on disk:

  1. coinmetrics date_first/date_last are not inverted (date_first <= date_last);
  2. coinmetrics date_first/date_last equal the panel CSV's min/max date;
  3. coinmetrics panel_sha256/panel_rows equal the panel CSV on disk;
  4. every binance series in the provenance matches its panel CSV
     (date_first/date_last/rows), so the summary cannot drift from the
     binance_panel_manifest.json it duplicates.

Read-only: no files are written. stdlib csv + json only, so it runs in
environments where pandas/numpy are unavailable.
"""
import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
PANELS = ROOT / "artifacts" / EXP / "data" / "panels"
PROVENANCE = PANELS / "data_refresh_provenance.json"
BINANCE_MANIFEST = PANELS / "binance_panel_manifest.json"

KIND_COL = {"klines": "open_time", "funding": "calc_time"}


def _panel_stats(kind: str, symbol: str) -> tuple[int, int, int]:
    path = PANELS / f"binance_{kind}_{symbol}.csv"
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        col = header.index(KIND_COL[kind])
        rows = list(reader)
    ts = [int(r[col]) for r in rows]
    return min(ts), max(ts), len(rows)


def _cm_dates():
    with (PANELS / "marketcap_panel.csv").open(newline="", encoding="utf-8") as fh:
        return [r["date"] for r in csv.DictReader(fh) if r.get("date")]


class RefreshProvenanceBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prov = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        cls.dates = _cm_dates()

    def test_coinmetrics_provenance_boundaries_not_inverted(self):
        cm = self.prov["coinmetrics"]
        self.assertIsNotNone(cm.get("date_first"))
        self.assertIsNotNone(cm.get("date_last"))
        self.assertLessEqual(
            cm["date_first"], cm["date_last"],
            msg="coinmetrics provenance date_first must be <= date_last",
        )

    def test_coinmetrics_provenance_boundaries_match_panel_csv(self):
        cm = self.prov["coinmetrics"]
        self.assertEqual(cm["date_first"], min(self.dates),
                         msg="provenance date_first must equal the panel CSV min date")
        self.assertEqual(cm["date_last"], max(self.dates),
                         msg="provenance date_last must equal the panel CSV max date")

    def test_coinmetrics_provenance_sha_and_rows_match_panel_csv(self):
        cm = self.prov["coinmetrics"]
        actual_sha = hashlib.sha256(
            (PANELS / "marketcap_panel.csv").read_bytes()
        ).hexdigest()
        self.assertEqual(cm["panel_sha256"], actual_sha,
                         msg="provenance panel_sha256 must match the panel CSV")
        self.assertEqual(cm["panel_rows"], len(self.dates),
                         msg="provenance panel_rows must match the CSV row count")

    def test_binance_provenance_series_match_panel_csvs(self):
        """The provenance duplicates the binance_panel_manifest series; both must
        agree with the panel CSVs on disk, so neither can drift independently.

        Only the boundary/rows fields and the series identity are asserted: the
        manifest additionally carries a ``manifest_boundary_note`` added by
        fix_binance_manifest_boundaries.py, so full dict equality is not the
        invariant that matters.
        """
        manifest = json.loads(BINANCE_MANIFEST.read_text(encoding="utf-8"))
        prov_series = {f"{s['kind']}:{s['symbol']}": s for s in self.prov["binance"]["series"]}
        man_series = {f"{s['kind']}:{s['symbol']}": s for s in manifest["series"]}
        self.assertEqual(set(prov_series), set(man_series),
                         msg="provenance and manifest must describe the same series")
        for key, s in prov_series.items():
            kind, symbol = key.split(":")
            first, last, n = _panel_stats(kind, symbol)
            with self.subTest(series=key):
                self.assertEqual(s["kind"], man_series[key]["kind"])
                self.assertEqual(s["symbol"], man_series[key]["symbol"])
                self.assertEqual(s["asset"], man_series[key]["asset"])
                self.assertEqual(int(s["date_first"]), first,
                                 msg=f"{key}: provenance date_first != panel min")
                self.assertEqual(int(s["date_last"]), last,
                                 msg=f"{key}: provenance date_last != panel max")
                self.assertEqual(s["rows"], n,
                                 msg=f"{key}: provenance rows != panel data rows")
                self.assertEqual(s["rows"], man_series[key]["rows"],
                                 msg=f"{key}: provenance rows != manifest rows")
                self.assertEqual(int(s["date_first"]), int(man_series[key]["date_first"]),
                                 msg=f"{key}: provenance date_first != manifest date_first")
                self.assertEqual(int(s["date_last"]), int(man_series[key]["date_last"]),
                                 msg=f"{key}: provenance date_last != manifest date_last")


if __name__ == "__main__":
    unittest.main()