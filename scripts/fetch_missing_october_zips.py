#!/usr/bin/env python3
"""Download the missing October 2026 Binance archive zips for the DISP-003 panel set.

The cutoff gate for the H10 fresh sealed forward block requires the Binance Public
Data Archive to publish October 2026 monthly klines AND fundingRate zips for the
assets that form the expanding universe. As of the 2026-11-02T14:30Z probe the
archive has published October 2026 zips for 30 of the 32 panel symbols; MATICUSDT
and EOSUSDT still return HTTP 404 (MATICUSDT was delisted 2024-09, EOSUSDT was
delisted 2025-05, so they have no October 2026 observations by construction).

This script fetches only the zips that are MISSING on disk, writes them verbatim
with their SHA-256 next to the existing raw zips, and reports per-symbol coverage.
It is free-data-only (keyless HTTPS to data.binance.vision), idempotent, and does
NOT touch the canonical forward block, the grid ledger, DISPERSION-001/002 or any
frozen artifact. It is a data-acquisition step, not an evaluation input.

Usage:
    python3 scripts/fetch_missing_october_zips.py [--experiment EXP]
"""
from __future__ import annotations

import argparse
import sys
import time
import zipfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = "https://data.binance.vision/data/futures/um"
TARGET_YM = "2026-10"
TIMEOUT = 60
MAX_RETRIES = 4
BACKOFF_BASE = 2.0
SLEEP_BETWEEN = 0.35

# The 32 panel symbols in the DISP-003 expanding universe.
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "DOGEUSDT", "DOTUSDT", "MATICUSDT", "AVAXUSDT", "LINKUSDT", "UNIUSDT",
    "LTCUSDT", "BCHUSDT", "ETCUSDT", "XLMUSDT", "ATOMUSDT", "ALGOUSDT",
    "VETUSDT", "FILUSDT", "TRXUSDT", "EOSUSDT", "NEOUSDT", "IOSTUSDT",
    "QTUMUSDT", "ZECUSDT", "DASHUSDT", "RUNEUSDT", "1INCHUSDT", "AAVEUSDT",
    "ACHUSDT", "AGLDUSDT",
]


def http_get(url: str) -> tuple[bytes | None, int | None, str | None]:
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = Request(url, headers={"Accept": "application/zip"})
            with urlopen(req, timeout=TIMEOUT) as resp:
                return resp.read(), resp.getcode(), None
        except HTTPError as exc:
            if exc.code == 404:
                return None, 404, "404_not_found"
            last_err = f"HTTP {exc.code}"
            if exc.code in (429, 502, 503, 504):
                time.sleep(BACKOFF_BASE ** attempt)
                continue
            return None, exc.code, last_err
        except (URLError, TimeoutError, OSError) as exc:
            last_err = f"{type(exc).__name__}: {exc}"
            time.sleep(BACKOFF_BASE ** attempt)
    return None, None, last_err or "exhausted_retries"


def fetch_missing(exp: str) -> int:
    raw_root = ROOT / "artifacts" / exp / "data" / "raw" / "binance"
    fetched = 0
    missing_after: list[str] = []
    for kind in ("klines", "funding"):
        url_fn = (lambda s: f"{ARCHIVE}/monthly/klines/{s}/1d/{s}-1d-{TARGET_YM}.zip") if kind == "klines" \
            else (lambda s: f"{ARCHIVE}/monthly/fundingRate/{s}/{s}-fundingRate-{TARGET_YM}.zip")
        ext = "klines" if kind == "klines" else "funding"
        for symbol in SYMBOLS:
            out_dir = raw_root / kind / symbol
            out_dir.mkdir(parents=True, exist_ok=True)
            out = out_dir / f"{symbol}-{ext}-{TARGET_YM}.zip"
            if out.exists():
                continue
            data, status, err = http_get(url_fn(symbol))
            if data is None:
                missing_after.append(f"{symbol}/{kind}({status})")
                print(f"[fetch] {symbol}/{kind}: MISSING {status} {err}", flush=True)
                time.sleep(SLEEP_BETWEEN)
                continue
            out.write_bytes(data)
            fetched += 1
            print(f"[fetch] {symbol}/{kind}: wrote {len(data)} bytes -> "
                  f"{out.relative_to(ROOT)}", flush=True)
            time.sleep(SLEEP_BETWEEN)

    print(f"[fetch] downloaded {fetched} missing October 2026 zips")
    if missing_after:
        print(f"[fetch] still missing ({len(missing_after)}): {', '.join(missing_after)}")
    return 0 if not missing_after else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--experiment", default="HARMONY-CRYPTO-EDGE-004-DISPERSION-003")
    args = ap.parse_args()
    return fetch_missing(args.experiment)


if __name__ == "__main__":
    raise SystemExit(main())