"""Hermetic seam tests for scripts/fetch_coinmetrics_marketcap.py.

No network: urllib.request.urlopen and time.sleep are monkeypatched.

The module is a free-data-only Coin Metrics Community API fetcher. It had no
direct test references before this file. Covers the deterministic pure seams
(``sha256_bytes``, ``asset_metrics_url``), the ``fetch_json`` retry/error
branches (success, 400/403 free-tier no-retry, retryable 429/5xx exhaustion,
other non-retryable 4xx, URLError/TimeoutError/OSError exhaustion) and the
``fetch_asset_metric`` pagination/combined-hash/403-to-None logic.
"""
import importlib.util
import io
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "scripts" / "fetch_coinmetrics_marketcap.py"
spec = importlib.util.spec_from_file_location("fetch_coinmetrics_marketcap", SPEC)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class _JsonResp:
    def __init__(self, data: bytes):
        self._data = data

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _http_error(code, body=b""):
    def boom(req, timeout=None):
        raise HTTPError(req.full_url, code, "err", hdrs=None, fp=io.BytesIO(body))

    return boom


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


class AssetMetricsUrlTests(unittest.TestCase):
    def test_url_shape_without_start_time(self):
        url = mod.asset_metrics_url("btc", "CapMrktCurUSD")
        self.assertTrue(url.startswith(mod.BASE + "?"))
        self.assertIn("assets=btc", url)
        self.assertIn("metrics=CapMrktCurUSD", url)
        self.assertIn("frequency=1d", url)
        self.assertIn(f"end_time={mod.END}", url)
        self.assertNotIn("start_time=", url)

    def test_url_shape_with_start_time(self):
        url = mod.asset_metrics_url("eth", "CapMrktEstUSD", "2023-01-01")
        self.assertIn("assets=eth", url)
        self.assertIn("metrics=CapMrktEstUSD", url)
        self.assertIn("start_time=2023-01-01", url)

    def test_url_differs_by_asset_and_metric(self):
        u1 = mod.asset_metrics_url("btc", "CapMrktCurUSD")
        u2 = mod.asset_metrics_url("btc", "CapMrktEstUSD")
        u3 = mod.asset_metrics_url("eth", "CapMrktCurUSD")
        self.assertNotEqual(u1, u2)
        self.assertNotEqual(u1, u3)


class FetchJsonTests(unittest.TestCase):
    def test_success_returns_payload_and_sha(self):
        raw = b'{"data": [{"time": "2024-01-01"}], "next_page_url": null}'
        with mock.patch.object(mod.urllib.request, "urlopen", return_value=_JsonResp(raw)):
            with mock.patch.object(mod.time, "sleep"):
                payload, sha = mod.fetch_json("https://example/x")
        self.assertEqual(payload["data"], [{"time": "2024-01-01"}])
        self.assertEqual(sha, mod.sha256_bytes(raw))

    def test_400_raises_free_tier_without_retry(self):
        calls = []

        def boom(req, timeout=None):
            calls.append(1)
            raise HTTPError(req.full_url, 400, "bad", hdrs=None, fp=io.BytesIO(b"nope"))

        with mock.patch.object(mod.urllib.request, "urlopen", side_effect=boom):
            with mock.patch.object(mod.time, "sleep") as sl:
                with self.assertRaises(RuntimeError) as ctx:
                    mod.fetch_json("https://example/x")
        self.assertIn("free_tier_unavailable", str(ctx.exception))
        self.assertEqual(len(calls), 1)
        sl.assert_not_called()

    def test_403_raises_free_tier_without_retry(self):
        calls = []

        def boom(req, timeout=None):
            calls.append(1)
            raise HTTPError(req.full_url, 403, "forbidden", hdrs=None, fp=io.BytesIO(b"no"))

        with mock.patch.object(mod.urllib.request, "urlopen", side_effect=boom):
            with mock.patch.object(mod.time, "sleep") as sl:
                with self.assertRaises(RuntimeError) as ctx:
                    mod.fetch_json("https://example/x")
        self.assertIn("free_tier_unavailable", str(ctx.exception))
        self.assertEqual(len(calls), 1)
        sl.assert_not_called()

    def test_non_retryable_4xx_raises_immediately(self):
        calls = []

        def boom(req, timeout=None):
            calls.append(1)
            raise HTTPError(req.full_url, 404, "nf", hdrs=None, fp=io.BytesIO(b""))

        with mock.patch.object(mod.urllib.request, "urlopen", side_effect=boom):
            with mock.patch.object(mod.time, "sleep") as sl:
                with self.assertRaises(RuntimeError) as ctx:
                    mod.fetch_json("https://example/x")
        self.assertIn("non-retryable", str(ctx.exception))
        self.assertEqual(len(calls), 1)
        sl.assert_not_called()

    def test_retryable_5xx_retries_then_exhausts(self):
        for code in (429, 502, 503, 504):
            with self.subTest(code=code):
                calls = []

                def boom(req, timeout=None, _c=code):
                    calls.append(1)
                    raise HTTPError(req.full_url, _c, "busy", hdrs=None, fp=io.BytesIO(b""))

                with mock.patch.object(mod.urllib.request, "urlopen", side_effect=boom):
                    with mock.patch.object(mod.time, "sleep") as sl:
                        with self.assertRaises(RuntimeError) as ctx:
                            mod.fetch_json("https://example/x")
                self.assertIn("exhausted retries", str(ctx.exception))
                self.assertEqual(len(calls), mod.MAX_RETRIES)
                self.assertEqual(sl.call_count, mod.MAX_RETRIES)

    def test_url_error_retries_then_exhausts(self):
        calls = []

        def boom(req, timeout=None):
            calls.append(1)
            raise URLError("down")

        with mock.patch.object(mod.urllib.request, "urlopen", side_effect=boom):
            with mock.patch.object(mod.time, "sleep") as sl:
                with self.assertRaises(RuntimeError) as ctx:
                    mod.fetch_json("https://example/x")
        self.assertIn("exhausted retries", str(ctx.exception))
        self.assertEqual(len(calls), mod.MAX_RETRIES)
        self.assertEqual(sl.call_count, mod.MAX_RETRIES)

    def test_timeout_error_retries_then_exhausts(self):
        calls = []

        def boom(req, timeout=None):
            calls.append(1)
            raise TimeoutError("slow")

        with mock.patch.object(mod.urllib.request, "urlopen", side_effect=boom):
            with mock.patch.object(mod.time, "sleep"):
                with self.assertRaises(RuntimeError) as ctx:
                    mod.fetch_json("https://example/x")
        self.assertIn("exhausted retries", str(ctx.exception))
        self.assertEqual(len(calls), mod.MAX_RETRIES)

    def test_os_error_retries_then_exhausts(self):
        calls = []

        def boom(req, timeout=None):
            calls.append(1)
            raise OSError("io")

        with mock.patch.object(mod.urllib.request, "urlopen", side_effect=boom):
            with mock.patch.object(mod.time, "sleep"):
                with self.assertRaises(RuntimeError) as ctx:
                    mod.fetch_json("https://example/x")
        self.assertIn("exhausted retries", str(ctx.exception))
        self.assertEqual(len(calls), mod.MAX_RETRIES)


class FetchAssetMetricTests(unittest.TestCase):
    def test_single_page_returns_rows_and_sha(self):
        sha = "a" * 64
        payload = {"data": [{"time": "2024-01-01", "CapMrktCurUSD": "1"}]}
        with mock.patch.object(mod, "fetch_json", return_value=(payload, sha)) as fj:
            rows, combined = mod.fetch_asset_metric("btc", "CapMrktCurUSD")
        self.assertEqual(rows, payload["data"])
        self.assertEqual(combined, mod.sha256_bytes(sha.encode()))
        fj.assert_called_once()

    def test_multi_page_follows_next_page_url_and_combines_sha(self):
        sha1, sha2 = "a" * 64, "b" * 64
        page1 = {"data": [{"time": "2024-01-02"}], "next_page_url": "https://example/p2"}
        page2 = {"data": [{"time": "2024-01-01"}]}
        with mock.patch.object(
            mod, "fetch_json", side_effect=[(page1, sha1), (page2, sha2)]
        ) as fj:
            rows, combined = mod.fetch_asset_metric("btc", "CapMrktCurUSD")
        self.assertEqual(rows, [{"time": "2024-01-02"}, {"time": "2024-01-01"}])
        self.assertEqual(combined, mod.sha256_bytes((sha1 + sha2).encode()))
        self.assertEqual(fj.call_count, 2)
        # second call must use the next_page_url, not the original URL
        second_url = fj.call_args_list[1].args[0]
        self.assertEqual(second_url, "https://example/p2")

    def test_403_returns_none(self):
        with mock.patch.object(
            mod, "fetch_json", side_effect=RuntimeError("free_tier_unavailable HTTP 403: x")
        ):
            self.assertIsNone(mod.fetch_asset_metric("btc", "CapMrktCurUSD"))

    def test_http_403_message_returns_none(self):
        with mock.patch.object(mod, "fetch_json", side_effect=RuntimeError("HTTP 403 forbidden")):
            self.assertIsNone(mod.fetch_asset_metric("btc", "CapMrktCurUSD"))

    def test_other_runtime_error_propagates(self):
        with mock.patch.object(
            mod, "fetch_json", side_effect=RuntimeError("exhausted retries: down")
        ):
            with self.assertRaises(RuntimeError):
                mod.fetch_asset_metric("btc", "CapMrktCurUSD")


class ConstantsTests(unittest.TestCase):
    def test_constants_present(self):
        self.assertEqual(mod.EXP, "HARMONY-CRYPTO-EDGE-004-DISPERSION-001")
        self.assertEqual(mod.START, "2023-01-01")
        self.assertEqual(mod.END, "2024-12-31")
        self.assertEqual(mod.METRICS, ["CapMrktCurUSD", "CapMrktEstUSD"])
        self.assertEqual(mod.FREQUENCY, "1d")
        self.assertEqual(mod.REQUEST_TIMEOUT, 30)
        self.assertEqual(mod.MAX_RETRIES, 6)
        self.assertEqual(mod.BACKOFF_BASE, 2.0)

    def test_assets_list_non_empty_and_lowercase(self):
        self.assertGreater(len(mod.ASSETS), 0)
        self.assertEqual(mod.ASSETS[0], "btc")
        for a in mod.ASSETS:
            self.assertEqual(a, a.lower())

    def test_base_url_is_https(self):
        self.assertTrue(mod.BASE.startswith("https://"))
        self.assertIn("community-api.coinmetrics.io", mod.BASE)


class MainTests(unittest.TestCase):
    def test_main_guarded(self):
        import inspect
        self.assertTrue(hasattr(mod, "main"))
        self.assertTrue(inspect.isfunction(mod.main))


if __name__ == "__main__":
    unittest.main()