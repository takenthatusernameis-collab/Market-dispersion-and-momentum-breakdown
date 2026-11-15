"""Hermetic seam tests for scripts/fetch_binance_data.py.

No network: urlopen, time.sleep, and filesystem roots are monkeypatched.
Covers deterministic URL construction, zip extraction, month iteration,
sha256_bytes, and fetch_bytes retry/error branches.
"""
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "scripts" / "fetch_binance_data.py"
spec = importlib.util.spec_from_file_location("fetch_binance_data", SPEC)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class _Resp:
    def __init__(self, data=b"x", code=200):
        self._data = data
        self._code = code

    def read(self):
        return self._data

    def getcode(self):
        return self._code

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Sha256BytesTests(unittest.TestCase):
    def test_sha256_bytes_known_value(self):
        data = b"hello world"
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        self.assertEqual(mod.sha256_bytes(data), expected)

    def test_sha256_bytes_empty(self):
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        self.assertEqual(mod.sha256_bytes(b""), expected)

    def test_sha256_bytes_different_inputs_different_hashes(self):
        self.assertNotEqual(mod.sha256_bytes(b"a"), mod.sha256_bytes(b"b"))


class MonthIterTests(unittest.TestCase):
    def test_month_iter_single_month(self):
        months = list(mod.month_iter("2023-01", "2023-01"))
        self.assertEqual(months, ["2023-01"])

    def test_month_iter_multiple_months(self):
        months = list(mod.month_iter("2023-01", "2023-03"))
        self.assertEqual(months, ["2023-01", "2023-02", "2023-03"])

    def test_month_iter_year_boundary(self):
        months = list(mod.month_iter("2023-11", "2024-01"))
        self.assertEqual(months, ["2023-11", "2023-12", "2024-01"])

    def test_month_iter_long_range(self):
        months = list(mod.month_iter("2020-01", "2020-12"))
        self.assertEqual(len(months), 12)
        self.assertEqual(months[0], "2020-01")
        self.assertEqual(months[-1], "2020-12")


class ExtractCsvTests(unittest.TestCase):
    def test_extract_csv_valid_zip(self):
        import zipfile
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("data.csv", "header\nrow1\nrow2\n")
        data = buf.getvalue()
        result = mod.extract_csv(data)
        self.assertIsNotNone(result)
        self.assertIn("header", result)
        self.assertIn("row1", result)
        self.assertIn("row2", result)

    def test_extract_csv_no_csv_in_zip(self):
        import zipfile
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("data.txt", "not a csv")
        data = buf.getvalue()
        self.assertIsNone(mod.extract_csv(data))

    def test_extract_csv_bad_zip(self):
        self.assertIsNone(mod.extract_csv(b"not a zip file"))

    def test_extract_csv_empty_zip(self):
        import zipfile
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            pass
        data = buf.getvalue()
        self.assertIsNone(mod.extract_csv(data))


class UrlConstructionTests(unittest.TestCase):
    def test_kline_url_shape(self):
        url = mod.kline_url("BTCUSDT", "2023-01")
        self.assertIn("data.binance.vision", url)
        self.assertIn("BTCUSDT", url)
        self.assertIn("1d", url)
        self.assertIn("2023-01", url)
        self.assertTrue(url.endswith("BTCUSDT-1d-2023-01.zip"))

    def test_funding_url_shape(self):
        url = mod.funding_url("BTCUSDT", "2023-01")
        self.assertIn("data.binance.vision", url)
        self.assertIn("BTCUSDT", url)
        self.assertIn("fundingRate", url)
        self.assertIn("2023-01", url)
        self.assertTrue(url.endswith("BTCUSDT-fundingRate-2023-01.zip"))

    def test_kline_url_different_symbols(self):
        url1 = mod.kline_url("BTCUSDT", "2023-01")
        url2 = mod.kline_url("ETHUSDT", "2023-01")
        self.assertNotEqual(url1, url2)
        self.assertIn("BTCUSDT", url1)
        self.assertIn("ETHUSDT", url2)

    def test_funding_url_different_symbols(self):
        url1 = mod.funding_url("BTCUSDT", "2023-01")
        url2 = mod.funding_url("ETHUSDT", "2023-01")
        self.assertNotEqual(url1, url2)
        self.assertIn("BTCUSDT", url1)
        self.assertIn("ETHUSDT", url2)


class FetchBytesTests(unittest.TestCase):
    def test_success_returns_bytes_and_code(self):
        with mock.patch.object(mod, "urlopen", return_value=_Resp(b"abc", 200)):
            with mock.patch.object(mod.time, "sleep"):
                data, status, err = mod.fetch_bytes("https://example/x")
        self.assertEqual(data, b"abc")
        self.assertEqual(status, 200)
        self.assertEqual(err, mod.sha256_bytes(b"abc"))

    def test_404_returns_none_without_retry(self):
        calls = []

        def boom(req, timeout=None):
            calls.append(1)
            raise HTTPError(req.full_url, 404, "nf", hdrs=None, fp=io.BytesIO(b""))

        with mock.patch.object(mod, "urlopen", side_effect=boom):
            with mock.patch.object(mod.time, "sleep") as sl:
                data, status, err = mod.fetch_bytes("https://example/x")
        self.assertIsNone(data)
        self.assertEqual(status, 404)
        self.assertEqual(err, "404_not_found")
        self.assertEqual(len(calls), 1)
        sl.assert_not_called()

    def test_non_retryable_http_error_returns_immediately(self):
        def boom(req, timeout=None):
            raise HTTPError(req.full_url, 403, "forbidden", hdrs=None, fp=io.BytesIO(b""))

        with mock.patch.object(mod, "urlopen", side_effect=boom):
            with mock.patch.object(mod.time, "sleep") as sl:
                data, status, err = mod.fetch_bytes("https://example/x")
        self.assertIsNone(data)
        self.assertEqual(status, 403)
        self.assertEqual(err, "HTTP 403")
        sl.assert_not_called()

    def test_retryable_http_error_retries_then_fails(self):
        calls = []

        def boom(req, timeout=None):
            calls.append(1)
            raise HTTPError(req.full_url, 503, "busy", hdrs=None, fp=io.BytesIO(b""))

        with mock.patch.object(mod, "urlopen", side_effect=boom):
            with mock.patch.object(mod.time, "sleep") as sl:
                data, status, err = mod.fetch_bytes("https://example/x")
        self.assertIsNone(data)
        self.assertIsNone(status)
        self.assertEqual(err, "HTTP 503")
        self.assertEqual(len(calls), mod.MAX_RETRIES)
        self.assertEqual(sl.call_count, mod.MAX_RETRIES)

    def test_url_error_retries_then_exhausts(self):
        calls = []

        def boom(req, timeout=None):
            calls.append(1)
            raise URLError("down")

        with mock.patch.object(mod, "urlopen", side_effect=boom):
            with mock.patch.object(mod.time, "sleep"):
                data, status, err = mod.fetch_bytes("https://example/x")
        self.assertIsNone(data)
        self.assertIsNone(status)
        self.assertIn("URLError", err)
        self.assertEqual(len(calls), mod.MAX_RETRIES)

    def test_timeout_error_retries_then_exhausts(self):
        calls = []

        def boom(req, timeout=None):
            calls.append(1)
            raise TimeoutError("slow")

        with mock.patch.object(mod, "urlopen", side_effect=boom):
            with mock.patch.object(mod.time, "sleep"):
                data, status, err = mod.fetch_bytes("https://example/x")
        self.assertIsNone(data)
        self.assertIsNone(status)
        self.assertIn("TimeoutError", err)
        self.assertEqual(len(calls), mod.MAX_RETRIES)


class ConstantsTests(unittest.TestCase):
    def test_constants_present(self):
        self.assertEqual(mod.START_YM, "2020-01")
        self.assertEqual(mod.END_YM, "2024-12")
        self.assertEqual(mod.MAX_WORKERS, 1)
        self.assertEqual(mod.REQUEST_TIMEOUT, 60)
        self.assertEqual(mod.MAX_RETRIES, 4)
        self.assertEqual(mod.BACKOFF_BASE, 2.0)
        self.assertEqual(mod.SLEEP_BETWEEN, 0.35)

    def test_symbol_map_non_empty(self):
        self.assertGreater(len(mod.SYMBOL_MAP), 0)
        self.assertIn("btc", mod.SYMBOL_MAP)
        self.assertEqual(mod.SYMBOL_MAP["btc"], "BTCUSDT")

    def test_archive_url(self):
        self.assertTrue(mod.ARCHIVE.startswith("https://"))
        self.assertIn("data.binance.vision", mod.ARCHIVE)

    def test_headers_present(self):
        self.assertEqual(mod.KLINES_HEADER, "open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore")
        self.assertEqual(mod.FUNDING_HEADER, "symbol,calc_time,funding_interval_hours,last_funding_rate")


class MainTests(unittest.TestCase):
    def test_main_guarded(self):
        self.assertTrue(hasattr(mod, "main"))
        import inspect
        self.assertTrue(inspect.isfunction(mod.main))


if __name__ == "__main__":
    unittest.main()