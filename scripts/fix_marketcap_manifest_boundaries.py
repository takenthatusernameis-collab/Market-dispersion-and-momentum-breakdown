#!/usr/bin/env python3
"""Migrate the committed CoinMetrics market-cap panel manifest to correct boundaries.

2026-10-30 finding: ``scripts/refresh_free_data.py`` recorded ``time_first`` /
``time_last`` as ``rows[0]`` / ``rows[-1]`` of the raw CoinMetrics payload. The
CoinMetrics timeseries endpoint paginates in DESCENDING time order (page 1 opens
at the request ``end_time`` and walks backwards; only the final page is
ascending), so those fields were inverted for 49 of 51 ok metric entries in
``artifacts/.../data/panels/marketcap_panel_manifest.json`` (e.g. btc
CapMrktEstUSD time_first 2026-07-16 > time_last 2023-04-02). The manifest's
top-level ``start``/``end`` are derived from the same inverted fields, so they
were inverted too (start 2023-01-01 / end 2026-10-23 happened to be correct only
because the request window was passed explicitly and the min/max happened to
coincide).

This script does NOT re-fetch anything. It reads the already-committed raw JSON
files under artifacts/.../data/raw/coinmetrics/, recomputes the boundaries from
their contents after sorting by time ascending, and rewrites the manifest. It is
idempotent: running it when the boundaries are already correct changes nothing.

The raw files themselves are deliberately left in API order: the normalized
panel CSV is hashed by the sealed forward block (via ``panel_sha256``) and must
stay byte-identical, and the raw files carry ``raw_sha256`` hashes.

Free-data-only, read/write of local files only. No network, no secrets, no trading.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
MANIFEST_PATH = ART / "data" / "panels" / "marketcap_panel_manifest.json"

TIME_ORDER_NOTE = (
    "boundaries computed after sorting rows by time ascending; "
    "the CoinMetrics timeseries endpoint paginates descending, "
    "so the raw file's first/last rows are not the earliest/latest"
)


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    fixed = 0
    already = 0
    missing_raw = 0
    unparseable = 0
    rows_fixed = 0
    rows_already = 0

    for asset, entry in manifest["asset_results"].items():
        for metric, m in entry.get("metrics", {}).items():
            if m.get("status") != "ok" or not m.get("raw_path"):
                continue
            raw = ROOT / m["raw_path"]
            if not raw.exists():
                missing_raw += 1
                continue
            try:
                rows = json.loads(raw.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                unparseable += 1
                continue
            times = [r.get("time") for r in rows if r.get("time")]
            if not times:
                continue
            lo, hi = min(times), max(times)
            if m.get("time_first") == lo and m.get("time_last") == hi:
                already += 1
            else:
                m["time_first"] = lo
                m["time_last"] = hi
                m["time_order_note"] = TIME_ORDER_NOTE
                fixed += 1
            # `rows` is raw-file provenance: it must equal the number of records
            # actually present in the archived raw file. The committed manifest
            # declared 1392 for btc_CapMrktEstUSD while the committed raw file
            # holds 1397 (the API returned rows through 2026-10-28 that never
            # reached the truncated panel). Correct it from the file on disk.
            if m.get("rows") == len(rows):
                rows_already += 1
            else:
                m["rows"] = len(rows)
                rows_fixed += 1

    # Recompute top-level start/end from the PANEL CSV, not from the raw files.
    # start/end describe the normalized panel that is hashed by the sealed
    # forward block (panel_sha256); the raw files legitimately carry extra rows
    # (see panel_raw_divergence_note) and must not drive the panel boundary.
    panel_path = ROOT / manifest["panel_path"]
    import csv
    pstarts, pends = [], []
    with panel_path.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("date"):
                pstarts.append(r["date"])
                pends.append(r["date"])
    manifest["start"] = min(pstarts) if pstarts else None
    manifest["end"] = max(pends) if pends else None
    manifest["panel_raw_divergence_note"] = (
        "The archived raw files contain rows beyond the normalized panel: the "
        "CoinMetrics timeseries request was truncated at the panel end date, but "
        "the API returned additional observations (e.g. btc_CapMrktEstUSD raw "
        "1397 rows through 2026-10-28 vs 1392 panel rows through 2026-10-23). "
        "Raw files are left byte-identical (they carry raw_sha256 provenance); "
        "panel boundaries and panel_sha256 describe the panel CSV only."
    )
    manifest["timestamp_boundary_correction_utc"] = (
        "2026-10-30T22:15:00Z: time_first/time_last recomputed from the raw "
        "payloads after sorting by time ascending (the CoinMetrics timeseries "
        "endpoint paginates descending); `rows` corrected to the actual record "
        "count in each archived raw file; top-level start/end recomputed from "
        "the panel CSV. Raw files and panel CSV untouched."
    )

    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[migrate] boundaries fixed={fixed} already_correct={already} "
          f"missing_raw={missing_raw} unparseable={unparseable}", flush=True)
    print(f"[migrate] rows corrected={rows_fixed} already_correct={rows_already}")
    print(f"[migrate] panel start={manifest['start']} end={manifest['end']}")
    print(f"[migrate] manifest -> {MANIFEST_PATH.relative_to(ROOT)}")
    return 0 if (missing_raw == 0 and unparseable == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())