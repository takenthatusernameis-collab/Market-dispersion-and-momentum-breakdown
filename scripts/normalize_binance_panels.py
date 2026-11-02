"""Normalize binance panel CSVs from already-saved raw zips with explicit headers.

Reads artifacts/.../data/raw/binance/{klines,funding}/{SYMBOL}/*.zip and writes
artifacts/.../data/panels/binance_{kind}_{SYMBOL}.csv with a canonical header
and (for funding) a symbol column. No re-download; idempotent.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-001"
RAW_DIR = ROOT / "artifacts" / EXP / "data" / "raw" / "binance"
PANEL_DIR = ROOT / "artifacts" / EXP / "data" / "panels"

KLINES_HEADER = "open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore"
FUNDING_HEADER = "symbol,calc_time,funding_interval_hours,last_funding_rate"


def main() -> None:
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    total_rows = 0
    for kind, header in (("klines", KLINES_HEADER), ("funding", FUNDING_HEADER)):
        by_symbol: dict[str, list[str]] = {}
        # Sort by (year, month) from the filename, not by the month suffix
        # alone: splitting "MATICUSDT-klines-2026-10.zip" on "-" and taking
        # the last element ("10.zip") groups every year's October together, so
        # the concatenated panel would read 2023-01, 2024-01, 2025-01, 2026-01,
        # 2023-02, ... instead of chronological order.
        def _ym_key(p: Path) -> tuple[int, int]:
            parts = p.stem.split("-")
            return int(parts[-2]), int(parts[-1].split(".")[0])

        for z in sorted(RAW_DIR.glob(f"{kind}/*/*.zip"), key=_ym_key):
            symbol = z.parent.name
            with zipfile.ZipFile(z) as zf:
                csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
                if not csv_names:
                    continue
                text = zf.read(csv_names[0]).decode("utf-8")
            lines = [l for l in text.splitlines() if l.strip()]
            if lines and lines[0].startswith(("open_time,", "calc_time,", "symbol,")):
                lines = lines[1:]
            by_symbol.setdefault(symbol, []).extend(lines)
            total_rows += len(lines)

        for symbol, lines in by_symbol.items():
            panel_path = PANEL_DIR / f"binance_{kind}_{symbol}.csv"
            # The Binance fundingRate archive ships 3 columns
            # (calc_time,funding_interval_hours,last_funding_rate) with no symbol
            # column, but the panel header is 4 columns and every downstream reader
            # (pandas, build_universe, eval_forward_block) expects the symbol in
            # column 0. Prefix every funding row with the symbol so the header and
            # the data agree; without this the symbol int lands in calc_time and
            # last_funding_rate parses as NaN.
            prefixed = (
                [f"{symbol},{l}" for l in lines] if kind == "funding" else lines
            )
            panel_path.write_text(header + "\n" + "\n".join(prefixed) + "\n")

    print(f"[normalize] wrote per-symbol klines+funding panels, {total_rows} total data rows")
    print(f"[normalize] panels dir: {PANEL_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
