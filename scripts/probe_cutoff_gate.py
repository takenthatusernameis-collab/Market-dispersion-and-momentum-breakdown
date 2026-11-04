#!/usr/bin/env python3
"""Probe whether the Binance Public Data Archive has published the cutoff month.

Free-data-only: keyless HTTPS GET against data.binance.vision. No API keys,
no paid services, no trading. Writes a JSON record under
research_state/cutoff_probe/ and appends a summary line to the durable
handoff so the cutoff gate decision is auditable across sessions.

The gate is: the forward block may advance only when a published archive
covers a cutoff >= 2026-10-29 (the month-end that would let the sealed block
include formations after 2026-09-29 with a full 30-day outcome). A 404 on the
target month is a genuine availability signal only when the archive is alive
around it, so every probe records a positive control (the prior month, which
must return HTTP 200).

Usage:
    python3 scripts/probe_cutoff_gate.py [--probe-month 2026-10]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = "https://data.binance.vision/data/futures/um"
GATE_DATE = "2026-10-29"  # minimum cutoff required to unblock the forward block
CONTROL_MONTH = "2026-09"  # prior fully-published month; must return HTTP 200
TIMEOUT = 45


def http_probe(url: str) -> dict:
    """GET a URL and return (status, bytes, error)."""
    last_err = None
    for attempt in range(1, 4):
        try:
            req = Request(url, headers={"Accept": "application/zip"})
            with urlopen(req, timeout=TIMEOUT) as resp:
                return resp.getcode(), len(resp.read()), None
        except urllib.error.HTTPError as exc:
            return exc.code, 0, None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = f"{type(exc).__name__}: {exc}"
            time.sleep(2.0 ** attempt)
    return None, 0, last_err or "exhausted_retries"


def monthly_kline_url(symbol: str, ym: str) -> str:
    """Monthly klines path: the canonical Binance archive URL shape."""
    return f"{ARCHIVE}/monthly/klines/{symbol}/1d/{symbol}-1d-{ym}.zip"


def monthly_funding_url(symbol: str, ym: str) -> str:
    """Monthly fundingRate path: the canonical Binance archive URL shape."""
    return f"{ARCHIVE}/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{ym}.zip"


def daily_kline_url(symbol: str, ym: str, day: int) -> str:
    """Daily klines path for one calendar day within a month.

    The daily archive names files with a full YYYY-MM-DD date
    (BTCUSDT-1d-2026-10-31.zip), unlike the monthly path which uses YYYY-MM.
    """
    return f"{ARCHIVE}/daily/klines/{symbol}/1d/{symbol}-1d-{ym}-{day:02d}.zip"


def probe_month(ym: str, symbol: str = "BTCUSDT") -> list[dict]:
    """Probe every documented archive path for one (month, symbol).

    Covers the monthly klines and fundingRate paths (the two series the
    refresh pipeline consumes) plus the daily-kline path for the last three
    days of the month, which is a different endpoint family and was never
    probed before 2026-10-31. Daily-kline 200s for a couple of days do NOT
    constitute a published month for the pipeline's purposes: refresh_free_data
    fetches the monthly zips, so the gate requires the monthly endpoints.
    """
    urls = [
        monthly_kline_url(symbol, ym),
        monthly_funding_url(symbol, ym),
        daily_kline_url(symbol, ym, 28),
        daily_kline_url(symbol, ym, 29),
        daily_kline_url(symbol, ym, 30),
        daily_kline_url(symbol, ym, 31),
    ]
    return [{"url": u, "status": s, "bytes": b, "error": e}
            for u in urls for s, b, e in [http_probe(u)]]


def monthly_published(results: list[dict], symbol: str, ym: str) -> bool:
    """True only if both monthly endpoints the refresh pipeline consumes are HTTP 200.

    refresh_free_data.py fetches monthly klines and monthly fundingRate zips via
    monthly_kline_url / monthly_funding_url. A month is treated as published
    only when both are available; daily-kline 200s for a partial set of days do
    not give the pipeline a complete cutoff.
    """
    want_klines = monthly_kline_url(symbol, ym)
    want_funding = monthly_funding_url(symbol, ym)
    got = {r.get("url"): r.get("status") for r in results if isinstance(r, dict)}
    return got.get(want_klines) == 200 and got.get(want_funding) == 200


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probe-month", default="2026-10",
                    help="target month to probe (default 2026-10)")
    ap.add_argument("--symbol", default="BTCUSDT")
    args = ap.parse_args()

    target = args.probe_month
    target_end = f"{target}-31"
    # The gate requires a published archive whose cutoff is on/after GATE_DATE.
    # A month-end on/after 2026-10-29 satisfies the structural date requirement;
    # the month is usable only when its monthly archives (consumed by
    # refresh_free_data.py) are actually published.
    gate_met_by_month_end = target >= "2026-10"

    target_results = probe_month(target, args.symbol)
    control_results = probe_month(CONTROL_MONTH, args.symbol)

    # target_published requires the monthly klines AND monthly funding endpoints
    # to be HTTP 200. Daily-kline 200s for a partial set of days do not count.
    target_published = monthly_published(target_results, args.symbol, target)
    control_ok = any(r["status"] == 200 for r in control_results)
    archive_alive = control_ok
    gate = "UNBLOCKED" if (target_published and archive_alive and gate_met_by_month_end) else "BLOCKED"

    record = {
        "probe_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "probe_month": target,
        "symbol": args.symbol,
        "gate_date_required": GATE_DATE,
        "gate_met_by_month_end": gate_met_by_month_end,
        "target_endpoints": target_results,
        "control_month": CONTROL_MONTH,
        "control_endpoints": control_results,
        "archive_alive": archive_alive,
        "target_published": target_published,
        "cutoff_gate": gate,
        "rationale": (
            "The forward block may only advance when a published Binance archive "
            "covers a cutoff >= 2026-10-29, so that formations after 2026-09-29 "
            "have a complete 30-day outcome. A 404 on the target month is a "
            "genuine availability signal only when the archive is alive around "
            "it (control month must return HTTP 200)."
        ),
    }

    out_dir = ROOT / "research_state" / "cutoff_probe"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = record["probe_utc"].replace(":", "").replace("-", "")
    out_path = out_dir / f"cutoff_probe_{stamp}.json"
    out_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")

    # The summary line is only trustworthy when the record it names actually
    # exists on disk. probe_month is mocked in the test suite and Path.write_text
    # is mocked to a no-op, so a naive print would emit a fake "record" path and
    # a fake UNBLOCKED line that looks exactly like a live gate decision. Real
    # runs write the file and out_path.exists() is True; mocked runs report
    # record: null instead of inventing a path.
    record_path = str(out_path.relative_to(ROOT)) if out_path.exists() else None

    print(json.dumps({
        "probe_month": target,
        "target_published": target_published,
        "control_month": CONTROL_MONTH,
        "control_ok": control_ok,
        "archive_alive": archive_alive,
        "gate_met_by_month_end": gate_met_by_month_end,
        "cutoff_gate": gate,
        "record": record_path,
    }, indent=2))
    return 0 if gate == "UNBLOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())