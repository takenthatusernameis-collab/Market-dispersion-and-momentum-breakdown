"""Hermetic unit tests for scripts.repair_refresh_provenance_binance.

Covers the pure, deterministic ``series_stats(kind, symbol, panels)`` seam: it
reads a single binance panel CSV and returns ``(min_ts, max_ts, row_count)``
for the timestamp column of the requested kind. The script is one-off repair
tooling that rewrites ``data_refresh_provenance.json``; these tests never invoke
``main()`` and never read or write any committed panel, manifest, or frozen
artifact. Synthetic fixtures live in a temp dir only.

No network, no secrets, no trading endpoints.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "repair_refresh_provenance_binance.py"


def _load():
    spec = importlib.util.spec_from_file_location(
        "repair_refresh_provenance_binance_test", SCRIPT
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class SeriesStatsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def _write(self, tmp: Path, kind: str, symbol: str, header: str, rows):
        path = tmp / f"binance_{kind}_{symbol}.csv"
        path.write_text(header + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
        return path

    def test_klines_open_time_min_max_count(self):
        with TemporaryDirectory() as tmp:
            panels = Path(tmp)
            self._write(
                panels, "klines", "BTCUSDT",
                "symbol,open_time,open,high,low,close,volume",
                [
                    "BTCUSDT,1700000000000,1,1,1,1,1",
                    "BTCUSDT,1700000060000,2,2,2,2,2",
                    "BTCUSDT,1700000030000,3,3,3,3,3",
                ],
            )
            first, last, n = self.mod.series_stats("klines", "BTCUSDT", panels)
            self.assertEqual((first, last, n), (1700000000000, 1700000060000, 3))

    def test_funding_calc_time_min_max_count(self):
        with TemporaryDirectory() as tmp:
            panels = Path(tmp)
            self._write(
                panels, "funding", "ETHUSDT",
                "symbol,calc_time,funding_interval_hours,last_funding_rate",
                [
                    "ETHUSDT,1700000000000,8,0.0001",
                    "ETHUSDT,1699999940000,8,0.0002",
                ],
            )
            first, last, n = self.mod.series_stats("funding", "ETHUSDT", panels)
            self.assertEqual((first, last, n), (1699999940000, 1700000000000, 2))

    def test_unsorted_rows_still_yield_min_and_max(self):
        with TemporaryDirectory() as tmp:
            panels = Path(tmp)
            self._write(
                panels, "klines", "SOLUSDT",
                "symbol,open_time,open,high,low,close,volume",
                ["SOLUSDT,9,1", "SOLUSDT,1,1", "SOLUSDT,5,1"],
            )
            first, last, n = self.mod.series_stats("klines", "SOLUSDT", panels)
            self.assertEqual((first, last, n), (1, 9, 3))

    def test_single_row_returns_equal_min_max_and_count_one(self):
        with TemporaryDirectory() as tmp:
            panels = Path(tmp)
            self._write(
                panels, "funding", "XRPUSDT",
                "symbol,calc_time,funding_interval_hours,last_funding_rate",
                ["XRPUSDT,1700000000000,8,0.0005"],
            )
            first, last, n = self.mod.series_stats("funding", "XRPUSDT", panels)
            self.assertEqual((first, last, n), (1700000000000, 1700000000000, 1))

    def test_missing_timestamp_column_raises(self):
        with TemporaryDirectory() as tmp:
            panels = Path(tmp)
            self._write(
                panels, "klines", "ADAUSDT",
                "symbol,close_time,open,high,low,close,volume",
                ["ADAUSDT,1700000000000,1,1,1,1,1"],
            )
            with self.assertRaises(ValueError):
                self.mod.series_stats("klines", "ADAUSDT", panels)

    def test_unknown_kind_raises(self):
        with TemporaryDirectory() as tmp:
            panels = Path(tmp)
            self._write(
                panels, "perp", "DOGEUSDT",
                "symbol,open_time,open,high,low,close,volume",
                ["DOGEUSDT,1700000000000,1,1,1,1,1"],
            )
            with self.assertRaises(KeyError):
                self.mod.series_stats("perp", "DOGEUSDT", panels)

    def test_module_constants(self):
        self.assertEqual(self.mod.KIND_COL, {"klines": "open_time", "funding": "calc_time"})


if __name__ == "__main__":
    unittest.main()
