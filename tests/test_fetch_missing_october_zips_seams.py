"""Hermetic seam tests for scripts/fetch_missing_october_zips.py.

No network: urlopen, time.sleep, and filesystem roots are monkeypatched.
Covers deterministic URL construction/selection logic inside fetch_missing,
http_get retry/error branches, and fetch_missing idempotency/reporting.
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
SPEC = ROOT / "scripts" / "fetch_missing_october_zips.py"
spec = importlib.util.spec_from_file_location("fetch_missing_october_zips", SPEC)
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


class HttpGetTests(unittest.TestCase):
    def test_success_returns_bytes_and_code(self):
        with mock.patch.object(mod, "urlopen", return_value=_Resp(b"abc", 200)):
            with mock.patch.object(mod.time, "sleep"):
                data, status, err = mod.http_get("https://example/x")
        self.assertEqual(data, b"abc")
        self.assertEqual(status, 200)
        self.assertIsNone(err)

    def test_404_returns_none_without_retry(self):
        calls = []
        def boom(req, timeout=None):
            calls.append(1)
            raise HTTPError(req.full_url, 404, "nf", hdrs=None, fp=io.BytesIO(b""))
        with mock.patch.object(mod, "urlopen", side_effect=boom):
            with mock.patch.object(mod.time, "sleep") as sl:
                data, status, err = mod.http_get("https://example/x")
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
                data, status, err = mod.http_get("https://example/x")
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
                data, status, err = mod.http_get("https://example/x")
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
                data, status, err = mod.http_get("https://example/x")
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
                data, status, err = mod.http_get("https://example/x")
        self.assertIsNone(data)
        self.assertIsNone(status)
        self.assertIn("TimeoutError", err)
        self.assertEqual(len(calls), mod.MAX_RETRIES)


class FetchMissingTests(unittest.TestCase):
    def _run(self, tmp, http_side_effect, existing=None):
        existing = existing or set()
        root = Path(tmp)
        # seed existing files to test idempotency
        for rel in existing:
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"old")

        def fake_http_get(url):
            return http_side_effect(url)

        with mock.patch.object(mod, "ROOT", root), \
             mock.patch.object(mod, "SYMBOLS", ["BTCUSDT", "ETHUSDT"]), \
             mock.patch.object(mod, "SLEEP_BETWEEN", 0), \
             mock.patch.object(mod, "http_get", side_effect=fake_http_get), \
             mock.patch.object(mod.time, "sleep"):
            buf = io.StringIO()
            with mock.patch("sys.stdout", buf):
                rc = mod.fetch_missing("EXP")
        return rc, buf.getvalue(), root

    def test_fetches_missing_and_writes_verbatim(self):
        seen = []
        def side(url):
            seen.append(url)
            return b"zipbytes-" + url.encode()[-8:], 200, None
        rc, out, root = self._run(tempfile.mkdtemp(), side)
        self.assertEqual(rc, 0)
        # 2 symbols * 2 kinds = 4
        self.assertEqual(len(seen), 4)
        k = root / "artifacts/EXP/data/raw/binance/klines/BTCUSDT/BTCUSDT-klines-2026-10.zip"
        f = root / "artifacts/EXP/data/raw/binance/funding/BTCUSDT/BTCUSDT-funding-2026-10.zip"
        self.assertTrue(k.exists())
        self.assertTrue(f.exists())
        self.assertTrue(k.read_bytes().startswith(b"zipbytes-"))
        self.assertIn("downloaded 4 missing", out)
        self.assertNotIn("still missing", out)
        # URL shapes
        self.assertTrue(any("/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2026-10.zip" in u for u in seen))
        self.assertTrue(any("/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-2026-10.zip" in u for u in seen))

    def test_skips_existing_files(self):
        seen = []
        def side(url):
            seen.append(url)
            return b"new", 200, None
        existing = {"artifacts/EXP/data/raw/binance/klines/BTCUSDT/BTCUSDT-klines-2026-10.zip"}
        rc, out, root = self._run(tempfile.mkdtemp(), side, existing=existing)
        self.assertEqual(rc, 0)
        # existing kline not re-fetched
        self.assertEqual(len(seen), 3)
        kept = root / existing.pop()
        self.assertEqual(kept.read_bytes(), b"old")

    def test_reports_still_missing_but_returns_zero(self):
        def side(url):
            if "ETHUSDT" in url and "fundingRate" in url:
                return None, 404, "404_not_found"
            return b"ok", 200, None
        rc, out, root = self._run(tempfile.mkdtemp(), side)
        self.assertEqual(rc, 0)
        self.assertIn("downloaded 3 missing", out)
        self.assertIn("still missing (1)", out)
        self.assertIn("ETHUSDT/funding(404)", out)
        # other three written
        self.assertTrue((root / "artifacts/EXP/data/raw/binance/klines/ETHUSDT/ETHUSDT-klines-2026-10.zip").exists())

    def test_all_missing_returns_zero_and_lists_all(self):
        def side(url):
            return None, 404, "404_not_found"
        rc, out, root = self._run(tempfile.mkdtemp(), side)
        self.assertEqual(rc, 0)
        self.assertIn("downloaded 0 missing", out)
        self.assertIn("still missing (4)", out)


class ConstantsTests(unittest.TestCase):
    def test_target_and_archive_constants(self):
        self.assertEqual(mod.TARGET_YM, "2026-10")
        self.assertTrue(mod.ARCHIVE.startswith("https://"))
        self.assertIn("data.binance.vision", mod.ARCHIVE)
        self.assertEqual(len(mod.SYMBOLS), 32)
        self.assertIn("BTCUSDT", mod.SYMBOLS)
        self.assertIn("MATICUSDT", mod.SYMBOLS)

    def test_main_uses_default_experiment(self):
        with mock.patch.object(mod, "fetch_missing", return_value=0) as fm:
            with mock.patch.object(sys, "argv", ["prog"]):
                rc = mod.main()
        self.assertEqual(rc, 0)
        fm.assert_called_once_with("HARMONY-CRYPTO-EDGE-004-DISPERSION-003")

    def test_main_passes_experiment_arg(self):
        with mock.patch.object(mod, "fetch_missing", return_value=0) as fm:
            with mock.patch.object(sys, "argv", ["prog", "--experiment", "X"]):
                rc = mod.main()
        self.assertEqual(rc, 0)
        fm.assert_called_once_with("X")


if __name__ == "__main__":
    unittest.main()
