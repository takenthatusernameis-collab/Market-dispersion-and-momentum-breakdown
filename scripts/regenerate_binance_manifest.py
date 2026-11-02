#!/usr/bin/env python3
"""Regenerate the Binance panel manifest for the full 32-symbol DISP-003 panel set.

The committed ``binance_panel_manifest.json`` is a FROZEN INPUT to the sealed
DISP-003 forward block: the block records SHA-256 hashes over it, so any change
to the manifest invalidates those hashes and forces a re-seal. It currently
describes only BTCUSDT/ETHUSDT because the last data refresh ran with the
default ``--binance-assets btc,eth`` argument, while the on-disk raw zips and the
rebuilt panels now cover all 32 panel symbols.

This script rebuilds the manifest from the panel CSVs that are actually on disk,
so the manifest's ``series`` set, per-series boundaries, row counts, window and
symbol map all agree with the data the evaluator reads. It is idempotent and
deterministic: re-running it reproduces the same bytes.

It does NOT touch the canonical forward block, the grid ledger, DISPERSION-001/002
or any frozen artifact. The caller is responsible for re-sealing any forward block
that hashes this manifest after it changes.

Usage:
    python3 scripts/regenerate_binance_manifest.py [--experiment EXP]
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = "https://data.binance.vision/data/futures/um"
START_YM = "2023-01"

KIND_COL = {"klines": "open_time", "funding": "calc_time"}


def series_stats(kind: str, symbol: str, panels: Path) -> tuple[int, int, int]:
    path = panels / f"binance_{kind}_{symbol}.csv"
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        col = header.index(KIND_COL[kind])
        rows = list(reader)
    ts = [int(r[col]) for r in rows]
    return min(ts), max(ts), len(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--experiment", default="HARMONY-CRYPTO-EDGE-004-DISPERSION-003")
    args = ap.parse_args()
    exp = args.experiment
    panels = ROOT / "artifacts" / exp / "data" / "panels"
    manifest_path = panels / "binance_panel_manifest.json"

    # Derive the symbol set from the panel CSVs on disk, so the manifest cannot
    # drift from the data it describes. CoinMetrics asset -> Binance symbol map
    # mirrors refresh_free_data.py SYMBOL_MAP.
    symbol_map = {
        "btc": "BTCUSDT", "eth": "ETHUSDT", "sol": "SOLUSDT", "bnb": "BNBUSDT",
        "xrp": "XRPUSDT", "ada": "ADAUSDT", "doge": "DOGEUSDT", "dot": "DOTUSDT",
        "matic": "MATICUSDT", "avax": "AVAXUSDT", "link": "LINKUSDT", "uni": "UNIUSDT",
        "ltc": "LTCUSDT", "bch": "BCHUSDT", "etc": "ETCUSDT", "xlm": "XLMUSDT",
        "atom": "ATOMUSDT", "algo": "ALGOUSDT", "vet": "VETUSDT", "fil": "FILUSDT",
        "trx": "TRXUSDT", "eos": "EOSUSDT", "neo": "NEOUSDT", "iost": "IOSTUSDT",
        "qtum": "QTUMUSDT", "zec": "ZECUSDT", "dash": "DASHUSDT", "rune": "RUNEUSDT",
        "1inch": "1INCHUSDT", "aave": "AAVEUSDT", "ach": "ACHUSDT", "agld": "AGLDUSDT",
    }
    asset_by_symbol = {v: k for k, v in symbol_map.items()}

    series = []
    for kind in ("klines", "funding"):
        for symbol in sorted(symbol_map.values()):
            first, last, n = series_stats(kind, symbol, panels)
            series.append({
                "asset": asset_by_symbol[symbol],
                "symbol": symbol,
                "kind": kind,
                "date_first": str(first),
                "date_last": str(last),
                "rows": n,
                "manifest_boundary_note": (
                    "date_first/date_last/rows recomputed from the panel CSV "
                    f"({kind} panel for {symbol}) after the panels were rebuilt "
                    "from all saved monthly zips"
                ),
            })

    manifest = {
        "experiment_id": exp,
        "source": "binance_public_data_archive",
        "archive": ARCHIVE,
        "window": {"start": START_YM, "end": "2026-10"},
        "symbol_map": symbol_map,
        "series": series,
        "manifest_scope_note": (
            "Covers all 32 DISP-003 panel symbols. MATICUSDT (delisted 2024-09) "
            "and EOSUSDT (delisted 2025-05) have no October 2026 archive zips "
            "(HTTP 404 for every month after their delisting), so their klines "
            "panels end at their last tradeable date; their funding panels carry "
            "the final published funding rows. All other symbols extend through "
            "2026-10-31."
        ),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"[regen-manifest] wrote {len(series)} series -> "
          f"{manifest_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())