#!/usr/bin/env python3
"""Recompute data_refresh_provenance.json's Binance series from the panel CSVs.

The provenance record duplicates the binance_panel_manifest's per-series
boundary/rows fields. When the panels are rebuilt from the raw zips
(rebuild_binance_panels.py) and the manifest regenerated
(regenerate_binance_manifest.py) to cover the full 32-symbol set, the provenance
record -- last written by a partial ``--binance-assets btc,eth`` refresh -- still
describes only BTCUSDT/ETHUSDT. The two artifacts then disagree, and the
refresh-provenance regression test (test_refresh_provenance_boundaries.py) flags
it.

This script recomputes every binance series in the provenance from the panel
CSVs themselves (the single source of truth the evaluator reads), preserving
the record's other fields (fetch_utc, coinmetrics summary, auth, sources,
point_in_time). Idempotent: re-running it reproduces the same bytes.

It does NOT touch the canonical forward block, the grid ledger, DISPERSION-001/002
or any frozen artifact.

Usage:
    python3 scripts/repair_refresh_provenance_binance.py [--experiment EXP]
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
    prov_path = panels / "data_refresh_provenance.json"
    manifest = json.loads((panels / "binance_panel_manifest.json").read_text())

    prov = json.loads(prov_path.read_text(encoding="utf-8"))
    prov_series = {f"{s['kind']}:{s['symbol']}": s for s in prov["binance"]["series"]}
    man_series = {f"{s['kind']}:{s['symbol']}": s for s in manifest["series"]}

    new_series = []
    changed = 0
    for key, m in man_series.items():
        kind, symbol = key.split(":")
        first, last, n = series_stats(kind, symbol, panels)
        old = prov_series.get(key)
        entry = {
            "asset": m["asset"],
            "symbol": m["symbol"],
            "kind": m["kind"],
            "date_first": str(first),
            "date_last": str(last),
            "rows": n,
        }
        if old is None or old != entry:
            changed += 1
        new_series.append(entry)

    prov["binance"]["series"] = new_series
    prov_path.write_text(json.dumps(prov, indent=2, sort_keys=True) + "\n")
    print(f"[repair-provenance] recomputed {len(new_series)} binance series, "
          f"{changed} changed -> {prov_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())