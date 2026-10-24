#!/usr/bin/env python3
"""Evaluate the DISPERSION-003 primary anchor H004V106 on the sealed forward block.

Forward block: formation dates beginning 2025-01-01 through the latest fully
closed UTC daily candle frozen at preregistration time. Only the preselected
anchor is evaluated; no parameter, asset, threshold, or cost search is
performed on this block.

Free-data-only: reads panels under artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/.
No API keys, no secrets, no trading.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
PANEL_DIR = ART / "data" / "panels"
OUT_DIR = ART / "forward_block"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_COST_TURN = 0.0005
COST_1X = BASE_COST_TURN * 2.0
MIN_ASSETS_DECILES = 20
FORWARD_BLOCK_START = "2025-01-01"

# Anchor H004V106 parameters (frozen from grid manifest).
ANCHOR_ID = "H004V106"
ANCHOR_PARAMS = {
    "momentum_lookback_days": 30,
    "forward_horizon_days": 30,
    "dispersion_estimator": "cross_sectional_population_stddev",
    "dispersion_window_days": 365,
    "dispersion_state_rule": "trailing_window_outer_deciles",
    "universe_arm": "expanding_point_in_time",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate H004V106 on the sealed forward block.")
    p.add_argument("--data-cutoff", default=None,
                   help="latest fully closed UTC daily candle, e.g. 2026-10-29. "
                        "If omitted, derived from the Binance kline panels.")
    p.add_argument("--min-horizon-days", type=int, default=30,
                   help="minimum completed forward-horizon days required after the "
                        "last formation date (default 30). Formations whose horizon "
                        "is not fully observed are excluded.")
    return p.parse_args()


def derive_data_cutoff(px: dict[str, pd.DataFrame]) -> str:
    """Latest fully closed UTC daily candle across all Binance kline panels."""
    latest = None
    for df in px.values():
        dates = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
        d = dates.max()
        if d > (latest or ""):
            latest = d
    return latest


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_marketcap() -> pd.DataFrame:
    p = PANEL_DIR / "marketcap_panel.csv"
    df = pd.read_csv(p, dtype={"CapMrktCurUSD": str, "CapMrktEstUSD": str})
    df["date"] = df["date"].astype(str).str.slice(0, 10)
    df["CapMrktEstUSD"] = pd.to_numeric(df["CapMrktEstUSD"], errors="coerce")
    return df[["date", "asset", "CapMrktEstUSD"]]


def load_binance_panel(kind: str) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for p in sorted(PANEL_DIR.glob(f"binance_{kind}_*.csv")):
        symbol = p.stem.replace(f"binance_{kind}_", "")
        df = pd.read_csv(p)
        if kind == "klines":
            df = df.rename(columns={"open_time": "ts"})
            df["date"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
            df["close"] = pd.to_numeric(df["close"], errors="coerce")
            out[symbol] = df[["date", "close"]].copy()
        else:
            df = df.rename(columns={"calc_time": "ts", "last_funding_rate": "funding_rate"})
            df["date"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
            df["funding_rate"] = pd.to_numeric(df["funding_rate"], errors="coerce")
            out[symbol] = df[["date", "funding_rate"]].copy()
    return out


def build_eligibility_map(mc: pd.DataFrame, px: dict[str, pd.DataFrame]) -> dict[str, dict]:
    asset_to_symbol: dict[str, str] = {}
    for symbol in px:
        if symbol.endswith("USDT"):
            asset = symbol[:-4].lower()
            asset_to_symbol[asset] = symbol

    px_dates: dict[str, set[str]] = {}
    for symbol, df_px in px.items():
        px_dates[symbol] = set(df_px["date"].astype(str).str.slice(0, 10).unique())

    mc_dates = sorted(mc["date"].unique())
    result: dict[str, dict] = {}
    for d in mc_dates:
        mc_d = mc[mc["date"] == d][["asset", "CapMrktEstUSD"]].dropna()
        elig: dict[str, float] = {}
        for _, r in mc_d.iterrows():
            asset = r["asset"]
            symbol = asset_to_symbol.get(asset)
            if symbol is None:
                continue
            if d not in px_dates.get(symbol, set()):
                continue
            cap = float(r["CapMrktEstUSD"])
            if math.isnan(cap):
                continue
            elig[asset] = cap
        if elig:
            result[d] = elig
    return result


def build_price_wide_all(px: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frames = []
    for symbol, df_px in px.items():
        df = df_px[["date", "close"]].copy()
        asset = symbol[:-4].lower() if symbol.endswith("USDT") else symbol.lower()
        df = df.rename(columns={"close": asset})
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    merged = frames[0]
    for f in frames[1:]:
        merged = merged.merge(f, on="date", how="outer")
    merged["date"] = pd.to_datetime(merged["date"], utc=True)
    merged = merged.sort_values("date").set_index("date")
    return merged


class MomentumCache:
    """Cumulative momentum over DAILY RETURNS, not raw price levels.

    A cumulative product of (1 + price) across the cross-section multiplies
    dollar magnitudes (1e9-1e12 per asset), so the resulting "momentum" is
    dominated by price level and the cross-sectional dispersion is ~1e128. The
    decile split then ranks by price level, not by return dispersion, and the
    dispersion-state thresholds are meaningless. Daily returns are used here.
    """

    def __init__(self, px_wide: pd.DataFrame):
        self.px_wide = px_wide
        self.returns_wide = px_wide.pct_change()
        self._cache: dict[tuple, pd.Series] = {}

    def get(self, end_date: str, lookback: int, assets: tuple[str, ...]) -> pd.Series:
        key = (end_date, lookback, assets)
        if key in self._cache:
            return self._cache[key]
        idx = self.px_wide.index
        if end_date not in idx:
            self._cache[key] = pd.Series(dtype=float)
            return self._cache[key]
        end_loc = idx.get_loc(end_date)
        start_loc = end_loc - lookback + 1
        if start_loc < 0:
            self._cache[key] = pd.Series(dtype=float)
            return self._cache[key]
        window = self.returns_wide.iloc[start_loc:end_loc + 1]
        sub = window[list(assets)]
        complete = sub.notna().all(axis=0)
        assets_c = sub.columns[complete].tolist()
        if not assets_c:
            self._cache[key] = pd.Series(dtype=float)
            return self._cache[key]
        comp = (1.0 + sub[assets_c]).prod() - 1.0
        self._cache[key] = comp
        return comp


def compute_dispersion(mom: pd.Series, estimator: str) -> float:
    if estimator == "cross_sectional_population_stddev":
        return float(mom.std(ddof=0))
    if estimator == "scaled_median_absolute_deviation_1_4826":
        med = float(mom.median())
        mad = float((mom - med).abs().median())
        return 1.4826 * mad
    raise ValueError(f"unknown estimator {estimator}")


def portfolio_spread(mom: pd.Series, rule: str) -> tuple[list[str], list[str]]:
    ranked = mom.sort_values(ascending=False)
    ranked = ranked.reindex(sorted(ranked.index, key=lambda a: (-ranked[a], a)))
    n = len(ranked)
    if rule == "trailing_window_outer_deciles":
        k = n // 10
        if k < 2:
            return [], []
        return ranked.head(k).index.tolist(), ranked.tail(k).index.tolist()
    return [], []


def forward_returns(px_wide: pd.DataFrame, T: str, horizon: int,
                    assets: list[str]) -> dict[str, float]:
    if T not in px_wide.index:
        return {}
    idx = px_wide.index
    T_loc = idx.get_loc(T)
    window = px_wide.iloc[T_loc + 1:T_loc + horizon + 1]
    if window.empty:
        return {}
    out = {}
    for a in assets:
        if a not in window.columns:
            continue
        s = window[a].dropna()
        if len(s) == 0:
            continue
        out[a] = float(s.iloc[-1] / s.iloc[0] - 1.0)
    return out


def main() -> int:
    args = parse_args()
    mc = load_marketcap()
    px = load_binance_panel("klines")
    fd = load_binance_panel("funding")

    px_wide = build_price_wide_all(px)
    mom_cache = MomentumCache(px_wide)

    elig_map = build_eligibility_map(mc, px)

    data_cutoff = args.data_cutoff or derive_data_cutoff(px)
    horizon = ANCHOR_PARAMS["forward_horizon_days"]
    min_horizon = args.min_horizon_days
    if horizon < min_horizon:
        raise ValueError(f"forward horizon {horizon} below min_horizon_days {min_horizon}")

    # A formation is only evaluable if its full forward horizon is completed by
    # the data cutoff. This is what makes the block genuinely sealed: the last
    # formation date is data_cutoff - horizon days, not the raw last panel date.
    idx = px_wide.index
    cutoff_ts = pd.Timestamp(data_cutoff, tz="UTC")
    if cutoff_ts not in idx:
        raise ValueError(f"data cutoff {data_cutoff} is not a panel observation date")
    cutoff_loc = idx.get_loc(cutoff_ts)
    last_allowed_loc = cutoff_loc - horizon
    last_allowed_date = idx[last_allowed_loc] if last_allowed_loc >= 0 else None
    last_allowed_str = last_allowed_date.strftime("%Y-%m-%d") if last_allowed_date is not None else None

    # Freeze input data hashes before computing outcomes.
    input_files = {}
    for p in sorted(PANEL_DIR.iterdir()):
        if p.is_file():
            input_files[p.name] = sha256_file(p)

    # Also hash the manifest and config.
    input_files["grid_config_manifest.json"] = sha256_file(
        ART / "grid_config_manifest.json"
    )
    input_files["grid_result_ledger.json"] = sha256_file(
        ART / "grid_result_ledger.json"
    )

    freeze_record = {
        "experiment_id": EXP,
        "anchor_id": ANCHOR_ID,
        "anchor_parameters": ANCHOR_PARAMS,
        "forward_block_start": FORWARD_BLOCK_START,
        "forward_block_end": None,  # set after evaluation
        "data_cutoff_utc": f"{data_cutoff}T00:00:00Z",
        "data_cutoff_source": "derived from latest fully closed UTC daily Binance kline candle (or --data-cutoff)",
        "min_completed_forward_horizon_days": min_horizon,
        "last_allowed_formation_date": last_allowed_str,
        "input_file_hashes": input_files,
        "evaluated_utc": now_utc(),
        "status": "IN_PROGRESS",
        "reason": "",
        "n_formations": 0,
        "n_high": 0,
        "n_low": 0,
        "n_mid": 0,
        "spread_gross_mean": None,
        "spread_net_1x_mean": None,
        "spread_gross_median": None,
        "spread_net_1x_median": None,
        "high_gross_mean": None,
        "low_gross_mean": None,
        "high_net_1x_mean": None,
        "low_net_1x_mean": None,
        "high_low_diff_gross": None,
        "high_low_diff_net_1x": None,
        "date_first": None,
        "date_last": None,
        "eligible_assets_per_date": {"mean": 0.0, "min": 0, "max": 0},
        "formations": [],
    }

    lookback = ANCHOR_PARAMS["momentum_lookback_days"]
    estimator = ANCHOR_PARAMS["dispersion_estimator"]
    window_days = ANCHOR_PARAMS["dispersion_window_days"]
    state_rule = ANCHOR_PARAMS["dispersion_state_rule"]

    formation_records = []
    all_dispersions: dict[str, float] = {}

    for T, elig in sorted(elig_map.items()):
        if T < FORWARD_BLOCK_START:
            continue
        if last_allowed_str is not None and T > last_allowed_str:
            # Forward horizon not yet completed at the data cutoff: seal the
            # block by excluding this formation rather than computing a
            # truncated outcome.
            continue
        assets = sorted(elig.keys())
        n_elig = len(assets)
        if n_elig < MIN_ASSETS_DECILES:
            continue

        mom = mom_cache.get(T, lookback, tuple(assets))
        mom = mom.dropna()
        if len(mom) < MIN_ASSETS_DECILES:
            continue

        disp = compute_dispersion(mom, estimator)
        all_dispersions[T] = disp

        top, bot = portfolio_spread(mom, state_rule)
        if not top or not bot:
            continue

        fwd = forward_returns(px_wide, T, horizon, list(set(top) | set(bot)))
        if not fwd:
            continue

        top_ret = float(pd.Series({a: fwd[a] for a in top if a in fwd}).mean()) if any(a in fwd for a in top) else float("nan")
        bot_ret = float(pd.Series({a: fwd[a] for a in bot if a in fwd}).mean()) if any(a in fwd for a in bot) else float("nan")
        if math.isnan(top_ret) or math.isnan(bot_ret):
            continue

        spread_gross = top_ret - bot_ret
        spread_net_1x = spread_gross - COST_1X

        formation_records.append({
            "formation_date": T,
            "dispersion": disp,
            "n_assets": n_elig,
            "top_ret": top_ret,
            "bot_ret": bot_ret,
            "spread_gross": spread_gross,
            "spread_net_1x": spread_net_1x,
        })

    if not formation_records:
        freeze_record["status"] = "BLOCKED"
        freeze_record["reason"] = "no_formations_passed_data_gate"
        freeze_record["forward_block_end"] = FORWARD_BLOCK_START
        OUT_DIR.joinpath("forward_block_evaluation.json").write_text(
            json.dumps(freeze_record, indent=2, sort_keys=True) + "\n"
        )
        print("[forward-block] BLOCKED: no formations passed data gate")
        return 1

    dser = pd.Series({r["formation_date"]: r["dispersion"] for r in formation_records})
    results_rows = []
    for r in formation_records:
        T = r["formation_date"]
        past = dser.loc[:T].iloc[:-1].tail(window_days)
        state = "mid"
        if len(past) >= 30:
            thr_hi = float(past.quantile(0.9))
            thr_lo = float(past.quantile(0.1))
            if r["dispersion"] >= thr_hi:
                state = "high"
            elif r["dispersion"] <= thr_lo:
                state = "low"
        r["state"] = state
        results_rows.append(r)

    df = pd.DataFrame(results_rows)
    n_formations = len(df)
    n_high = int((df["state"] == "high").sum())
    n_low = int((df["state"] == "low").sum())
    n_mid = int((df["state"] == "mid").sum())

    gross = df["spread_gross"].dropna()
    net = df["spread_net_1x"].dropna()
    hi = df[df["state"] == "high"]["spread_gross"].dropna()
    lo = df[df["state"] == "low"]["spread_gross"].dropna()
    hi_net = df[df["state"] == "high"]["spread_net_1x"].dropna()
    lo_net = df[df["state"] == "low"]["spread_net_1x"].dropna()

    diff_gross = float(hi.mean() - lo.mean()) if len(hi) and len(lo) else None
    diff_net = float(hi_net.mean() - lo_net.mean()) if len(hi_net) and len(lo_net) else None

    elig_counts = [r["n_assets"] for r in formation_records]

    freeze_record["status"] = "OK"
    freeze_record["reason"] = ""
    freeze_record["forward_block_end"] = df["formation_date"].iloc[-1]
    freeze_record["n_formations"] = n_formations
    freeze_record["n_high"] = n_high
    freeze_record["n_low"] = n_low
    freeze_record["n_mid"] = n_mid
    freeze_record["spread_gross_mean"] = float(gross.mean()) if len(gross) else None
    freeze_record["spread_net_1x_mean"] = float(net.mean()) if len(net) else None
    freeze_record["spread_gross_median"] = float(gross.median()) if len(gross) else None
    freeze_record["spread_net_1x_median"] = float(net.median()) if len(net) else None
    freeze_record["high_gross_mean"] = float(hi.mean()) if len(hi) else None
    freeze_record["low_gross_mean"] = float(lo.mean()) if len(lo) else None
    freeze_record["high_net_1x_mean"] = float(hi_net.mean()) if len(hi_net) else None
    freeze_record["low_net_1x_mean"] = float(lo_net.mean()) if len(lo_net) else None
    freeze_record["high_low_diff_gross"] = diff_gross
    freeze_record["high_low_diff_net_1x"] = diff_net
    freeze_record["date_first"] = df["formation_date"].iloc[0]
    freeze_record["date_last"] = df["formation_date"].iloc[-1]
    freeze_record["eligible_assets_per_date"] = {
        "mean": float(statistics.mean(elig_counts)) if elig_counts else 0.0,
        "min": int(min(elig_counts)) if elig_counts else 0,
        "max": int(max(elig_counts)) if elig_counts else 0,
    }
    freeze_record["block_sealed"] = True
    freeze_record["block_sealing_rule"] = (
        f"formations with formation_date > {last_allowed_str} excluded because "
        f"their {horizon}-day forward horizon is not completed by the data cutoff "
        f"{data_cutoff}; no truncated outcomes are computed"
    )
    freeze_record["formations"] = [
        {
            "formation_date": r["formation_date"],
            "state": r["state"],
            "dispersion": r["dispersion"],
            "n_assets": r["n_assets"],
            "spread_gross": r["spread_gross"],
            "spread_net_1x": r["spread_net_1x"],
        }
        for r in results_rows
    ]
    freeze_record["evaluated_utc"] = now_utc()

    out_path = OUT_DIR / "forward_block_evaluation.json"
    out_path.write_text(json.dumps(freeze_record, indent=2, sort_keys=True) + "\n")

    print(f"[forward-block] anchor={ANCHOR_ID} status=OK")
    print(f"[forward-block] data_cutoff={data_cutoff} last_allowed_formation={last_allowed_str}")
    print(f"[forward-block] block={FORWARD_BLOCK_START}->{freeze_record['forward_block_end']}")
    print(f"[forward-block] formations={n_formations} high={n_high} low={n_low} mid={n_mid}")
    print(f"[forward-block] high_low_diff_gross={diff_gross} high_low_diff_net_1x={diff_net}")
    print(f"[forward-block] output -> {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
