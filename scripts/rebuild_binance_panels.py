#!/usr/bin/env python3
"""Rebuild per-symbol Binance panels from the raw zips already saved on disk.

The Binance Public Data Archive publishes monthly zips per symbol. The refresh
pipeline (refresh_free_data.py) downloads them and writes both the raw zips and
the normalized panels, but a partial refresh (e.g. ``--binance-assets btc,eth``)
rewrites only the requested symbols' panels while leaving the other panels at
their previous cutoff. The raw zips for the untouched symbols may already cover
a later month than their panels do, so the on-disk state becomes internally
inconsistent: a panel that ends 2026-09-30 sits next to a raw zip for 2026-10.

This script closes that gap WITHOUT re-downloading anything. It walks
artifacts/<experiment>/data/raw/binance/{klines,funding} and rewrites every
panel from the zips that are actually present, in ascending month order, with the
canonical header and (for funding) the symbol column prefixed. It is idempotent
and deterministic: re-running it reproduces the same bytes.

It is a data-normalization tool, not an evaluation input. It does not touch the
canonical forward block, the grid ledger, DISPERSION-001/002 or any frozen
artifact.

Usage:
    python3 scripts/rebuild_binance_panels.py [--experiment EXP]
"""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

KLINES_HEADER = (
    "open_time,open,high,low,close,volume,close_time,quote_volume,count,"
    "taker_buy_volume,taker_buy_quote_volume,ignore"
)
FUNDING_HEADER = "symbol,calc_time,funding_interval_hours,last_funding_rate"


def rebuild(exp: str) -> int:
    raw_root = ROOT / "artifacts" / exp / "data" / "raw" / "binance"
    panel_dir = ROOT / "artifacts" / exp / "data" / "panels"
    panel_dir.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    written_panels = 0
    for kind, header in (("klines", KLINES_HEADER), ("funding", FUNDING_HEADER)):
        zips = sorted(raw_root.glob(f"{kind}/*/*.zip"))
        if not zips:
            print(f"[rebuild] no {kind} zips under {raw_root.relative_to(ROOT)}")
            continue
        by_symbol: dict[str, list[str]] = {}
        # Sort by (year, month) extracted from the filename, NOT by the month
        # suffix alone. A stem like MATICUSDT-klines-2026-10.zip splits on "-"
        # to [..., "2026", "10.zip"], and sorting by the last element ("10.zip")
        # groups every year's October together, so the concatenated panel would
        # read 2023-01, 2024-01, 2025-01, 2026-01, 2023-02, ... — wrong order.
        # The forward-block evaluator re-sorts by timestamp, so outcomes are
        # unaffected, but the panel convention is chronological and the manifest
        # boundaries are derived from it.
        def _ym_key(p: Path) -> tuple[int, int]:
            stem = p.stem  # e.g. MATICUSDT-klines-2026-10
            parts = stem.split("-")
            return int(parts[-2]), int(parts[-1].split(".")[0])

        for z in sorted(zips, key=_ym_key):
            symbol = z.parent.name
            with zipfile.ZipFile(z) as zf:
                csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
                if not csv_names:
                    continue
                text = zf.read(csv_names[0]).decode("utf-8")
            lines = [ln for ln in text.splitlines() if ln.strip()]
            if lines and lines[0].startswith(("open_time,", "calc_time,", "symbol,")):
                lines = lines[1:]
            by_symbol.setdefault(symbol, []).extend(lines)
            total_rows += len(lines)

        for symbol, lines in by_symbol.items():
            prefixed = [f"{symbol},{ln}" for ln in lines] if kind == "funding" else lines
            out = panel_dir / f"binance_{kind}_{symbol}.csv"
            out.write_text(header + "\n" + "\n".join(prefixed) + "\n")
            written_panels += 1

    print(f"[rebuild] wrote {written_panels} panels, {total_rows} total data rows")
    print(f"[rebuild] panels -> {panel_dir.relative_to(ROOT)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--experiment", default="HARMONY-CRYPTO-EDGE-004-DISPERSION-003")
    args = ap.parse_args()
    return rebuild(args.experiment)


if __name__ == "__main__":
    raise SystemExit(main())