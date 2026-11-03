#!/usr/bin/env python3
"""Add binance series to data_refresh_provenance.json that are in the manifest
but absent from the provenance (2026-11-03 refresh extended the panel set to all
32 symbols, but the provenance summary still described only BTCUSDT/ETHUSDT).

The provenance's binance.series is a per-(asset,kind) boundary/rows summary that
must describe exactly the same series as binance_panel_manifest.json. This script
copies the missing series entries from the manifest (which is itself recomputed
from the panel CSVs by regenerate_binance_manifest.py) and then the caller runs
fix_refresh_provenance_boundaries.py to recompute every boundary from the CSVs.

Idempotent. No network, no secrets, no trading. stdlib only.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
PANELS = ROOT / "artifacts" / EXP / "data" / "panels"
PROVENANCE = PANELS / "data_refresh_provenance.json"
MANIFEST = PANELS / "binance_panel_manifest.json"


def main() -> int:
    prov = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    man_series = {f"{s['kind']}:{s['symbol']}": s for s in manifest["series"]}

    prov_series = prov.setdefault("binance", {}).setdefault("series", [])
    prov_keys = {f"{s['kind']}:{s['symbol']}" for s in prov_series}
    missing = sorted(set(man_series) - prov_keys)

    for key in missing:
        m = dict(man_series[key])
        # The provenance entry carries the raw-archive provenance (months, raw_dir)
        # that refresh_free_data.py records; the manifest entry does not. Keep only
        # the identity + boundary fields, which fix_refresh_provenance_boundaries.py
        # recomputes from the CSVs anyway.
        prov_series.append({
            "asset": m["asset"],
            "symbol": m["symbol"],
            "kind": m["kind"],
            "date_first": m["date_first"],
            "date_last": m["date_last"],
            "rows": m["rows"],
        })

    PROVENANCE.write_text(json.dumps(prov, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[add-binance-series] added {len(missing)} missing series -> "
          f"{len(prov_series)} total in provenance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())