#!/usr/bin/env python3
"""Rebuild the per-symbol Binance funding panels from the already-saved raw zips.

Red-team finding (2026-10-25): every committed ``binance_funding_*.csv`` panel
carried a 4-column header (``symbol,calc_time,funding_interval_hours,
last_funding_rate``) but 3-column data rows from the Binance fundingRate archive
(``calc_time,funding_interval_hours,last_funding_rate``). pandas therefore read
the symbol integer into ``calc_time`` and left ``last_funding_rate`` NaN for all
32 symbols -- i.e. the funding leg of the data gate reported 100% coverage while
the actual field was entirely missing. The forward-block evaluator loads the
funding panels into ``fd`` and never uses them, so the canonical block outcomes
are unaffected, but the artifact was wrong and the manifest's ``funding_source:
verified`` claim was unsupported.

This script rewrites each panel from the raw zips that are already on disk (no
re-download, no network) with the symbol column correctly prefixed. It is
idempotent: re-running it reproduces the same bytes.

Free-data-only. No API keys, no secrets, no trading.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
RAW_DIR = ROOT / "artifacts" / EXP / "data" / "raw" / "binance" / "funding"
PANEL_DIR = ROOT / "artifacts" / EXP / "data" / "panels"

FUNDING_HEADER = "symbol,calc_time,funding_interval_hours,last_funding_rate"


def rebuild() -> int:
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    zips = sorted(RAW_DIR.glob("*/*.zip"))
    if not zips:
        print("[repair] no funding zips found under", RAW_DIR.relative_to(ROOT))
        return 1

    total_rows = 0
    written = 0
    for z in zips:
        symbol = z.parent.name
        with zipfile.ZipFile(z) as zf:
            csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
            if not csv_names:
                continue
            text = zf.read(csv_names[0]).decode("utf-8")
        lines = [ln for ln in text.splitlines() if ln.strip()]
        if lines and lines[0].startswith("calc_time,"):
            lines = lines[1:]
        # Prefix the 3-column archive row with the symbol so it lines up with the
        # 4-column header. See module docstring for why this was previously missed.
        prefixed = [f"{symbol},{ln}" for ln in lines]
        out = PANEL_DIR / f"binance_funding_{symbol}.csv"
        out.write_text(FUNDING_HEADER + "\n" + "\n".join(prefixed) + "\n")
        total_rows += len(prefixed)
        written += 1

    print(f"[repair] rebuilt {written} funding panels, {total_rows} data rows")
    print(f"[repair] panels -> {PANEL_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(rebuild())