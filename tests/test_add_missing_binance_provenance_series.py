"""Hermetic unit tests for scripts.add_missing_binance_provenance_series.

Covers the script's pure, deterministic seam: computing which binance series in
binance_panel_manifest.json are absent from data_refresh_provenance.json and
appending exactly the identity/boundary fields (asset, symbol, kind,
date_first, date_last, rows) for each missing series, idempotently.

No network access, no dependency on committed panel artifacts, no frozen
artifact or config reads/writes. Synthetic fixtures under tmp_path are software
tests only, never market evidence.
"""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "add_missing_binance_provenance_series.py"


def _load():
    spec = importlib.util.spec_from_file_location("add_missing_binance_provenance_series_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _write_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _prov(series):
    return {"binance": {"series": list(series)}}


def _manifest(series):
    return {"series": list(series)}


class TestAddMissingBinanceProvenanceSeries(unittest.TestCase):
    def setUp(self):
        self.mod = _load()
        self.tmp = Path(__file__).with_suffix(".tmp")  # placeholder, replaced per test

    def _run_main(self, prov, manifest):
        prov_path = Path("/tmp/add_missing_series_prov_test.json")
        man_path = Path("/tmp/add_missing_series_man_test.json")
        _write_json(prov_path, prov)
        _write_json(man_path, manifest)
        with patch.object(self.mod, "PROVENANCE", prov_path), patch.object(
            self.mod, "MANIFEST", man_path
        ):
            return self.mod.main(), prov_path


class ModuleConstantsTests(TestAddMissingBinanceProvenanceSeries):
    def test_experiment_id(self):
        self.assertEqual(
            self.mod.EXP, "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
        )

    def test_path_constants_under_disp003_panels(self):
        self.assertTrue(
            str(self.mod.PANELS).endswith(
                "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels"
            )
        )
        self.assertEqual(
            self.mod.PROVENANCE, self.mod.PANELS / "data_refresh_provenance.json"
        )
        self.assertEqual(
            self.mod.MANIFEST, self.mod.PANELS / "binance_panel_manifest.json"
        )


class MainBehaviorTests(TestAddMissingBinanceProvenanceSeries):
    BASE_PROV = _prov(
        [
            {
                "asset": "BTC",
                "symbol": "BTCUSDT",
                "kind": "klines",
                "date_first": "2023-01-01",
                "date_last": "2026-10-31",
                "rows": 1200,
            }
        ]
    )
    BASE_MAN = _manifest(
        [
            {
                "asset": "BTC",
                "symbol": "BTCUSDT",
                "kind": "klines",
                "date_first": "2023-01-01",
                "date_last": "2026-10-31",
                "rows": 1200,
                "months_ok": 10,
                "raw_dir": "raw/binance/klines/BTCUSDT",
            },
            {
                "asset": "ETH",
                "symbol": "ETHUSDT",
                "kind": "klines",
                "date_first": "2023-01-01",
                "date_last": "2026-09-30",
                "rows": 990,
            },
            {
                "asset": "BTC",
                "symbol": "BTCUSDT",
                "kind": "funding",
                "date_first": "2023-01-01",
                "date_last": "2026-09-29",
                "rows": 990,
            },
        ]
    )

    def test_main_returns_zero(self):
        _, prov_path = self._run_main(self.BASE_PROV, self.BASE_MAN)
        self.assertTrue(prov_path.exists())

    def test_adds_exactly_the_missing_series(self):
        _, prov_path = self._run_main(self.BASE_PROV, self.BASE_MAN)
        prov = json.loads(prov_path.read_text(encoding="utf-8"))
        series = prov["binance"]["series"]
        self.assertEqual(len(series), 3)
        # original entry preserved exactly
        self.assertEqual(series[0], self.BASE_PROV["binance"]["series"][0])
        # missing entries appended in sorted kind:symbol order
        self.assertEqual(series[1]["kind"], "funding")
        self.assertEqual(series[1]["symbol"], "BTCUSDT")
        self.assertEqual(series[2]["kind"], "klines")
        self.assertEqual(series[2]["symbol"], "ETHUSDT")
        for entry in series[1:]:
            self.assertEqual(
                set(entry),
                {"asset", "symbol", "kind", "date_first", "date_last", "rows"},
            )

    def test_manifest_extra_fields_are_stripped(self):
        _, prov_path = self._run_main(self.BASE_PROV, self.BASE_MAN)
        prov = json.loads(prov_path.read_text(encoding="utf-8"))
        eth = [s for s in prov["binance"]["series"] if s["symbol"] == "ETHUSDT"][0]
        self.assertNotIn("months_ok", eth)
        self.assertNotIn("raw_dir", eth)
        self.assertEqual(eth["date_first"], "2023-01-01")

    def test_idempotent_second_run_adds_nothing(self):
        _, prov_path = self._run_main(self.BASE_PROV, self.BASE_MAN)
        first = json.loads(prov_path.read_text(encoding="utf-8"))["binance"]["series"]
        man_path = Path("/tmp/add_missing_series_man_test.json")
        with patch.object(self.mod, "PROVENANCE", prov_path), patch.object(
            self.mod, "MANIFEST", man_path
        ):
            self.mod.main()
        second = json.loads(prov_path.read_text(encoding="utf-8"))["binance"]["series"]
        self.assertEqual(len(first), len(second))
        self.assertEqual(first, second)

    def test_no_missing_when_fully_covered(self):
        covered = _prov(self.BASE_MAN["series"])
        _, prov_path = self._run_main(covered, self.BASE_MAN)
        prov = json.loads(prov_path.read_text(encoding="utf-8"))
        self.assertEqual(len(prov["binance"]["series"]), 3)

    def test_empty_manifest_adds_nothing(self):
        _, prov_path = self._run_main(self.BASE_PROV, _manifest([]))
        prov = json.loads(prov_path.read_text(encoding="utf-8"))
        self.assertEqual(len(prov["binance"]["series"]), 1)
        self.assertEqual(prov["binance"]["series"][0], self.BASE_PROV["binance"]["series"][0])

    def test_written_file_is_deterministic_json(self):
        _, prov_path = self._run_main(self.BASE_PROV, self.BASE_MAN)
        text = prov_path.read_text(encoding="utf-8")
        self.assertTrue(text.endswith("\n"))
        reparsed = json.loads(text)
        self.assertEqual(reparsed, json.loads(prov_path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
