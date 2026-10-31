#!/usr/bin/env python3
"""Recompute data_refresh_provenance.json boundary fields from the panel CSVs.

The committed ``data_refresh_provenance.json`` carries a per-source summary:

  * ``coinmetrics.date_first`` / ``date_last`` / ``panel_sha256`` / ``panel_rows``
  * ``binance.series[].date_first`` / ``date_last`` / ``rows`` per (asset, kind)

These describe the panels on disk, but they were written by
``scripts/refresh_free_data.py`` from *other* derived fields rather than from the
panels themselves:

  * the coinmetrics summary copied the manifest's per-metric
    ``CapMrktEstUSD.time_first`` / ``time_last``. Those are correct in the
    manifest (computed after sorting rows by time ascending), but they came from
    different assets: ``date_first`` from the alphabetically-first asset's
    CapMrktEstUSD time_first -- which is that asset's LATEST observation, because
    the CoinMetrics timeseries endpoint paginates descending -- and ``date_last``
    from the max CapMrktEstUSD time_last across assets, i.e. some other asset's
    EARLIEST observation. The committed summary read
    ``date_first 2026-07-16`` / ``date_last 2023-04-04``: an inverted boundary
    contradicting the panel CSV on disk, which spans 2023-01-01..2026-10-23.
  * the binance series copied the binance_panel_manifest's per-series fields, so
    when the funding panels were rebuilt from all saved monthly zips (2026-10-31)
    the manifest was repaired by fix_binance_manifest_boundaries.py but the
    provenance summary kept the old truncated-panel ``rows`` (4152 raw-archive
    newlines, including per-month header rows) instead of the 4107 data rows now
    written to the panel CSV.

Same defect class as the CoinMetrics manifest boundary inversion repaired
2026-10-30 and the Binance funding-panel truncation repaired 2026-10-31: a
provenance field describing a boundary that did not match the artifact it claimed
to describe, invisible because no test compared them.

This script recomputes every boundary/rows field from the panel CSVs themselves,
the single source of truth the downstream evaluator reads. Idempotent. No
network, no secrets, no trading. stdlib only.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
PANELS = ROOT / "artifacts" / EXP / "data" / "panels"
PROVENANCE = PANELS / "data_refresh_provenance.json"
BINANCE_MANIFEST = PANELS / "binance_panel_manifest.json"

KIND_COL = {"klines": "open_time", "funding": "calc_time"}


def _binance_stats(kind: str, symbol: str) -> tuple[int, int, int]:
    path = PANELS / f"binance_{kind}_{symbol}.csv"
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        col = header.index(KIND_COL[kind])
        rows = list(reader)
    ts = [int(r[col]) for r in rows]
    return min(ts), max(ts), len(rows)


def _cm_stats() -> tuple[str, str, str, int]:
    path = PANELS / "marketcap_panel.csv"
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(newline="", encoding="utf-8") as fh:
        dates = [r["date"] for r in csv.DictReader(fh) if r.get("date")]
    return min(dates), max(dates), sha, len(dates)


def main() -> int:
    prov = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    changed: list[str] = []

    cm = prov["coinmetrics"]
    d_first, d_last, sha, rows = _cm_stats()
    for field, old, new in (
        ("date_first", cm.get("date_first"), d_first),
        ("date_last", cm.get("date_last"), d_last),
        ("panel_sha256", cm.get("panel_sha256"), sha),
        ("panel_rows", cm.get("panel_rows"), rows),
    ):
        if old != new:
            changed.append(f"coinmetrics.{field}: {old} -> {new}")
        cm[field] = new

    # The binance series in the provenance must describe exactly the same series
    # as the binance_panel_manifest (which is itself recomputed from the CSVs by
    # fix_binance_manifest_boundaries.py), and both must agree with the CSVs.
    manifest = json.loads(BINANCE_MANIFEST.read_text(encoding="utf-8"))
    man_series = {f"{s['kind']}:{s['symbol']}": s for s in manifest["series"]}
    prov_series = prov.setdefault("binance", {}).setdefault("series", [])
    for s in prov_series:
        key = f"{s['kind']}:{s['symbol']}"
        first, last, n = _binance_stats(s["kind"], s["symbol"])
        man = man_series.get(key)
        if man is None:
            changed.append(f"binance.{key}: series missing from the manifest")
            continue
        for field, old, new in (
            ("date_first", s.get("date_first"), str(first)),
            ("date_last", s.get("date_last"), str(last)),
            ("rows", s.get("rows"), n),
        ):
            if old != new:
                changed.append(f"binance.{key}.{field}: {old} -> {new}")
            s[field] = new
        for field in ("kind", "symbol", "asset"):
            if s.get(field) != man.get(field):
                changed.append(f"binance.{key}.{field}: {s.get(field)} != manifest {man.get(field)}")
                s[field] = man[field]

    missing = set(man_series) - {f"{s['kind']}:{s['symbol']}" for s in prov_series}
    for key in sorted(missing):
        changed.append(f"binance.{key}: series in the manifest but absent from the provenance")

    PROVENANCE.write_text(json.dumps(prov, indent=2, sort_keys=True) + "\n")
    print(f"[fix-refresh-provenance] recomputed provenance; {len(changed)} fields changed")
    for line in changed:
        print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())