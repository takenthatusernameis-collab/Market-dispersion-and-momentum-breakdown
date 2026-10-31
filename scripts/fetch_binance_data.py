"""Fetch Binance USD-M perpetual daily klines and funding from the public archive.

data.binance.vision (free, keyless). Writes raw archived monthly zips (with
SHA-256) and normalized panels under
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-001/data/.

No API keys. Respects archive rate limits with bounded concurrency and backoff.
Missing months (pre-listing / delisted / gap) are recorded as exclusions, not
synthesized.
"""

from __future__ import annotations

import hashlib
import io
import json
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-001"
RAW_DIR = ROOT / "artifacts" / EXP / "data" / "raw" / "binance"
PANEL_DIR = ROOT / "artifacts" / EXP / "data" / "panels"
ARCHIVE = "https://data.binance.vision/data/futures/um"

# CoinMetrics asset -> Binance USD-M perpetual symbol (canonical, uppercase).
SYMBOL_MAP = {
    "btc": "BTCUSDT", "eth": "ETHUSDT", "sol": "SOLUSDT", "bnb": "BNBUSDT",
    "xrp": "XRPUSDT", "ada": "ADAUSDT", "doge": "DOGEUSDT", "dot": "DOTUSDT",
    "matic": "MATICUSDT", "avax": "AVAXUSDT", "link": "LINKUSDT", "uni": "UNIUSDT",
    "ltc": "LTCUSDT", "bch": "BCHUSDT", "etc": "ETCUSDT", "xlm": "XLMUSDT",
    "atom": "ATOMUSDT", "algo": "ALGOUSDT", "vet": "VETUSDT", "fil": "FILUSDT",
    "trx": "TRXUSDT", "eos": "EOSUSDT", "neo": "NEOUSDT", "iost": "IOSTUSDT",
    "qtum": "QTUMUSDT", "zec": "ZECUSDT", "dash": "DASHUSDT", "rune": "RUNEUSDT",
}

# Nominal analysis window (inclusive). Actual per-contract first/last dates are
# derived from what the archive contains (point-in-time, no backfill).
START_YM = "2020-01"
END_YM = "2024-12"

KLINES_HEADER = "open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore"
FUNDING_HEADER = "symbol,calc_time,funding_interval_hours,last_funding_rate"
MAX_WORKERS = 1
REQUEST_TIMEOUT = 60
MAX_RETRIES = 4
BACKOFF_BASE = 2.0
SLEEP_BETWEEN = 0.35


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def month_iter(start_ym: str, end_ym: str):
    y, m = map(int, start_ym.split("-"))
    ey, em = map(int, end_ym.split("-"))
    while (y, m) <= (ey, em):
        yield f"{y:04d}-{m:02d}"
        m += 1
        if m > 12:
            m = 1
            y += 1


def fetch_bytes(url: str) -> tuple[bytes | None, int | None, str | None]:
    """GET raw bytes. Returns (data, status, sha) or (None, status, error) on miss."""
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = Request(url, headers={"Accept": "application/zip"})
            with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                data = resp.read()
                return data, resp.getcode(), sha256_bytes(data)
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
            continue
    return None, None, last_err or "exhausted_retries"


def extract_csv(data: bytes) -> str | None:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
            if not csv_names:
                return None
            return zf.read(csv_names[0]).decode("utf-8")
    except (zipfile.BadZipFile, KeyError):
        return None


def kline_url(symbol: str, ym: str) -> str:
    return f"{ARCHIVE}/monthly/klines/{symbol}/1d/{symbol}-1d-{ym}.zip"


def funding_url(symbol: str, ym: str) -> str:
    return f"{ARCHIVE}/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{ym}.zip"


def fetch_series(symbol: str, kind: str) -> dict:
    """Fetch all monthly archives for one symbol/kind. Returns a result record."""
    url_fn = kline_url if kind == "klines" else funding_url
    ext = "klines" if kind == "klines" else "funding"
    months = list(month_iter(START_YM, END_YM))

    result = {
        "symbol": symbol,
        "kind": kind,
        "months_requested": len(months),
        "months_ok": 0,
        "months_missing": 0,
        "months_error": 0,
        "rows": 0,
        "date_first": None,
        "date_last": None,
        "months": [],
        "raw_dir": f"data/raw/binance/{kind}/{symbol}",
    }

    all_csv_text: list[str] = []
    for ym in months:
        url = url_fn(symbol, ym)
        rel = f"data/raw/binance/{kind}/{symbol}/{symbol}-{ext}-{ym}.zip"
        out = RAW_DIR / kind / symbol / f"{symbol}-{ext}-{ym}.zip"
        out.parent.mkdir(parents=True, exist_ok=True)

        data, status, err = fetch_bytes(url)
        if data is None:
            if status == 404 or err == "404_not_found":
                result["months_missing"] += 1
                result["months"].append({"ym": ym, "status": "missing"})
            else:
                result["months_error"] += 1
                result["months"].append({"ym": ym, "status": "error", "error": err})
            time.sleep(SLEEP_BETWEEN)
            continue

        out.write_bytes(data)
        result["months_ok"] += 1
        result["months"].append({
            "ym": ym, "status": "ok", "raw_path": rel,
            "raw_sha256": sha256_bytes(data),
        })
        csv_text = extract_csv(data)
        if csv_text:
            all_csv_text.append(csv_text)
            # Count DATA rows only: the monthly archive ships its own header row
            # (calc_time,... / open_time,...), and the panel is written with a
            # single canonical header, so counting raw newlines overstates the
            # panel row count by one per month. The manifest `rows` must equal
            # the number of data rows actually written to the panel CSV.
            body_lines = [ln for ln in csv_text.splitlines() if ln.strip()]
            if body_lines and body_lines[0].startswith(
                    ("open_time,", "calc_time,", "symbol,")):
                body_lines = body_lines[1:]
            result["rows"] += len(body_lines)
        time.sleep(SLEEP_BETWEEN)

    # Normalize panel with an explicit header; concat monthly bodies.
    header = KLINES_HEADER if kind == "klines" else FUNDING_HEADER
    panel_path = PANEL_DIR / f"binance_{kind}_{symbol}.csv"
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    if all_csv_text:
        bodies = []
        for t in all_csv_text:
            ls = t.splitlines()
            # Strip any header row present in a monthly archive so we keep one
            # canonical header written below.
            first = ls[0].strip()
            if kind == "klines" and first.startswith("open_time,"):
                ls = ls[1:]
            elif kind == "funding" and first.startswith("calc_time,"):
                ls = ls[1:]
            bodies.extend(ls)
        panel_path.write_text(header + "\n" + "\n".join(bodies) + "\n")
        dates = [l.split(",")[0] for l in bodies if l.strip()]
        if dates:
            result["date_first"] = min(dates)
            result["date_last"] = max(dates)
    else:
        panel_path.write_text("open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore\n"
                              if kind == "klines" else "symbol,fundingTime,fundingRate\n")
    return result


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PANEL_DIR.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    for asset, symbol in SYMBOL_MAP.items():
        for kind in ("klines", "funding"):
            rec = fetch_series(symbol, kind)
            rec["asset"] = asset
            records.append(rec)
            print(f"[binance] {symbol}/{kind}: ok={rec['months_ok']} "
                  f"missing={rec['months_missing']} error={rec['months_error']} "
                  f"rows={rec['rows']} {rec['date_first']}->{rec['date_last']}",
                  flush=True)

    manifest = {
        "experiment_id": EXP,
        "source": "binance_public_data_archive",
        "archive": ARCHIVE,
        "window": {"start": START_YM, "end": END_YM},
        "symbol_map": SYMBOL_MAP,
        "series": records,
    }
    manifest_path = PANEL_DIR / "binance_panel_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"[binance] manifest -> {manifest_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
