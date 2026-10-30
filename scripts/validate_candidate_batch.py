#!/usr/bin/env python3
"""Validate the first discovered candidate batch (25 assets) for DISPERSION-003.

For each candidate in research_state/universe_frontier.json (candidates_discovered):
  1. Fetch CoinMetrics CapMrktEstUSD history (point-in-time, no forward-fill).
  2. Probe Binance USD-M perpetual symbol (<ASSET>USDT) for contract existence.
  3. Record eligibility (cap data AND perpetual contract available) or blocker.
  4. Move asset from candidates_discovered to candidates_verified or candidates_blocked.

Free-data-only: keyless CoinMetrics Community API + Binance Public Data Archive.
No API keys, no secrets, no trading.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTIER_PATH = ROOT / "research_state" / "universe_frontier.json"
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
RAW_DIR = ART / "data" / "raw" / "coinmetrics_candidates"
PANEL_DIR = ART / "data" / "panels"
CM_BASE = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
BINANCE_ARCHIVE = "https://data.binance.vision/data/futures/um"

CM_START = "2023-01-01"
CM_END = "2026-10-23"
CM_METRICS = ["CapMrktEstUSD", "CapMrktCurUSD"]
CM_FREQUENCY = "1d"

REQUEST_TIMEOUT = 30
MAX_RETRIES = 6
BACKOFF_BASE = 2.0
BETWEEN_ASSET_SLEEP = 1.0
BINANCE_MAX_RETRIES = 3
BINANCE_BACKOFF_BASE = 2.0


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# Binance series are collected via a thread pool, so their order in the
# manifest is not reproducible run to run. Fixed lexical order keeps the
# signature and the committed manifest byte-stable.
_KIND_ORDER = {"funding": 0, "klines": 1}


def _series_sig(d):
    """Return a copy of ``d`` with every ``series`` array sorted.

    The ``series`` array is collected via a thread pool, so its order is not
    reproducible run to run. Sorting by (asset, kind) makes the signature
    order-independent while still sensitive to any actual data change. The
    signature recurses into nested dicts so it also covers the candidate
    validation record, which is hashed by the sealed forward block.
    """
    if isinstance(d, dict):
        out = {k: _series_sig(v) for k, v in d.items()
               if k not in ("fetch_utc", "time_order_note")}
        if isinstance(out.get("series"), list):
            out["series"] = sorted(out["series"], key=lambda r: (r.get("asset", ""), _KIND_ORDER.get(r.get("kind", ""), 99)))
        return out
    if isinstance(d, list):
        return [_series_sig(x) for x in d]
    return d


def preserve_fetch_utc_if_unchanged(path: Path, new_dict: dict, data_sig) -> bool:
    """Keep a committed manifest byte-stable when a refresh changes no data.

    The sealed forward block records SHA-256 input hashes over the panel
    manifests and the candidate validation record. A no-op validation run
    only rewrites the ``fetch_utc`` timestamp, which would silently invalidate
    those provenance hashes and fail ``test_forward_block_hashes_match_files_on_disk``.
    When the data signature is unchanged, leave the existing file untouched so
    the committed artifact stays byte-identical. Returns True when the caller
    may skip writing. When data genuinely changes, the new fetch_utc is kept
    and the caller writes normally.
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


def cm_fetch_json(url: str):
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                raw = resp.read()
                return json.loads(raw.decode("utf-8")), sha256_bytes(raw)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace") if hasattr(exc, "read") else str(exc)
            last_err = f"HTTP {exc.code}: {body[:200]}"
            if exc.code == 400:
                raise RuntimeError(f"asset_not_served {last_err}") from exc
            if exc.code == 403:
                raise RuntimeError(f"free_tier_unavailable {last_err}") from exc
            if exc.code in (429, 502, 503, 504):
                time.sleep(BACKOFF_BASE ** attempt)
                continue
            raise RuntimeError(f"non-retryable {last_err}") from exc
        except (urllib.error.URLError, TimeoutError, OSError, UnicodeError) as exc:
            last_err = f"{type(exc).__name__}: {exc}"
            time.sleep(BACKOFF_BASE ** attempt)
            continue
    raise RuntimeError(f"exhausted retries: {last_err}")


def cm_fetch_asset_metric(asset: str, metric: str, start_time: str, end_time: str):
    """Fetch one (asset, metric) series.

    Returns (rows, page_shas) on success, or None on free-tier/invalid-asset
    failure. The caller records the specific reason: HTTP 400 means the asset
    id is not served on the community tier (invalid or unsupported), HTTP 403
    means the free tier is unavailable for this metric/asset combination.
    """
    params = (f"assets={asset}&metrics={metric}&frequency={CM_FREQUENCY}"
              f"&start_time={start_time}&end_time={end_time}")
    url = f"{CM_BASE}?{params}"
    all_rows = []
    page_shas = []
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
        msg = str(exc)
        if "asset_not_served" in msg:
            return None, "asset_not_served"
        if "free_tier_unavailable" in msg or "HTTP 403" in msg:
            return None, "blocked_free_tier"
        raise
    return all_rows, page_shas


def binance_symbol_exists(symbol: str):
    """Probe whether a Binance USD-M perpetual monthly kline zip exists for symbol."""
    ym = "2024-01"
    url = f"{BINANCE_ARCHIVE}/monthly/klines/{symbol}/1d/{symbol}-1d-{ym}.zip"
    last_err = None
    for attempt in range(1, BINANCE_MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/zip"})
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                data = resp.read(1)
                return True, None
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return False, "404_not_found"
            last_err = f"HTTP {exc.code}"
            if exc.code in (429, 502, 503, 504):
                time.sleep(BINANCE_BACKOFF_BASE ** attempt)
                continue
            return False, last_err
        except (urllib.error.URLError, TimeoutError, OSError, UnicodeError) as exc:
            last_err = f"{type(exc).__name__}: {exc}"
            time.sleep(BINANCE_BACKOFF_BASE ** attempt)
            continue
    return False, last_err or "exhausted_retries"


def load_frontier():
    return json.loads(FRONTIER_PATH.read_text(encoding="utf-8"))


def save_frontier(frontier):
    frontier["last_updated_utc"] = now_utc()
    FRONTIER_PATH.write_text(
        json.dumps(frontier, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate discovered candidate assets.")
    p.add_argument("--limit", type=int, default=25,
                   help="max candidates to process this run (bounded batch)")
    p.add_argument("--cap-start", default=CM_START)
    p.add_argument("--cap-end", default=CM_END)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PANEL_DIR.mkdir(parents=True, exist_ok=True)

    frontier = load_frontier()
    discovered = list(frontier.get("candidates_discovered", []))
    verified = list(frontier.get("candidates_verified", []))
    blocked = list(frontier.get("candidates_blocked", []))

    already = set(verified) | set(blocked)
    to_process = [a for a in discovered if a not in already][: args.limit]

    print(f"[candidates] discovered={len(discovered)} already_processed={len(already)} "
          f"to_process={len(to_process)}", flush=True)

    fetch_utc = now_utc()
    run_record = {
        "experiment_id": EXP,
        "fetch_utc": fetch_utc,
        "sources": {
            "coinmetrics_community_api": CM_BASE,
            "binance_public_data_archive": BINANCE_ARCHIVE,
        },
        "auth": "keyless free public sources; no API keys, payment, or subscription",
        "point_in_time": "no forward-fill; eligibility uses on-or-before formation information",
        "candidates_processed": [],
    }

    # The committed validation record accumulates every batch's entries, so a
    # fresh run must extend rather than replace it. Loading the existing
    # record preserves prior batches' provenance and keeps the sealed forward
    # block's input hash valid.
    val_path = PANEL_DIR / "candidate_batch_validation.json"
    if val_path.exists():
        try:
            existing = json.loads(val_path.read_text(encoding="utf-8"))
            if isinstance(existing.get("candidates_processed"), list):
                run_record["candidates_processed"] = list(existing["candidates_processed"])
                run_record.setdefault("fetch_utc", existing.get("fetch_utc"))
        except (ValueError, OSError):
            pass

    for asset in to_process:
        entry = {"asset": asset, "fetch_utc": fetch_utc, "metrics": {},
                 "binance": {"symbol": None, "exists": None, "error": None},
                 "eligible": False, "status": None}
        print(f"[candidate] {asset}: fetching caps...", flush=True)

        if not asset.isascii():
            entry["metrics"] = {}
            entry["binance"] = {"symbol": None, "exists": False, "error": "non_ascii_asset_id"}
            entry["eligible"] = False
            entry["status"] = "blocked"
            entry["blocker_reasons"] = ["non_ascii_asset_id"]
            blocked.append(asset)
            run_record["candidates_processed"].append(entry)
            print(f"[candidate] {asset}: BLOCKED (non_ascii_asset_id)", flush=True)
            continue

        has_est = False
        for metric in CM_METRICS:
            result = cm_fetch_asset_metric(asset, metric, args.cap_start, args.cap_end)
            rows, payload = result
            if rows is None:
                entry["metrics"][metric] = {"status": payload, "rows": 0}
                print(f"[candidate] {asset}/{metric}: {payload}", flush=True)
                time.sleep(BETWEEN_ASSET_SLEEP)
                continue
            page_shas = payload
            combined_sha = hashlib.sha256("".join(page_shas).encode()).hexdigest()
            raw_path = RAW_DIR / f"{asset}_{metric}.json"
            RAW_DIR.mkdir(parents=True, exist_ok=True)
            raw_path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
            if rows:
                has_est = True if metric == "CapMrktEstUSD" else has_est
            # CoinMetrics paginates TIMESERIES endpoints in DESCENDING time
            # order: page 1 opens at the request end_time and walks backwards,
            # only the final page is ascending. rows[0]/rows[-1] are therefore
            # NOT the earliest/latest observation. Recording them as
            # time_first/time_last produced inverted boundaries for 189 of 190
            # verified candidates (e.g. alice time_first 2026-07-16 >
            # time_last 2023-04-02), which would mislead any downstream
            # point-in-time eligibility check. Sort by time before taking
            # boundaries; the raw file is left in API order (it is hashed and
            # must stay byte-identical).
            ordered = sorted(rows, key=lambda r: r.get("time") or "")
            entry["metrics"][metric] = {
                "status": "ok",
                "rows": len(rows),
                "raw_path": str(raw_path.relative_to(ROOT)),
                "raw_sha256": combined_sha,
                "page_shas": page_shas,
                "time_first": ordered[0].get("time") if ordered else None,
                "time_last": ordered[-1].get("time") if ordered else None,
                "time_order_note": (
                    "boundaries computed after sorting rows by time ascending; "
                    "the CoinMetrics timeseries endpoint paginates descending, "
                    "so the raw file's first/last rows are not the earliest/latest"
                ),
            }
            print(f"[candidate] {asset}/{metric}: {len(rows)} rows", flush=True)
            time.sleep(BETWEEN_ASSET_SLEEP)

        # Binance perpetual symbol probe
        symbol = f"{asset.upper()}USDT"
        entry["binance"]["symbol"] = symbol
        exists, err = binance_symbol_exists(symbol)
        entry["binance"]["exists"] = exists
        entry["binance"]["error"] = err
        print(f"[candidate] {asset}: binance {symbol} exists={exists} err={err}",
              flush=True)
        time.sleep(0.35)

        # Eligibility: CapMrktEstUSD rows > 0 AND Binance perpetual exists
        est_ok = entry["metrics"].get("CapMrktEstUSD", {}).get("status") == "ok" \
            and entry["metrics"].get("CapMrktEstUSD", {}).get("rows", 0) > 0
        entry["eligible"] = bool(est_ok and exists)

        if entry["eligible"]:
            entry["status"] = "verified"
            verified.append(asset)
            print(f"[candidate] {asset}: VERIFIED (cap + perpetual)", flush=True)
        else:
            reasons = []
            est = entry["metrics"].get("CapMrktEstUSD", {})
            if not est_ok:
                reasons.append(f"capmkt_est_usd:{est.get('status','missing')}")
            if not exists:
                reasons.append(f"no_binance_perpetual:{err}")
            entry["status"] = "blocked"
            entry["blocker_reasons"] = reasons
            blocked.append(asset)
            print(f"[candidate] {asset}: BLOCKED ({', '.join(reasons)})", flush=True)

        run_record["candidates_processed"].append(entry)
        save_frontier(frontier)

    # Update frontier lists
    frontier["candidates_discovered"] = [a for a in discovered if a not in to_process]
    frontier["candidates_verified"] = verified
    frontier["candidates_blocked"] = blocked
    frontier["candidate_page_cursor"] = frontier.get("candidate_page_cursor", 0) + len(to_process)
    frontier["batch_validation_utc"] = fetch_utc
    save_frontier(frontier)

    # A batch that processes nothing must not rewrite the validation record at
    # all: the committed record accumulates every prior batch's entries, so a
    # fresh ``run_record`` with an empty ``candidates_processed`` list would
    # silently drop 96 validated/blocked candidates and invalidate the sealed
    # forward block's input hash. Skip the write entirely when there is nothing
    # new to record.
    if not to_process:
        print(f"[candidates] nothing to process; validation record left untouched")
        print(f"[candidates] verified={len(verified)} blocked={len(blocked)} "
              f"remaining_discovered={len(frontier['candidates_discovered'])}")
        return 0

    # Write validation run record
    val_path = PANEL_DIR / "candidate_batch_validation.json"
    if not preserve_fetch_utc_if_unchanged(val_path, run_record, _series_sig):
        val_path.write_text(json.dumps(run_record, indent=2, sort_keys=True) + "\n")
    print(f"[candidates] validation record -> {val_path.relative_to(ROOT)}")
    print(f"[candidates] verified={len(verified)} blocked={len(blocked)} "
          f"remaining_discovered={len(frontier['candidates_discovered'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
