#!/usr/bin/env python3
"""Refresh free public price, cap and funding data to the latest fully closed UTC daily candle.

Writes raw archived responses (with SHA-256) and normalized panels under
artifacts/<experiment>/data/.

Free-data-only: keyless CoinMetrics Community API + Binance Public Data Archive,
bounded exponential backoff, caching. No API keys are stored or printed.

Point-in-time rules: no forward-fill; missingness and instrument lifecycle kept
explicit. Raw responses are archived verbatim with per-file SHA-256 so every
cutoff is reproducible and auditable.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"

# CoinMetrics Community API asset IDs (canonical lowercase). Legacy 28 mapped set
# plus verified DISPERSION-003 candidate batch 1 assets.
ASSETS = [
    "btc", "eth", "sol", "bnb", "xrp", "ada", "doge", "dot", "matic", "avax",
    "link", "uni", "ltc", "bch", "etc", "xlm", "atom", "algo", "vet", "fil",
    "trx", "eos", "neo", "iost", "qtum", "zec", "dash", "rune",
    "1inch", "aave", "ach", "agld",
]

# CoinMetrics asset -> Binance USD-M perpetual symbol (canonical, uppercase).
SYMBOL_MAP = {
    "btc": "BTCUSDT", "eth": "ETHUSDT", "sol": "SOLUSDT", "bnb": "BNBUSDT",
    "xrp": "XRPUSDT", "ada": "ADAUSDT", "doge": "DOGEUSDT", "dot": "DOTUSDT",
    "matic": "MATICUSDT", "avax": "AVAXUSDT", "link": "LINKUSDT", "uni": "UNIUSDT",
    "ltc": "LTCUSDT", "bch": "BCHUSDT", "etc": "ETCUSDT", "xlm": "XLMUSDT",
    "atom": "ATOMUSDT", "algo": "ALGOUSDT", "vet": "VETUSDT", "fil": "FILUSDT",
    "trx": "TRXUSDT", "eos": "EOSUSDT", "neo": "NEOUSDT", "iost": "IOSTUSDT",
    "qtum": "QTUMUSDT", "zec": "ZECUSDT", "dash": "DASHUSDT", "rune": "RUNEUSDT",
    # Verified candidate batch 1 (DISPERSION-003 expanding arm).
    "1inch": "1INCHUSDT", "aave": "AAVEUSDT", "ach": "ACHUSDT", "agld": "AGLDUSDT",
}

CM_BASE = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
BINANCE_ARCHIVE = "https://data.binance.vision/data/futures/um"

CM_METRICS = ["CapMrktEstUSD", "CapMrktCurUSD"]
CM_FREQUENCY = "1d"
CM_START = "2023-01-01"

REQUEST_TIMEOUT = 30
MAX_RETRIES = 6
BACKOFF_BASE = 2.0
BETWEEN_ASSET_SLEEP = 1.0  # respect CoinMetrics community rate limits

BINANCE_MAX_WORKERS = 2
BINANCE_REQUEST_TIMEOUT = 60
BINANCE_MAX_RETRIES = 4
BINANCE_BACKOFF_BASE = 2.0
BINANCE_SLEEP_BETWEEN = 0.35

KLINES_HEADER = "open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore"
FUNDING_HEADER = "symbol,calc_time,funding_interval_hours,last_funding_rate"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_KIND_ORDER = {"funding": 0, "klines": 1}


def _series_sig(d):
    """Return a copy of ``d`` with every ``series`` array sorted.

    The ``series`` array is collected via a thread pool, so its order is not
    reproducible run to run. Sorting by (asset, kind) makes the signature
    order-independent while still sensitive to any actual data change. The
    signature recurses into nested dicts (e.g. ``run_record["binance"]``) so
    both the flat Binance manifest and the refresh provenance record compare
    order-independently.
    """
    if isinstance(d, dict):
        out = {k: _series_sig(v) for k, v in d.items() if k != "fetch_utc"}
        if isinstance(out.get("series"), list):
            out["series"] = sorted(out["series"], key=lambda r: (r.get("asset", ""), _KIND_ORDER.get(r.get("kind", ""), 99)))
        return out
    if isinstance(d, list):
        return [_series_sig(x) for x in d]
    return d


def preserve_fetch_utc_if_unchanged(path: Path, new_dict: dict, data_sig) -> bool:
    """Keep a committed manifest byte-stable when a refresh changes no data.

    The sealed forward block records SHA-256 input hashes over the panel
    manifests. A no-op refresh only rewrites the ``fetch_utc`` timestamp (and,
    because Binance series are collected via a thread pool, occasionally the
    ``series`` array order), which would silently invalidate those provenance
    hashes and fail ``test_forward_block_hashes_match_files_on_disk``. When the
    data signature is unchanged, leave the existing file untouched so the
    committed artifact stays byte-identical. Returns True when the caller may
    skip writing. When data genuinely changes, the new fetch_utc and order are
    kept and the caller writes normally.
    """
    if not path.exists():
        return False
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return False
    if existing.get("fetch_utc") and data_sig(existing) == data_sig(new_dict):
        new_dict["fetch_utc"] = existing["fetch_utc"]
        return True
    return False


# ---------------------------------------------------------------------------
# CoinMetrics Community API
# ---------------------------------------------------------------------------

def cm_fetch_json(url: str) -> tuple[dict, str]:
    """GET JSON with retries and backoff. Returns (payload, raw_sha)."""
    last_err: str | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                raw = resp.read()
                return json.loads(raw.decode("utf-8")), sha256_bytes(raw)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace") if hasattr(exc, "read") else str(exc)
            last_err = f"HTTP {exc.code}: {body[:200]}"
            if exc.code in (400, 403):
                raise RuntimeError(f"free_tier_unavailable {last_err}") from exc
            if exc.code in (429, 502, 503, 504):
                time.sleep(BACKOFF_BASE ** attempt)
                continue
            raise RuntimeError(f"non-retryable {last_err}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = f"{type(exc).__name__}: {exc}"
            time.sleep(BACKOFF_BASE ** attempt)
            continue
    raise RuntimeError(f"exhausted retries: {last_err}")


def cm_asset_url(asset: str, metric: str, start_time: str, end_time: str) -> str:
    params = (f"assets={asset}&metrics={metric}&frequency={CM_FREQUENCY}"
              f"&start_time={start_time}&end_time={end_time}")
    return f"{CM_BASE}?{params}"


def cm_fetch_asset_metric(asset: str, metric: str, start_time: str, end_time: str):
    """Fetch all pages for one (asset, metric). Returns (rows, page_shas) or None on 403."""
    url = cm_asset_url(asset, metric, start_time, end_time)
    all_rows: list[dict] = []
    page_shas: list[str] = []
    try:
        while True:
            payload, raw_sha = cm_fetch_json(url)
            page_shas.append(raw_sha)
            rows = payload.get("data", [])
            all_rows.extend(rows)
            nxt = payload.get("next_page_url")
            if not nxt:
                break
            url = nxt
    except RuntimeError as exc:
        if "free_tier_unavailable" in str(exc) or "HTTP 403" in str(exc):
            return None
        raise
    return all_rows, page_shas


# ---------------------------------------------------------------------------
# Binance Public Data Archive
# ---------------------------------------------------------------------------

def month_iter(start_ym: str, end_ym: str):
    y, m = map(int, start_ym.split("-"))
    ey, em = map(int, end_ym.split("-"))
    while (y, m) <= (ey, em):
        yield f"{y:04d}-{m:02d}"
        m += 1
        if m > 12:
            m = 1
            y += 1


def binance_fetch_bytes(url: str) -> tuple[bytes | None, int | None, str | None]:
    """GET raw bytes. Returns (data, status, sha) or (None, status, error)."""
    last_err = None
    for attempt in range(1, BINANCE_MAX_RETRIES + 1):
        try:
            req = Request(url, headers={"Accept": "application/zip"})
            with urlopen(req, timeout=BINANCE_REQUEST_TIMEOUT) as resp:
                data = resp.read()
                return data, resp.getcode(), sha256_bytes(data)
        except HTTPError as exc:
            if exc.code == 404:
                return None, 404, "404_not_found"
            last_err = f"HTTP {exc.code}"
            if exc.code in (429, 502, 503, 504):
                time.sleep(BINANCE_BACKOFF_BASE ** attempt)
                continue
            return None, exc.code, last_err
        except (URLError, TimeoutError, OSError) as exc:
            last_err = f"{type(exc).__name__}: {exc}"
            time.sleep(BINANCE_BACKOFF_BASE ** attempt)
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


def binance_kline_url(symbol: str, ym: str) -> str:
    return f"{BINANCE_ARCHIVE}/monthly/klines/{symbol}/1d/{symbol}-1d-{ym}.zip"


def binance_funding_url(symbol: str, ym: str) -> str:
    return f"{BINANCE_ARCHIVE}/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{ym}.zip"


def fetch_binance_series(symbol: str, kind: str, start_ym: str, end_ym: str, raw_root: Path) -> dict:
    url_fn = binance_kline_url if kind == "klines" else binance_funding_url
    ext = "klines" if kind == "klines" else "funding"
    months = list(month_iter(start_ym, end_ym))

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
        out = raw_root / kind / symbol / f"{symbol}-{ext}-{ym}.zip"
        out.parent.mkdir(parents=True, exist_ok=True)

        data, status, err = binance_fetch_bytes(url)
        if data is None:
            if status == 404 or err == "404_not_found":
                result["months_missing"] += 1
                result["months"].append({"ym": ym, "status": "missing"})
            else:
                result["months_error"] += 1
                result["months"].append({"ym": ym, "status": "error", "error": err})
            time.sleep(BINANCE_SLEEP_BETWEEN)
            continue

        out.write_bytes(data)
        result["months_ok"] += 1
        result["months"].append({
            "ym": ym, "status": "ok", "raw_path": str(out.relative_to(ROOT)),
            "raw_sha256": sha256_bytes(data),
        })
        csv_text = extract_csv(data)
        if csv_text:
            all_csv_text.append(csv_text)
            result["rows"] += csv_text.count("\n")
        time.sleep(BINANCE_SLEEP_BETWEEN)

    header = KLINES_HEADER if kind == "klines" else FUNDING_HEADER
    panel_path = raw_root.parent.parent / "panels" / f"binance_{kind}_{symbol}.csv"
    panel_path.parent.mkdir(parents=True, exist_ok=True)
    if all_csv_text:
        bodies = []
        for t in all_csv_text:
            ls = t.splitlines()
            first = ls[0].strip()
            if kind == "klines" and first.startswith("open_time,"):
                ls = ls[1:]
            elif kind == "funding" and first.startswith("calc_time,"):
                ls = ls[1:]
            # The Binance fundingRate archive ships 3 columns
            # (calc_time,funding_interval_hours,last_funding_rate) with no symbol
            # column, but the panel header is 4 columns and every downstream reader
            # (pandas, build_universe, eval_forward_block) expects the symbol in
            # column 0. Prefix every funding row with the symbol so the header and
            # the data agree; without this the symbol int lands in calc_time and
            # last_funding_rate parses as NaN across all 32 panels.
            if kind == "funding":
                ls = [f"{symbol},{l}" for l in ls]
            bodies.extend(ls)
        panel_path.write_text(header + "\n" + "\n".join(bodies) + "\n")
        dates = [l.split(",")[1] for l in bodies if l.strip()] if kind == "funding" \
            else [l.split(",")[0] for l in bodies if l.strip()]
        if dates:
            result["date_first"] = min(dates)
            result["date_last"] = max(dates)
    else:
        panel_path.write_text(header + "\n")
    return result


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Refresh free public price, cap and funding data.")
    p.add_argument("--experiment", default=DEFAULT_EXP)
    p.add_argument("--assets", default="legacy28", help='comma-separated asset IDs or "legacy28"')
    p.add_argument("--binance-assets", default="btc,eth", help='comma-separated asset IDs for Binance price/funding')
    p.add_argument("--cap-start", default=CM_START)
    p.add_argument("--cap-end", default="2026-10-23", help="latest CoinMetrics cap candle date")
    p.add_argument("--price-end", default="2026-09-30", help="latest Binance price/funding candle date (full month)")
    return p


def main() -> int:
    args = build_arg_parser().parse_args()
    exp = args.experiment
    art = ROOT / "artifacts" / exp
    raw_root = art / "data" / "raw"
    panels = art / "data" / "panels"
    raw_root.mkdir(parents=True, exist_ok=True)
    panels.mkdir(parents=True, exist_ok=True)

    fetch_utc = now_utc()
    run_record = {
        "experiment_id": exp,
        "fetch_utc": fetch_utc,
        "sources": {
            "coinmetrics_community_api": CM_BASE,
            "binance_public_data_archive": BINANCE_ARCHIVE,
        },
        "auth": "keyless free public sources; no API keys, payment, or subscription",
        "point_in_time": "no forward-fill; eligibility and ranking use on-or-before formation information",
    }

    # ---------------- CoinMetrics market caps ----------------
    assets = ASSETS if args.assets == "legacy28" else [a.strip() for a in args.assets.split(",") if a.strip()]
    cm_raw_dir = raw_root / "coinmetrics"
    cm_raw_dir.mkdir(parents=True, exist_ok=True)

    cm_asset_results: dict[str, dict] = {}
    frames: dict[str, dict[str, dict[str, str]]] = {}
    for asset in assets:
        print(f"[coinmetrics] {asset}: fetching caps {args.cap_start}->{args.cap_end}", flush=True)
        asset_entry = {"asset": asset, "metrics": {}}
        available_any = False
        for metric in CM_METRICS:
            result = cm_fetch_asset_metric(asset, metric, args.cap_start, args.cap_end)
            if result is None:
                print(f"[coinmetrics] {asset}/{metric}: blocked free tier", flush=True)
                asset_entry["metrics"][metric] = {"status": "blocked_free_tier", "rows": 0}
                time.sleep(BETWEEN_ASSET_SLEEP)
                continue
            rows, page_shas = result
            available_any = True
            combined_sha = hashlib.sha256("".join(page_shas).encode()).hexdigest()
            raw_path = cm_raw_dir / f"{asset}_{metric}.json"
            raw_path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
            for r in rows:
                t = r.get("time")
                if t:
                    frames.setdefault(asset, {}).setdefault(t, {})[metric] = r.get(metric, "")
            asset_entry["metrics"][metric] = {
                "status": "ok",
                "rows": len(rows),
                "raw_path": str(raw_path.relative_to(ROOT)),
                "raw_sha256": combined_sha,
                "page_shas": page_shas,
                "time_first": rows[0].get("time") if rows else None,
                "time_last": rows[-1].get("time") if rows else None,
            }
            print(f"[coinmetrics] {asset}/{metric}: {len(rows)} rows", flush=True)
            time.sleep(BETWEEN_ASSET_SLEEP)
        if available_any:
            cm_asset_results[asset] = asset_entry
        else:
            cm_asset_results[asset] = asset_entry
            print(f"[coinmetrics] {asset}: no metrics available on free tier", flush=True)

    cm_panel_path = panels / "marketcap_panel.csv"
    with cm_panel_path.open("w") as fh:
        fh.write("date,asset,CapMrktCurUSD,CapMrktEstUSD\n")
        for asset in sorted(frames):
            for t in sorted(frames[asset]):
                row = frames[asset][t]
                fh.write(f"{t},{asset},{row.get('CapMrktCurUSD','')},{row.get('CapMrktEstUSD','')}\n")
    cm_panel_bytes = cm_panel_path.read_bytes()
    cm_panel_sha = sha256_bytes(cm_panel_bytes)
    cm_panel_rows = sum(len(v) for v in frames.values())

    cm_manifest_path = panels / "marketcap_panel_manifest.json"
    cm_manifest = {
        "experiment_id": exp,
        "source": "coinmetrics_community_api",
        "endpoint": CM_BASE,
        "panel_path": str(cm_panel_path.relative_to(ROOT)),
        "panel_sha256": cm_panel_sha,
        "panel_rows": cm_panel_rows,
        "assets_requested": assets,
        "assets_with_data": sorted(frames.keys()),
        "start": args.cap_start,
        "end": args.cap_end,
        "frequency": CM_FREQUENCY,
        "metrics": CM_METRICS,
        "fetch_utc": fetch_utc,
        "asset_results": cm_asset_results,
    }
    if not preserve_fetch_utc_if_unchanged(cm_manifest_path, cm_manifest, _series_sig):
        cm_manifest_path.write_text(json.dumps(cm_manifest, indent=2, sort_keys=True) + "\n")
    print(f"[coinmetrics] panel -> {cm_panel_path.relative_to(ROOT)} ({cm_panel_rows} rows) sha={cm_panel_sha[:12]}")
    print(f"[coinmetrics] manifest -> {cm_manifest_path.relative_to(ROOT)}")
    run_record["coinmetrics"] = {
        "panel_path": str(cm_panel_path.relative_to(ROOT)),
        "panel_sha256": cm_panel_sha,
        "panel_rows": cm_panel_rows,
        "date_first": cm_manifest["asset_results"][sorted(frames.keys())[0]]["metrics"]["CapMrktEstUSD"]["time_first"] if frames else None,
        "date_last": max((v["metrics"]["CapMrktEstUSD"]["time_last"] for v in cm_asset_results.values() if v["metrics"].get("CapMrktEstUSD", {}).get("status") == "ok"), default=None),
    }

    # ---------------- Binance price + funding ----------------
    binance_assets = [a.strip() for a in args.binance_assets.split(",") if a.strip()]
    binance_raw_dir = raw_root / "binance"
    binance_start_ym = args.cap_start[:7]
    price_end_ym = args.price_end[:7]
    binance_records: list[dict] = []

    def _run(symbol: str, kind: str) -> dict:
        rec = fetch_binance_series(symbol, kind, binance_start_ym, price_end_ym, binance_raw_dir)
        rec["asset"] = next(a for a, s in SYMBOL_MAP.items() if s == symbol)
        return rec

    with ThreadPoolExecutor(max_workers=BINANCE_MAX_WORKERS) as ex:
        futures = [ex.submit(_run, SYMBOL_MAP[a], kind) for a in binance_assets for kind in ("klines", "funding")]
        for fut in as_completed(futures):
            rec = fut.result()
            binance_records.append(rec)
            print(f"[binance] {rec['symbol']}/{rec['kind']}: ok={rec['months_ok']} "
                  f"missing={rec['months_missing']} error={rec['months_error']} "
                  f"rows={rec['rows']} {rec['date_first']}->{rec['date_last']}", flush=True)

    # as_completed yields in thread completion order, which is not reproducible.
    # Sort deterministically by (asset, kind) with kind in a fixed lexical order
    # (funding before klines) so the manifest hash is stable across runs and
    # matches the hashes recorded in the sealed forward block.
    binance_records.sort(key=lambda r: (r.get("asset", ""), _KIND_ORDER.get(r.get("kind", ""), 99)))

    binance_manifest = {
        "experiment_id": exp,
        "source": "binance_public_data_archive",
        "archive": BINANCE_ARCHIVE,
        "window": {"start": binance_start_ym, "end": price_end_ym},
        "symbol_map": {a: SYMBOL_MAP[a] for a in binance_assets},
        "fetch_utc": fetch_utc,
        "series": binance_records,
    }
    binance_manifest_path = panels / "binance_panel_manifest.json"
    if not preserve_fetch_utc_if_unchanged(binance_manifest_path, binance_manifest, _series_sig):
        binance_manifest_path.write_text(json.dumps(binance_manifest, indent=2, sort_keys=True) + "\n")
    print(f"[binance] manifest -> {binance_manifest_path.relative_to(ROOT)}")
    run_record["binance"] = {
        "manifest_path": str(binance_manifest_path.relative_to(ROOT)),
        "window": {"start": binance_start_ym, "end": price_end_ym},
        "series": binance_records,
    }

    run_record_path = panels / "data_refresh_provenance.json"
    if not preserve_fetch_utc_if_unchanged(run_record_path, run_record, _series_sig):
        run_record_path.write_text(json.dumps(run_record, indent=2, sort_keys=True) + "\n")
    print(f"[refresh] provenance -> {run_record_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
