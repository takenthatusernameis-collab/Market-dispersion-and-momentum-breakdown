"""Hermetic unit tests for scripts.fix_funding_panel_rows.

Covers the pure, deterministic ``month_key(path: Path)`` seam. The committed
panels (e.g. binance_funding_BTCUSDT.csv, 4200 rows, 2023-01-01..2026-10-31,
strictly ascending by calc_time) are produced by an ascending month sort, so
the key must order by the full ``YYYY-MM`` token, not by the trailing ``MM``
alone: a stem like ``BTCUSDT-funding-2023-01.zip`` split on ``-`` yields
[..., "2023", "01"], and taking only the last element returns ``01`` for every
year's January, grouping 2023-01, 2024-01, 2025-01, 2026-01 together.

These tests exercise only the pure function against synthetic ``Path`` inputs:
no file reads, no network, no committed-panel dependency, no frozen artifact
reads/writes. Synthetic fixtures are software tests only, never market
evidence.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "fix_funding_panel_rows.py"


def _load():
    spec = importlib.util.spec_from_file_location("fix_funding_panel_rows_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class MonthKeyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_returns_full_yyyy_mm_token(self):
        self.assertEqual(
            self.mod.month_key(Path("BTCUSDT/BTCUSDT-funding-2023-01.zip")),
            "2023-01",
        )

    def test_full_path_object(self):
        self.assertEqual(
            self.mod.month_key(
                Path("/repo/artifacts/EXP/data/raw/binance/funding/BTCUSDT/BTCUSDT-funding-2023-02.zip")
            ),
            "2023-02",
        )

    def test_symbol_with_internal_dash_still_resolves_to_month(self):
        # A symbol containing a dash must not shift the month token: the key is
        # always the last two dash components of the stem.
        self.assertEqual(
            self.mod.month_key(Path("SOME-SYMBOLUSDT/SOME-SYMBOLUSDT-funding-2026-09.zip")),
            "2026-09",
        )

    def test_sort_key_is_chronological_across_years(self):
        """``sorted(zips, key=month_key)`` must order by full YYYY-MM.

        Sorting by the trailing ``MM`` alone would interleave years (2023-01,
        2024-01, 2025-01, 2026-01, 2023-02, ...). The correct order is
        chronological: 2023-01, 2023-12, 2024-01, 2025-02, 2026-01.
        """
        names = [
            "BTCUSDT-funding-2026-01.zip",
            "BTCUSDT-funding-2023-12.zip",
            "BTCUSDT-funding-2024-01.zip",
            "BTCUSDT-funding-2023-01.zip",
            "BTCUSDT-funding-2025-02.zip",
        ]
        ordered = sorted(
            (Path("BTCUSDT/" + n) for n in names), key=self.mod.month_key
        )
        self.assertEqual(
            [p.name for p in ordered],
            [
                "BTCUSDT-funding-2023-01.zip",
                "BTCUSDT-funding-2023-12.zip",
                "BTCUSDT-funding-2024-01.zip",
                "BTCUSDT-funding-2025-02.zip",
                "BTCUSDT-funding-2026-01.zip",
            ],
        )

    def test_naive_mm_only_key_gives_the_wrong_order(self):
        """Document the regression this seam guards against.

        The previous implementation returned ``path.stem.split("-")[-1]``
        (``MM`` only). Assert that the naive key disagrees with ``month_key``
        and produces the non-chronological order: every January (any year)
        sorts before 2023-12, so years interleave.
        """
        names = [
            "BTCUSDT-funding-2026-01.zip",
            "BTCUSDT-funding-2023-12.zip",
            "BTCUSDT-funding-2024-01.zip",
            "BTCUSDT-funding-2023-01.zip",
        ]

        def naive(path):
            return path.stem.split("-")[-1]

        naive_order = [
            p.name for p in sorted((Path("BTCUSDT/" + n) for n in names), key=naive)
        ]
        correct_order = [
            p.name for p in sorted((Path("BTCUSDT/" + n) for n in names), key=self.mod.month_key)
        ]
        self.assertNotEqual(naive_order, correct_order)
        # naive: every January precedes 2023-12 (years interleaved)
        dec_index = naive_order.index("BTCUSDT-funding-2023-12.zip")
        self.assertEqual(dec_index, 3)
        # correct: 2023-12 comes before 2024-01
        self.assertLess(
            correct_order.index("BTCUSDT-funding-2023-12.zip"),
            correct_order.index("BTCUSDT-funding-2024-01.zip"),
        )

    def test_module_constants(self):
        self.assertEqual(
            self.mod.FUNDING_HEADER,
            "symbol,calc_time,funding_interval_hours,last_funding_rate",
        )


if __name__ == "__main__":
    unittest.main()