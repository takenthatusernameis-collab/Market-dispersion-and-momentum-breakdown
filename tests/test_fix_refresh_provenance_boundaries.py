"""Hermetic unit tests for scripts.fix_refresh_provenance_boundaries.

The migration script recomputes ``data_refresh_provenance.json`` boundary/rows
fields from the panel CSVs on disk. Its two pure seams are:

  * ``_binance_stats(kind, symbol)`` -> ``(min_ts, max_ts, n_rows)`` for
    ``binance_{kind}_{symbol}.csv``, selecting the timestamp column by kind
    (``open_time`` for klines, ``calc_time`` for funding) and excluding the
    header row;
  * ``_cm_stats()`` -> ``(min_date, max_date, panel_sha256, n_rows)`` for
    ``marketcap_panel.csv``, skipping rows whose ``date`` is empty.

Both read only from the module-level ``PANELS`` directory. These tests point
``PANELS`` at a temp dir with synthetic CSVs: no network, no committed panel,
no frozen artifact read/write. Synthetic fixtures are software tests only,
never market evidence.

This is the exact defect class the script repairs -- a provenance field that
describes a boundary drifting from the artifact it claims to describe -- so the
recompute seams themselves must be pinned, not only the committed output.
"""

from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "fix_refresh_provenance_boundaries.py"


def _load():
    spec = importlib.util.spec_from_file_location(
        "fix_refresh_provenance_boundaries_test", SCRIPT
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class _TempPanelsCase(unittest.TestCase):
    def setUp(self):
        self.mod = _load()
        self._tmp = tempfile.TemporaryDirectory()
        self.panels = Path(self._tmp.name)
        self.mod.PANELS = self.panels

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, name: str, text: str) -> Path:
        p = self.panels / name
        p.write_text(text, encoding="utf-8")
        return p


class BinanceStatsTests(_TempPanelsCase):
    def test_klines_selects_open_time_column(self):
        # open_time is deliberately NOT the first column: a header-index bug
        # that assumed position 0 would read ``close`` instead.
        self._write(
            "binance_klines_BTCUSDT.csv",
            "close,open_time,open\n1,1000,0.5\n2,3000,0.6\n3,2000,0.7\n",
        )
        self.assertEqual(self.mod._binance_stats("klines", "BTCUSDT"), (1000, 3000, 3))

    def test_funding_selects_calc_time_column(self):
        self._write(
            "binance_funding_ETHUSDT.csv",
            "calc_time,rate\n500,0.1\n100,0.2\n900,0.3\n",
        )
        self.assertEqual(self.mod._binance_stats("funding", "ETHUSDT"), (100, 900, 3))

    def test_kind_columns_are_not_swapped(self):
        # Same file carrying both timestamp columns: klines must read open_time,
        # funding must read calc_time. Guards the KIND_COL mapping directly.
        text = "open_time,calc_time\n10,700\n20,100\n30,900\n"
        self._write("binance_klines_X.csv", text)
        self._write("binance_funding_X.csv", text)
        self.assertEqual(self.mod._binance_stats("klines", "X"), (10, 30, 3))
        self.assertEqual(self.mod._binance_stats("funding", "X"), (100, 900, 3))

    def test_unsorted_rows_yield_min_max(self):
        self._write("binance_klines_Y.csv", "open_time\n5000\n10\n4200\n")
        self.assertEqual(self.mod._binance_stats("klines", "Y"), (10, 5000, 3))

    def test_header_only_panel_is_rejected_loudly(self):
        # No data rows must raise rather than silently returning a zero row
        # count with fabricated 0/0 boundaries.
        self._write("binance_klines_Z.csv", "open_time\n")
        with self.assertRaises(ValueError):
            self.mod._binance_stats("klines", "Z")


class CmStatsTests(_TempPanelsCase):
    def test_min_max_dates_and_row_count_skip_empty(self):
        text = "date,asset\n2023-01-01,a\n2024-06-15,b\n,empty\n2022-12-31,c\n"
        p = self._write("marketcap_panel.csv", text)
        d_first, d_last, sha, n = self.mod._cm_stats()
        self.assertEqual((d_first, d_last, n), ("2022-12-31", "2024-06-15", 3))
        self.assertEqual(sha, hashlib.sha256(p.read_bytes()).hexdigest())

    def test_sha256_is_over_raw_file_bytes(self):
        p = self.panels / "marketcap_panel.csv"
        p.write_bytes(b"date\n2023-01-01\n")
        _, _, sha, _ = self.mod._cm_stats()
        self.assertEqual(sha, hashlib.sha256(p.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()