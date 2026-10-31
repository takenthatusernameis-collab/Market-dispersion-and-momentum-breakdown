#!/usr/bin/env python3
"""Rebuild the per-symbol Binance funding panels from ALL saved raw zips (no re-download).

Red-team finding (2026-10-31): the committed ``binance_funding_*.csv`` panels hold
only the LAST monthly archive's rows. ``repair_funding_panels.py`` (2026-10-25)
rebuilt the panels to fix a header/column-count defect, but it iterated
``RAW_DIR.glob("*/*.zip")`` and wrote one output file per zip, so each panel was
overwritten by the final zip in iteration order -- 90 rows spanning
2026-09-01..2026-09-29 instead of the full 45-month window
(4152 rows for BTCUSDT, 2023-01-01..2026-09-29). The manifest's
``date_first`` was then computed from the truncated panel (1788220800005 =
2026-09-01) rather than the true first observation (1672531200000 = 2023-01-01),
while ``date_last`` and ``rows`` happened to be right. This is the same class of
provenance defect as the CoinMetrics manifest boundary inversion fixed on
2026-10-30: a boundary field that no test was checking.

This script rewrites each panel by concatenating every saved zip for that symbol
in month order (ascending), with the symbol column prefixed. It is idempotent:
re-running it reproduces the same bytes. No network, no secrets, no trading.

Free-data-only.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
RAW_DIR = ROOT / "artifacts" / EXP / "data" / "raw" / "binance" / "funding"
PANEL_DIR = ROOT / "artifacts" / EXP / "data" / "panels"

FUNDING_HEADER = "symbol,calc_time,funding_interval_hours,last_funding_rate"


def month_key(path: Path) -> str:
    """Return the ``YYYY-MM`` suffix of a funding zip filename."""
    return path.stem.split("-")[-1]


def rebuild() -> int:
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    zips = sorted(RAW_DIR.glob("*/*.zip"), key=lambda p: month_key(p))
    if not zips:
        print("[fix-funding] no funding zips found under", RAW_DIR.relative_to(ROOT))
        return 1

    total_rows = 0
    written = 0
    by_symbol: dict[str, list[str]] = {}
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
        by_symbol.setdefault(symbol, []).extend(lines)

    for symbol, lines in by_symbol.items():
        prefixed = [f"{symbol},{ln}" for ln in lines]
        out = PANEL_DIR / f"binance_funding_{symbol}.csv"
        out.write_text(FUNDING_HEADER + "\n" + "\n".join(prefixed) + "\n")
        total_rows += len(prefixed)
        written += 1

    print(f"[fix-funding] rebuilt {written} funding panels, {total_rows} total data rows")
    print(f"[fix-funding] panels -> {PANEL_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(rebuild())