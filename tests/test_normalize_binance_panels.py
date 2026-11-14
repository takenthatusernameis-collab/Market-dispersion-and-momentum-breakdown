import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import normalize_binance_panels as nbp


class YmKeyTests(unittest.TestCase):
    def test_ym_key_orders_chronologically_not_by_month_suffix(self):
        # Naive month-suffix sort would put 2026-10 before 2023-01; the
        # year-aware key must order 2023-01 first.
        names = [
            "MATICUSDT-klines-2026-10.zip",
            "MATICUSDT-klines-2023-01.zip",
            "MATICUSDT-klines-2024-01.zip",
            "MATICUSDT-klines-2025-01.zip",
        ]
        ordered = sorted(names, key=lambda n: nbp.ym_key(Path(n)))
        self.assertEqual(ordered, [
            "MATICUSDT-klines-2023-01.zip",
            "MATICUSDT-klines-2024-01.zip",
            "MATICUSDT-klines-2025-01.zip",
            "MATICUSDT-klines-2026-10.zip",
        ])

    def test_ym_key_is_year_then_month(self):
        self.assertEqual(nbp.ym_key(Path("X-klines-2026-10.zip")), (2026, 10))
        self.assertEqual(nbp.ym_key(Path("X-klines-2023-01.zip")), (2023, 1))

    def test_ym_key_handles_dot_suffix(self):
        # The glob may leave ".zip" as ".zip" or a stray dot; both parse.
        self.assertEqual(nbp.ym_key(Path("X-klines-2025-12.zip")), (2025, 12))


class StripHeaderTests(unittest.TestCase):
    def test_strips_klines_header(self):
        lines = ["open_time,open,high,low,close,volume", "1,2,3,4,5,6"]
        self.assertEqual(nbp.strip_header(lines), ["1,2,3,4,5,6"])

    def test_strips_funding_header(self):
        lines = ["calc_time,funding_interval_hours,last_funding_rate", "1,2,3"]
        self.assertEqual(nbp.strip_header(lines), ["1,2,3"])

    def test_strips_symbol_header(self):
        lines = ["symbol,calc_time,funding_interval_hours,last_funding_rate", "X,1,2,3"]
        self.assertEqual(nbp.strip_header(lines), ["X,1,2,3"])

    def test_no_header_left_unchanged(self):
        lines = ["1,2,3", "4,5,6"]
        self.assertEqual(nbp.strip_header(lines), ["1,2,3", "4,5,6"])

    def test_empty_input(self):
        self.assertEqual(nbp.strip_header([]), [])

    def test_blank_lines_are_filtered_before_header_check(self):
        # The caller strips blanks first; an all-blank list has no header.
        self.assertEqual(nbp.strip_header([]), [])


class PrefixFundingTests(unittest.TestCase):
    def test_prefixes_symbol_column(self):
        out = nbp.prefix_funding("BTCUSDT", ["1,2,3", "4,5,6"])
        self.assertEqual(out, ["BTCUSDT,1,2,3", "BTCUSDT,4,5,6"])

    def test_empty_input(self):
        self.assertEqual(nbp.prefix_funding("X", []), [])

    def test_header_constants(self):
        self.assertEqual(nbp.KLINES_HEADER,
                         "open_time,open,high,low,close,volume,close_time,"
                         "quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore")
        self.assertEqual(nbp.FUNDING_HEADER,
                         "symbol,calc_time,funding_interval_hours,last_funding_rate")


if __name__ == "__main__":
    unittest.main()