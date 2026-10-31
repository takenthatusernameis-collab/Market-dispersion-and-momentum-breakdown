#!/usr/bin/env python3
"""Recompute Binance panel manifest boundary/rows fields from the panel CSVs.

The committed ``binance_panel_manifest.json`` carries per-series ``date_first``,
``date_last`` and ``rows`` that were derived from the panel at a time when the
funding panels held only the final month's rows (see
fix_funding_panel_rows.py). The panels are now rebuilt from all saved zips, so
the manifest fields are stale: ``date_first`` for the two funding series reads
2026-09-01 instead of 2023-01-01, and ``rows`` counts raw-archive newlines
(including per-month header rows) rather than the data rows actually written to
the panel CSV.

This script recomputes each field from the panel CSV itself (the same source
the downstream evaluator reads), so the manifest can no longer disagree with
the data it describes. Idempotent. No network, no secrets, no trading.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
PANELS = ROOT / "artifacts" / EXP / "data" / "panels"
MANIFEST_PATH = PANELS / "binance_panel_manifest.json"

KIND_COL = {"klines": "open_time", "funding": "calc_time"}


def series_stats(kind: str, symbol: str) -> tuple[int, int, int]:
    """Return (date_first, date_last, rows) for one panel CSV."""
    path = PANELS / f"binance_{kind}_{symbol}.csv"
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        col = header.index(KIND_COL[kind])
        rows = list(reader)
    ts = [int(r[col]) for r in rows]
    return min(ts), max(ts), len(rows)


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text())
    changed = []
    for s in manifest["series"]:
        kind, symbol = s["kind"], s["symbol"]
        first, last, n = series_stats(kind, symbol)
        old = (s.get("date_first"), s.get("date_last"), s.get("rows"))
        if old != (str(first), str(last), n):
            changed.append((symbol, kind, old, (str(first), str(last), n)))
        s["date_first"] = str(first)
        s["date_last"] = str(last)
        s["rows"] = n
        s["manifest_boundary_note"] = (
            "date_first/date_last/rows recomputed from the panel CSV after the "
            "funding panels were rebuilt from all saved monthly zips; previously "
            "date_first for funding series reflected the truncated final-month "
            "panel and rows counted per-month archive header lines"
        )

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"[fix-binance-manifest] recomputed {len(manifest['series'])} series; "
          f"{len(changed)} fields changed")
    for symbol, kind, old, new in changed:
        print(f"  {symbol}/{kind}: {old} -> {new}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())