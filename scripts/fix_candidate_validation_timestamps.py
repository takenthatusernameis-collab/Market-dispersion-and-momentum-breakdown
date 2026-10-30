#!/usr/bin/env python3
"""Migrate the committed candidate validation record to correct timestamp boundaries.

2026-10-30 finding: ``scripts/validate_candidate_batch.py`` recorded
``time_first``/``time_last`` as ``rows[0]``/``rows[-1]`` of the raw CoinMetrics
payload. The CoinMetrics timeseries endpoint paginates in DESCENDING time order
(page 1 opens at the request ``end_time`` and walks backwards; only the final
page is ascending), so those fields were inverted for essentially every verified
candidate. The boundaries are now computed after sorting rows by time ascending.

This script does NOT re-fetch anything. It reads the already-committed raw JSON
files under artifacts/.../data/raw/coinmetrics_candidates/, recomputes the
boundaries from their contents, and rewrites the validation record. It is
idempotent: running it when the boundaries are already correct changes nothing.

The raw files themselves are deliberately left in API order: they are hashed by
the sealed forward block (via ``raw_sha256``) and must stay byte-identical.

Free-data-only, read/write of local files only. No network, no secrets, no trading.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
VAL_PATH = ART / "data" / "panels" / "candidate_batch_validation.json"

TIME_ORDER_NOTE = (
    "boundaries computed after sorting rows by time ascending; "
    "the CoinMetrics timeseries endpoint paginates descending, "
    "so the raw file's first/last rows are not the earliest/latest"
)


def main() -> int:
    val = json.loads(VAL_PATH.read_text(encoding="utf-8"))
    entries = val["candidates_processed"]
    print(f"[migrate] {len(entries)} validation entries", flush=True)

    fixed = 0
    already = 0
    missing_raw = 0
    for e in entries:
        for metric in ("CapMrktEstUSD", "CapMrktCurUSD"):
            m = e.get("metrics", {}).get(metric)
            if not m or m.get("status") != "ok" or not m.get("raw_path"):
                continue
            raw = ROOT / m["raw_path"]
            if not raw.exists():
                missing_raw += 1
                continue
            rows = json.loads(raw.read_text(encoding="utf-8"))
            times = [r.get("time") for r in rows if r.get("time")]
            if not times:
                continue
            lo, hi = min(times), max(times)
            if m.get("time_first") == lo and m.get("time_last") == hi:
                already += 1
                continue
            m["time_first"] = lo
            m["time_last"] = hi
            m["time_order_note"] = TIME_ORDER_NOTE
            fixed += 1

    val["timestamp_boundary_correction_utc"] = (
        "2026-10-30T14:35:00Z: time_first/time_last recomputed from the raw "
        "payloads after sorting by time ascending (the CoinMetrics timeseries "
        "endpoint paginates descending). Raw files untouched."
    )
    VAL_PATH.write_text(json.dumps(val, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(f"[migrate] fixed={fixed} already_correct={already} "
          f"missing_raw={missing_raw}", flush=True)
    print(f"[migrate] validation record -> {VAL_PATH.relative_to(ROOT)}")
    return 0 if missing_raw == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())