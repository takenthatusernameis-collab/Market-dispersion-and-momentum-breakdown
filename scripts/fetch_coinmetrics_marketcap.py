"""Fetch point-in-time market-cap history from CoinMetrics Community API.

Writes raw archived responses (with SHA-256) and a normalized panel under
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-001/data/.

Free-data-only: keyless Community API, bounded exponential backoff, caching.
No API keys are stored or printed.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-001"
RAW_DIR = ROOT / "artifacts" / EXP / "data" / "raw" / "coinmetrics"
PANEL_DIR = ROOT / "artifacts" / EXP / "data" / "panels"
BASE = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"

# Assets with high confidence of both CoinMetrics cap history and Binance
# USD-M perpetual listings. Canonical lowercase CoinMetrics asset IDs.
ASSETS = [
    "btc", "eth", "sol", "bnb", "xrp", "ada", "doge", "dot", "matic", "avax",
    "link", "uni", "ltc", "bch", "etc", "xlm", "atom", "algo", "vet", "fil",
    "trx", "eos", "neo", "iost", "qtum", "zec", "dash", "rune",
]

START = "2023-01-01"
END = "2024-12-31"
METRICS = ["CapMrktCurUSD", "CapMrktEstUSD"]
FREQUENCY = "1d"

REQUEST_TIMEOUT = 30
MAX_RETRIES = 6
BACKOFF_BASE = 2.0
BETWEEN_ASSET_SLEEP = 1.0  # respect community rate limits


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_json(url: str) -> tuple[dict, str]:
    """GET JSON with retries and backoff. Returns (payload, raw_sha).

    Raises RuntimeError on non-retryable errors; callers handle 403 per asset.
    """
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
                # Metric/asset not available on the free Community tier.
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


def asset_metrics_url(asset: str, metric: str, start_time: str | None = None) -> str:
    params = f"assets={asset}&metrics={metric}&frequency={FREQUENCY}&end_time={END}"
    if start_time:
        params += f"&start_time={start_time}"
    return f"{BASE}?{params}"


def fetch_asset_metric(asset: str, metric: str) -> tuple[list[dict], str] | None:
    """Fetch all pages for one (asset, metric). Returns (rows, combined_sha) or None on 403."""
    url = asset_metrics_url(asset, metric)
    all_rows: list[dict] = []
    page_shas: list[str] = []
    try:
        while True:
            payload, raw_sha = fetch_json(url)
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
    combined_sha = hashlib.sha256("".join(page_shas).encode()).hexdigest()
    return all_rows, combined_sha


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PANEL_DIR.mkdir(parents=True, exist_ok=True)

    asset_results: dict[str, dict] = {}
    frames: dict[str, dict[str, dict[str, str]]] = {}  # asset -> time -> {metric: value}

    for asset in ASSETS:
        print(f"[coinmetrics] {asset}: fetching...", flush=True)
        asset_entry: dict = {"asset": asset, "metrics": {}}
        available_any = False

        for metric in METRICS:
            result = fetch_asset_metric(asset, metric)
            if result is None:
                print(f"[coinmetrics] {asset}/{metric}: 403 not available on free tier", flush=True)
                asset_entry["metrics"][metric] = {"status": "blocked_free_tier", "rows": 0}
                time.sleep(BETWEEN_ASSET_SLEEP)
                continue
            rows, combined_sha = result
            available_any = True
            # Archive raw pages: store normalized rows as the archived raw artifact.
            raw_path = RAW_DIR / f"{asset}_{metric}.json"
            raw_path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
            for r in rows:
                t = r.get("time")
                if t:
                    frames.setdefault(asset, {}).setdefault(t, {})[metric] = r.get(metric, "")
            # CoinMetrics paginates TIMESERIES endpoints in DESCENDING time order,
            # so rows[0]/rows[-1] are NOT the earliest/latest observation. Sort by
            # time before taking boundaries; the raw file is left in API order
            # (it is hashed and must stay byte-identical).
            ordered = sorted(rows, key=lambda r: r.get("time") or "")
            asset_entry["metrics"][metric] = {
                "status": "ok",
                "rows": len(rows),
                "raw_path": str(raw_path.relative_to(ROOT)),
                "raw_sha256": combined_sha,
                "time_first": ordered[0].get("time") if ordered else None,
                "time_last": ordered[-1].get("time") if ordered else None,
                "time_order_note": (
                    "boundaries computed after sorting rows by time ascending; "
                    "the CoinMetrics timeseries endpoint paginates descending, "
                    "so the raw file's first/last rows are not the earliest/latest"
                ),
            }
            print(f"[coinmetrics] {asset}/{metric}: {len(rows)} rows", flush=True)
            time.sleep(BETWEEN_ASSET_SLEEP)

        if available_any:
            asset_results[asset] = asset_entry
        else:
            asset_results[asset] = asset_entry
            print(f"[coinmetrics] {asset}: no metrics available on free tier", flush=True)

    # Build normalized panel: date,asset,CapMrktCurUSD,CapMrktEstUSD
    panel_path = PANEL_DIR / "marketcap_panel.csv"
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    with panel_path.open("w") as fh:
        fh.write("date,asset,CapMrktCurUSD,CapMrktEstUSD\n")
        for asset in sorted(frames):
            for t in sorted(frames[asset]):
                row = frames[asset][t]
                fh.write(
                    f"{t},{asset},"
                    f"{row.get('CapMrktCurUSD','')},{row.get('CapMrktEstUSD','')}\n"
                )
    panel_bytes = panel_path.read_bytes()
    panel_sha = hashlib.sha256(panel_bytes).hexdigest()
    panel_rows = sum(len(v) for v in frames.values())

    manifest_path = PANEL_DIR / "marketcap_panel_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "experiment_id": EXP,
                "source": "coinmetrics_community_api",
                "endpoint": BASE,
                "panel_path": str(panel_path.relative_to(ROOT)),
                "panel_sha256": panel_sha,
                "panel_rows": panel_rows,
                "assets_requested": ASSETS,
                "assets_with_data": sorted(frames.keys()),
                "start": START,
                "end": END,
                "frequency": FREQUENCY,
                "metrics": METRICS,
                "asset_results": asset_results,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(f"[coinmetrics] panel -> {panel_path.relative_to(ROOT)} ({panel_rows} rows) sha={panel_sha[:12]}")
    print(f"[coinmetrics] manifest -> {manifest_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
