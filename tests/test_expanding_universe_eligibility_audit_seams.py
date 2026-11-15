"""Hermetic unit tests for scripts/expanding_universe_eligibility_audit.py.

Gap: the H33 expanding-universe eligibility coverage audit is the only delivered
DISPERSION-003 integrity-audit script without any direct test coverage. Every
sibling audit (H29 grid_anchor_crosscheck, H30 grid_summary_ledger_crosscheck,
H32 grid_ledger_internal_consistency, H34 H10 fresh prereg-compliance) has a
``test_*_seams.py`` file, and the H10 fresh integrity audit (H31) does too. The
H33 script was only ever exercised as a one-shot CLI against the committed
panels, so its eligibility reconstruction, lifecycle derivation and loaders had
no regression guard.

These tests exercise every pure seam with synthetic frames/CSVs: no frozen
artifact, no network, no market data. They do not recompute or re-label any
market evidence; the committed H33 artifact remains the only audit evidence.
"""
from __future__ import annotations

import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "expanding_universe_eligibility_audit.py"


def _load():
    spec = importlib.util.spec_from_file_location(
        "expanding_universe_eligibility_audit_seams_test", SCRIPT
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


MOD = _load()


def _mc(rows):
    return pd.DataFrame(rows, columns=["date", "asset", "CapMrktEstUSD"])


def _px(dates, close=100.0):
    return pd.DataFrame({"date": list(dates), "close": [close] * len(dates)})


class NowUtcTests(unittest.TestCase):
    def test_format(self):
        import re

        self.assertRegex(MOD.now_utc(), r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class Sha256FileTests(unittest.TestCase):
    def test_known_content(self):
        import hashlib

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "f.bin"
            p.write_bytes(b"abc")
            self.assertEqual(
                MOD.sha256_file(p), hashlib.sha256(b"abc").hexdigest()
            )

    def test_missing_file_raises(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                MOD.sha256_file(Path(td) / "nope.bin")


class BuildEligibilityMapTests(unittest.TestCase):
    def test_basic_eligibility(self):
        mc = _mc([
            ("2023-01-01", "btc", 100.0),
            ("2023-01-01", "eth", 50.0),
            ("2023-01-02", "btc", 110.0),
            ("2023-01-02", "eth", 50.0),
        ])
        px = {
            "BTCUSDT": _px(["2023-01-01", "2023-01-02"]),
            "ETHUSDT": _px(["2023-01-01", "2023-01-02"]),
        }
        em = MOD.build_eligibility_map(mc, px)
        self.assertEqual(set(em), {"2023-01-01", "2023-01-02"})
        self.assertEqual(em["2023-01-01"], {"btc": 100.0, "eth": 50.0})
        self.assertEqual(em["2023-01-02"], {"btc": 110.0, "eth": 50.0})

    def test_asset_without_usdt_symbol_excluded(self):
        mc = _mc([
            ("2023-01-01", "btc", 100.0),
            ("2023-01-01", "xyz", 10.0),  # no XYZUSDT
        ])
        px = {"BTCUSDT": _px(["2023-01-01"])}
        em = MOD.build_eligibility_map(mc, px)
        self.assertEqual(em, {"2023-01-01": {"btc": 100.0}})

    def test_asset_without_price_on_date_excluded(self):
        mc = _mc([
            ("2023-01-01", "btc", 100.0),
            ("2023-01-02", "btc", 110.0),
        ])
        # BTCUSDT has no price on 2023-01-02 -> not eligible that date.
        px = {"BTCUSDT": _px(["2023-01-01"])}
        em = MOD.build_eligibility_map(mc, px)
        self.assertEqual(em, {"2023-01-01": {"btc": 100.0}})

    def test_nan_cap_excluded(self):
        mc = _mc([
            ("2023-01-01", "btc", 100.0),
            ("2023-01-01", "eth", float("nan")),
        ])
        px = {
            "BTCUSDT": _px(["2023-01-01"]),
            "ETHUSDT": _px(["2023-01-01"]),
        }
        em = MOD.build_eligibility_map(mc, px)
        self.assertEqual(em, {"2023-01-01": {"btc": 100.0}})

    def test_non_usdt_symbol_ignored(self):
        mc = _mc([("2023-01-01", "eth", 50.0)])
        # Only an ETHBTC pair exists -> eth has no USDT contract.
        px = {"ETHBTC": _px(["2023-01-01"])}
        em = MOD.build_eligibility_map(mc, px)
        self.assertEqual(em, {})

    def test_date_with_no_eligible_assets_omitted(self):
        mc = _mc([("2023-01-01", "zzz", 1.0)])  # no contract
        px = {"BTCUSDT": _px(["2023-01-01"])}
        em = MOD.build_eligibility_map(mc, px)
        self.assertEqual(em, {})

    def test_cap_preserved_as_float(self):
        mc = _mc([("2023-01-01", "btc", 100)])
        px = {"BTCUSDT": _px(["2023-01-01"])}
        em = MOD.build_eligibility_map(mc, px)
        self.assertIsInstance(em["2023-01-01"]["btc"], float)
        self.assertEqual(em["2023-01-01"]["btc"], 100.0)


class ComputeLifecycleTests(unittest.TestCase):
    def test_listing_and_delisting_from_price_dates(self):
        px = {"BTCUSDT": _px(["2023-01-03", "2023-01-01", "2023-01-02"])}
        lc = MOD.compute_lifecycle(px)
        self.assertEqual(
            lc["btc"], {"listing_date": "2023-01-01", "delisting_date": "2023-01-03"}
        )

    def test_non_usdt_symbol_ignored(self):
        px = {"ETHBTC": _px(["2023-01-01"])}
        self.assertEqual(MOD.compute_lifecycle(px), {})

    def test_empty_frame_omitted(self):
        px = {"BTCUSDT": _px([])}
        self.assertEqual(MOD.compute_lifecycle(px), {})

    def test_single_date_listing_equals_delisting(self):
        px = {"BTCUSDT": _px(["2023-01-01"])}
        lc = MOD.compute_lifecycle(px)
        self.assertEqual(lc["btc"]["listing_date"], "2023-01-01")
        self.assertEqual(lc["btc"]["delisting_date"], "2023-01-01")


class LoadMarketcapTests(unittest.TestCase):
    def test_loads_slices_and_drops_nan(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "marketcap_panel.csv"
            p.write_text(
                "date,asset,CapMrktCurUSD,CapMrktEstUSD\n"
                "2023-01-01T00:00:00Z,btc,1000,100\n"
                "2023-01-01T00:00:00Z,eth,500,\n"
                "2023-01-02T00:00:00Z,btc,1100,110\n",
                encoding="utf-8",
            )
            old = MOD.PANEL_DIR
            MOD.PANEL_DIR = Path(td)
            try:
                df = MOD.load_marketcap()
            finally:
                MOD.PANEL_DIR = old
        self.assertEqual(list(df.columns), ["date", "asset", "CapMrktEstUSD"])
        self.assertEqual(set(df["date"]), {"2023-01-01", "2023-01-02"})
        # eth row dropped (NaN cap)
        self.assertEqual(set(df["asset"]), {"btc"})
        self.assertEqual(float(df.iloc[0]["CapMrktEstUSD"]), 100.0)


class LoadBinancePanelTests(unittest.TestCase):
    def test_klines(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "binance_klines_BTCUSDT.csv"
            # 2023-01-01T00:00:00Z in ms
            p.write_text(
                "open_time,close\n1672531200000,100.5\n", encoding="utf-8"
            )
            old = MOD.PANEL_DIR
            MOD.PANEL_DIR = Path(td)
            try:
                out = MOD.load_binance_panel("klines")
            finally:
                MOD.PANEL_DIR = old
        self.assertIn("BTCUSDT", out)
        df = out["BTCUSDT"]
        self.assertEqual(list(df.columns), ["date", "close"])
        self.assertEqual(df.iloc[0]["date"], "2023-01-01")
        self.assertEqual(float(df.iloc[0]["close"]), 100.5)

    def test_funding(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "binance_funding_BTCUSDT.csv"
            p.write_text(
                "calc_time,last_funding_rate\n1672531200000,0.0001\n",
                encoding="utf-8",
            )
            old = MOD.PANEL_DIR
            MOD.PANEL_DIR = Path(td)
            try:
                out = MOD.load_binance_panel("funding")
            finally:
                MOD.PANEL_DIR = old
        self.assertIn("BTCUSDT", out)
        df = out["BTCUSDT"]
        self.assertEqual(list(df.columns), ["date", "funding_rate"])
        self.assertEqual(df.iloc[0]["date"], "2023-01-01")
        self.assertAlmostEqual(float(df.iloc[0]["funding_rate"]), 0.0001)

    def test_no_files_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            old = MOD.PANEL_DIR
            MOD.PANEL_DIR = Path(td)
            try:
                self.assertEqual(MOD.load_binance_panel("klines"), {})
            finally:
                MOD.PANEL_DIR = old


class MainWiringTests(unittest.TestCase):
    """Exercise main()'s I/O/CLI wiring with synthetic panels + ledger.

    The production PASS path depends on the four frozen artifact hashes, which
    are only reproducible against the committed artifacts (verified separately
    by the real H33 audit artifact). Here we point ART at an empty temp dir so
    every frozen hash is MISSING, which must make the audit FAIL (rc 1) while
    still writing a well-formed artifact and computing the ledger comparison.
    """

    def _synthetic_ledger(self):
        return {
            "cells": {
                "H004V106": {
                    "parameters": {"universe_arm": "expanding_point_in_time"},
                    "formations": [
                        {"formation_date": "2023-01-01"},
                        {"formation_date": "2023-01-02"},
                    ],
                    "eligible_assets_per_date": {"mean": 2.0, "min": 2, "max": 2},
                }
            }
        }

    def test_main_fail_when_frozen_hashes_missing(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            panels = td / "panels"
            panels.mkdir()
            (panels / "marketcap_panel.csv").write_text(
                "date,asset,CapMrktCurUSD,CapMrktEstUSD\n"
                "2023-01-01,btc,1000,100\n"
                "2023-01-01,eth,500,50\n"
                "2023-01-02,btc,1100,110\n"
                "2023-01-02,eth,500,50\n",
                encoding="utf-8",
            )
            (panels / "binance_klines_BTCUSDT.csv").write_text(
                "open_time,close\n1672531200000,100\n", encoding="utf-8"
            )
            (panels / "binance_klines_ETHUSDT.csv").write_text(
                "open_time,close\n1672531200000,50\n", encoding="utf-8"
            )
            ledger_path = td / "ledger.json"
            ledger_path.write_text(json.dumps(self._synthetic_ledger()))

            old = (MOD.PANEL_DIR, MOD.LEDGER_PATH, MOD.AUDIT_DIR, MOD.ART, MOD.ROOT)
            MOD.PANEL_DIR = panels
            MOD.LEDGER_PATH = ledger_path
            MOD.AUDIT_DIR = td / "audit"
            MOD.AUDIT_DIR.mkdir()
            MOD.ART = td / "empty_art"
            MOD.ART.mkdir()
            MOD.ROOT = td
            try:
                rc = MOD.main()
            finally:
                (MOD.PANEL_DIR, MOD.LEDGER_PATH, MOD.AUDIT_DIR, MOD.ART, MOD.ROOT) = old

            self.assertEqual(rc, 1)
            written = list((td / "audit").glob("*.json"))
            self.assertEqual(len(written), 1)
            report = json.loads(written[0].read_text(encoding="utf-8"))
            self.assertEqual(report["hypothesis"], "H33")
            self.assertEqual(report["status"], "EXPLORATORY_ONLY")
            self.assertFalse(report["all_frozen_hashes_match"])
            self.assertFalse(report["audit_pass"])
            # Comparison against the synthetic ledger should still be consistent.
            self.assertEqual(len(report["ledger_comparison"]), 1)
            self.assertTrue(
                report["ledger_comparison"][0]["consistency"]["overall_ok"]
            )


class ConstantsTests(unittest.TestCase):
    def test_legacy_universe(self):
        self.assertEqual(len(MOD.LEGACY_ASSETS), 28)
        self.assertIn("btc", MOD.LEGACY_ASSETS)
        self.assertIn("eth", MOD.LEGACY_ASSETS)

    def test_paths(self):
        self.assertEqual(MOD.EXP, "HARMONY-CRYPTO-EDGE-004-DISPERSION-003")
        self.assertEqual(MOD.LEDGER_PATH.name, "grid_result_ledger.json")


if __name__ == "__main__":
    unittest.main()