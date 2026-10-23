"""Build the point-in-time, descending market-cap universe.

Inputs:
  - artifacts/.../data/panels/marketcap_panel.csv  (CoinMetrics CapMrkt*)
  - artifacts/.../data/panels/binance_klines_<SYMBOL>.csv
  - artifacts/.../data/panels/binance_funding_<SYMBOL>.csv

Outputs:
  - artifacts/.../data/panels/universe_coverage.csv   per (date, asset) coverage
  - artifacts/.../data/panels/price_panel.csv         date, asset, close
  - artifacts/.../data/panels/funding_panel.csv       date, asset, funding_rate
  - artifacts/.../data/panels/universe_manifest.json  coverage stats

Point-in-time rules:
  - Eligibility at formation date T requires a market-cap observation on T
    (no forward-fill) AND a listed perpetual (price) on T.
  - A contract enters from its actual listing date (first price observation)
    and stops after its last price observation (delisting). No backfill.
  - Rank eligible assets by CapMrktEstUSD descending; ties by asset id asc.
"""

from __future__ import annotations

import glob
import json
import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-002"
PANEL_DIR = ROOT / "artifacts" / EXP / "data" / "panels"

# CoinMetrics asset -> Binance USD-M perpetual symbol.
SYMBOL_MAP = {
    "btc": "BTCUSDT", "eth": "ETHUSDT", "sol": "SOLUSDT", "bnb": "BNBUSDT",
    "xrp": "XRPUSDT", "ada": "ADAUSDT", "doge": "DOGEUSDT", "dot": "DOTUSDT",
    "matic": "MATICUSDT", "avax": "AVAXUSDT", "link": "LINKUSDT", "uni": "UNIUSDT",
    "ltc": "LTCUSDT", "bch": "BCHUSDT", "etc": "ETCUSDT", "xlm": "XLMUSDT",
    "atom": "ATOMUSDT", "algo": "ALGOUSDT", "vet": "VETUSDT", "fil": "FILUSDT",
    "trx": "TRXUSDT", "eos": "EOSUSDT", "neo": "NEOUSDT", "iost": "IOSTUSDT",
    "qtum": "QTUMUSDT", "zec": "ZECUSDT", "dash": "DASHUSDT", "rune": "RUNEUSDT",
}
SYMBOL_TO_ASSET = {v: k for k, v in SYMBOL_MAP.items()}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_marketcap() -> pd.DataFrame:
    p = PANEL_DIR / "marketcap_panel.csv"
    df = pd.read_csv(p, dtype={"CapMrktCurUSD": str, "CapMrktEstUSD": str})
    df["date"] = df["date"].astype(str).str.slice(0, 10)
    df["CapMrktEstUSD"] = pd.to_numeric(df["CapMrktEstUSD"], errors="coerce")
    df["CapMrktCurUSD"] = pd.to_numeric(df["CapMrktCurUSD"], errors="coerce")
    df = df.rename(columns={"asset": "asset_id"})
    return df[["date", "asset_id", "CapMrktEstUSD", "CapMrktCurUSD"]]


def load_binance_panel(kind: str) -> pd.DataFrame:
    """kind in {klines, funding}. Concat per-symbol CSVs, map symbol->asset."""
    frames = []
    for p in sorted(PANEL_DIR.glob(f"binance_{kind}_*.csv")):
        symbol = p.stem.replace(f"binance_{kind}_", "")
        asset = SYMBOL_TO_ASSET.get(symbol)
        if asset is None:
            continue
        df = pd.read_csv(p)
        if kind == "klines":
            df = df.rename(columns={"open_time": "ts"})
            df["date"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
            df["close"] = pd.to_numeric(df["close"], errors="coerce")
            out = df[["date", "close"]].copy()
        else:
            df = df.rename(columns={"calc_time": "ts", "last_funding_rate": "funding_rate"})
            df["date"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
            df["funding_rate"] = pd.to_numeric(df["funding_rate"], errors="coerce")
            out = df[["date", "funding_rate"]].copy()
        out["asset_id"] = asset
        frames.append(out)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def build_universe() -> None:
    mc = load_marketcap()
    px = load_binance_panel("klines")
    fd = load_binance_panel("funding")

    mc.to_csv(PANEL_DIR / "marketcap_panel_long.csv", index=False)
    px.to_csv(PANEL_DIR / "price_panel.csv", index=False)
    fd.to_csv(PANEL_DIR / "funding_panel.csv", index=False)

    # Presence flags per (date, asset).
    mc_p = mc.assign(has_market_cap=True)[["date", "asset_id", "has_market_cap",
                                           "CapMrktEstUSD", "CapMrktCurUSD"]].drop_duplicates(
        ["date", "asset_id"])
    px_p = px.assign(has_price=True)[["date", "asset_id", "has_price"]].drop_duplicates(
        ["date", "asset_id"])
    fd_p = fd.assign(has_funding=True)[["date", "asset_id", "has_funding"]].drop_duplicates(
        ["date", "asset_id"])

    all_dates = sorted(set(mc["date"]) | set(px["date"]))
    all_assets = sorted(set(mc["asset_id"]) | set(px["asset_id"]))

    # Full (date x asset) grid.
    grid = pd.MultiIndex.from_product([all_dates, all_assets], names=["date", "asset_id"]).to_frame(index=False)

    cov = grid.merge(mc_p, on=["date", "asset_id"], how="left") \
              .merge(px_p, on=["date", "asset_id"], how="left") \
              .merge(fd_p, on=["date", "asset_id"], how="left")

    cov["has_market_cap"] = cov["has_market_cap"].fillna(False)
    cov["has_price"] = cov["has_price"].fillna(False)
    cov["has_funding"] = cov["has_funding"].fillna(False)

    # Contract lifecycle from price panel (actual listing/delisting dates).
    lifecycle = (
        px.groupby("asset_id")["date"]
        .agg(listing_date="min", delisting_date="max")
        .reset_index()
    )
    cov = cov.merge(lifecycle, on="asset_id", how="left")

    def exclusion_reason(r):
        if not r["has_market_cap"]:
            return "no_market_cap_observation"
        if not r["has_price"]:
            if pd.isna(r["listing_date"]):
                return "no_perpetual_contract"
            if r["date"] < r["listing_date"]:
                return "not_yet_listed"
            return "delisted"
        return ""

    cov["exclusion_reason"] = cov.apply(exclusion_reason, axis=1)
    cov["eligible"] = cov["has_market_cap"] & cov["has_price"]
    cov["included"] = cov["eligible"]

    # Historical rank among eligible assets per date: desc CapMrktEstUSD, tie asset asc.
    cov["rank"] = pd.NA
    elig_mask = cov["eligible"]
    if elig_mask.any():
        ranks = (
            cov[elig_mask]
            .sort_values(["date", "CapMrktEstUSD", "asset_id"],
                         ascending=[True, False, True])
            .groupby("date")
            .cumcount() + 1
        )
        cov.loc[elig_mask, "rank"] = ranks.values

    cov["contract_symbol"] = cov["asset_id"].map(SYMBOL_MAP)
    cov["rank"] = cov["rank"].astype("Int64")

    cov = cov[["date", "rank", "asset_id", "contract_symbol", "CapMrktEstUSD",
               "CapMrktCurUSD", "eligible", "has_price", "has_funding",
               "included", "exclusion_reason"]]
    cov["eligible"] = cov["eligible"].map({True: "yes", False: "no"})
    cov["has_price"] = cov["has_price"].map({True: "yes", False: "no"})
    cov["has_funding"] = cov["has_funding"].map({True: "yes", False: "no"})
    cov["included"] = cov["included"].map({True: "yes", False: "no"})

    cov_path = PANEL_DIR / "universe_coverage.csv"
    cov.to_csv(cov_path, index=False)
    cov_sha = sha256_file(cov_path)

    eligible_by_date = cov[cov["eligible"] == "yes"].groupby("date")["asset_id"].count()
    stats = {
        "experiment_id": EXP,
        "universe_coverage_path": str(cov_path.relative_to(ROOT)),
        "universe_coverage_sha256": cov_sha,
        "n_dates": int(len(all_dates)),
        "date_first": all_dates[0],
        "date_last": all_dates[-1],
        "n_assets": int(len(all_assets)),
        "assets": all_assets,
        "eligible_assets_per_date": {
            "mean": float(eligible_by_date.mean()),
            "min": int(eligible_by_date.min()),
            "max": int(eligible_by_date.max()),
            "median": float(eligible_by_date.median()),
        },
        "total_rows": int(len(cov)),
        "eligible_rows": int((cov["eligible"] == "yes").sum()),
        "price_panel_path": str((PANEL_DIR / "price_panel.csv").relative_to(ROOT)),
        "funding_panel_path": str((PANEL_DIR / "funding_panel.csv").relative_to(ROOT)),
    }
    (PANEL_DIR / "universe_manifest.json").write_text(
        json.dumps(stats, indent=2, sort_keys=True) + "\n"
    )
    print(f"[universe] coverage -> {cov_path.relative_to(ROOT)} sha={cov_sha[:12]}")
    print(f"[universe] dates={stats['n_dates']} {stats['date_first']}->{stats['date_last']} "
          f"assets={stats['n_assets']} "
          f"eligible/date mean={stats['eligible_assets_per_date']['mean']:.1f} "
          f"min={stats['eligible_assets_per_date']['min']} "
          f"max={stats['eligible_assets_per_date']['max']}")
    print(f"[universe] manifest -> artifacts/{EXP}/data/panels/universe_manifest.json")


if __name__ == "__main__":
    build_universe()
