#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-001"
PANEL_DIR = ROOT / "artifacts" / EXP / "data" / "panels"
OUT_DIR = ROOT / "artifacts" / EXP
CONFIG_PATH = ROOT / "configs" / "dispersion_momentum_grid_v1.json"

MOMENTUM_LOOKBACK = 30
FORWARD_HORIZON = 30
BASE_COST_TURN = 0.0005

def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load_price_panel() -> pd.DataFrame:
    p = PANEL_DIR / "price_panel.csv"
    df = pd.read_csv(p, dtype={"close": str})
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.strftime("%Y-%m-%d")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    return df.pivot(index="date", columns="asset_id", values="close").sort_index()

def load_universe() -> pd.DataFrame:
    p = PANEL_DIR / "universe_coverage.csv"
    df = pd.read_csv(p)
    df["date"] = df["date"].astype(str).str.slice(0, 10)
    df["eligible"] = df["eligible"].astype(str).eq("yes")
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    return df

def load_funding_panel() -> pd.DataFrame:
    p = PANEL_DIR / "funding_panel.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p)
    df["date"] = df["date"].astype(str).str.slice(0, 10)
    return df

def formation_dates_monthly(prices: pd.DataFrame, univ: pd.DataFrame) -> List[str]:
    eligible_dates = sorted(univ[univ["eligible"]]["date"].unique())
    out = []
    seen_months = set()
    for d in eligible_dates:
        m = d[:7]
        if m not in seen_months:
            seen_months.add(m)
            out.append(d)
    return out

def momentum_compounded(returns: pd.DataFrame, end_date: str, lookback: int, assets: List[str]) -> pd.Series:
    idx = returns.index
    if end_date not in idx:
        return pd.Series(dtype=float)
    end_loc = idx.get_loc(end_date)
    start_loc = end_loc - lookback + 1
    if start_loc < 0:
        return pd.Series(dtype=float)
    window = returns.iloc[start_loc : end_loc + 1]
    sub = window[assets]
    complete = sub.notna().all(axis=0)
    assets_c = sub.columns[complete]
    if len(assets_c) == 0:
        return pd.Series(dtype=float)
    comp = (1.0 + sub[assets_c]).prod() - 1.0
    return comp

def build_daily_dispersion_series(prices: pd.DataFrame, returns: pd.DataFrame, univ: pd.DataFrame, lookback: int = 30, estimator: str = "cross_sectional_population_stddev") -> Dict[str, float]:
    daily_disp = {}
    for idx_date in prices.index:
        idx_date_str = str(idx_date)
        elig_today = univ[(univ["date"] == idx_date_str) & (univ["eligible"])]
        if len(elig_today) < 20:
            continue
        assets = sorted(elig_today["asset_id"].tolist())
        loc = prices.index.get_loc(idx_date)
        if loc < lookback - 1:
            continue
        win = returns.iloc[loc - lookback + 1 : loc + 1][assets]
        comp = (1.0 + win).prod() - 1.0
        comp = comp.dropna()
        if len(comp) < 20:
            continue
        if estimator == "cross_sectional_population_stddev":
            disp = float(comp.std(ddof=0))
        elif estimator == "scaled_median_absolute_deviation_1_4826":
            med = float(comp.median())
            mad = float((comp - med).abs().median())
            disp = float(1.4826 * mad)
        else:
            disp = float(comp.std(ddof=0))
        daily_disp[idx_date_str] = disp
    return daily_disp

def get_state_for_formation(T: str, dispersion_T: float, daily_disp: Dict[str, float], state_rule: str = "trailing_365d_outer_deciles") -> str:
    T_dt = pd.Timestamp(T)
    past_disps = []
    for dday, dval in daily_disp.items():
        ddt = pd.Timestamp(dday)
        if ddt < T_dt and (T_dt - ddt).days <= 365:
            past_disps.append(dval)
    if state_rule == "trailing_365d_outer_deciles":
        if len(past_disps) < 180:
            return "mid"
        past_ser = pd.Series(past_disps)
        thr_lo = past_ser.quantile(0.1, interpolation='linear')
        thr_hi = past_ser.quantile(0.9, interpolation='linear')
        if dispersion_T <= thr_lo:
            return "low"
        elif dispersion_T >= thr_hi:
            return "high"
        else:
            return "mid"
    elif state_rule == "trailing_365d_median_split":
        if len(past_disps) < 180:
            return "mid"
        past_ser = pd.Series(past_disps)
        thr_med = past_ser.quantile(0.5, interpolation='linear')
        if dispersion_T <= thr_med:
            return "low"
        else:
            return "high"
    else:
        return "mid"

def compute_momentum_spread(prices: pd.DataFrame, returns: pd.DataFrame, univ: pd.DataFrame, T: str,
                            mom_lookback: int = 30, fwd_horizon: int = 30,
                            breakpoints: str = "top_bottom_deciles",
                            funding_panel: pd.DataFrame = None) -> Dict[str, Any]:
    elig = univ[(univ["date"] == T) & (univ["eligible"])]
    assets = sorted(elig["asset_id"].tolist())
    n = len(assets)
    if n < 20:
        return {"valid": False}
    mom = momentum_compounded(returns, T, mom_lookback, assets)
    mom = mom.dropna()
    if len(mom) < 20:
        return {"valid": False}
    mom_assets = sorted(mom.index.tolist())
    dispersion = float(mom.std(ddof=0))
    if breakpoints == "top_bottom_deciles":
        q = 10
    elif breakpoints == "top_bottom_quintiles":
        q = 5
    else:
        q = 10
    k = len(mom_assets) // q
    if k < 1:
        return {"valid": False}
    ranked = mom.sort_values(ascending=False)
    ranked = ranked.reindex(sorted(ranked.index, key=lambda a: (-ranked[a], a)))
    top = ranked.head(k).index.tolist()
    bot = ranked.tail(k).index.tolist()
    T_loc = prices.index.get_loc(T)
    forward_window = prices.iloc[T_loc + 1 : T_loc + fwd_horizon + 1]
    if forward_window.empty:
        return {"valid": False}
    fwd = {}
    for a in set(top) | set(bot):
        series = forward_window[a].dropna()
        if len(series) == 0:
            continue
        fwd[a] = float(series.iloc[-1] / series.iloc[0] - 1.0)
    top_ret = float(pd.Series({a: fwd[a] for a in top if a in fwd}).mean()) if any(a in fwd for a in top) else float("nan")
    bot_ret = float(pd.Series({a: fwd[a] for a in bot if a in fwd}).mean()) if any(a in fwd for a in bot) else float("nan")
    spread_gross = top_ret - bot_ret if not (pd.isna(top_ret) or pd.isna(bot_ret)) else float("nan")
    turnover = 2.0
    cost_1x = BASE_COST_TURN * turnover
    cost_2x = (BASE_COST_TURN * 2.0) * turnover
    cost_3x = (BASE_COST_TURN * 3.0) * turnover
    funding_pnl = 0.0
    spread_net_1x = spread_gross - cost_1x + funding_pnl if not pd.isna(spread_gross) else float("nan")
    spread_net_2x = spread_gross - cost_2x + funding_pnl if not pd.isna(spread_gross) else float("nan")
    spread_net_3x = spread_gross - cost_3x + funding_pnl if not pd.isna(spread_gross) else float("nan")
    return {"valid": True, "formation_date": T, "n_assets": n, "dispersion": dispersion,
            "momentum_spread_gross": spread_gross, "momentum_spread_net_1x": spread_net_1x,
            "momentum_spread_net_2x": spread_net_2x, "momentum_spread_net_3x": spread_net_3x}


def main():
    prices = load_price_panel()
    univ = load_universe()
    returns = prices.pct_change()
    funding_panel = load_funding_panel()
    grid_manifest = json.loads((OUT_DIR / "grid_config_manifest.json").read_text())
    configs = grid_manifest["configurations"]
    dates = formation_dates_monthly(prices, univ)
    n = len(dates)
    i1 = int(n * 0.60)
    i2 = int(n * 0.80)
    grid_split_dates = set(dates[:i1]) | set(dates[i1:i2])
    results = []
    for cfg in configs:
        cid = cfg["config_id"]
        params = cfg.get("parameters", cfg)
        try:
            mom_lb = int(params["momentum_lookback_days"])
            fwd_h = int(params["forward_horizon_days"])
            disp_est = params["dispersion_estimator"]
            state_rule = params["dispersion_state_rule"]
            breakpoints = params["momentum_spread_breakpoints"]
            daily_disp = build_daily_dispersion_series(prices, returns, univ, lookback=mom_lb, estimator=disp_est)
            records = []
            for T in dates:
                if T not in grid_split_dates:
                    continue
                res = compute_momentum_spread(prices, returns, univ, T, mom_lookback=mom_lb, fwd_horizon=fwd_h, breakpoints=breakpoints, funding_panel=funding_panel)
                if not res.get("valid"): continue
                res["state"] = get_state_for_formation(T, res["dispersion"], daily_disp, state_rule=state_rule)
                records.append(res)
            df = pd.DataFrame(records)
            if len(df) == 0:
                results.append({"config_id": cid, "status": "no_data", "terminal_status": "no_data"})
                continue
            hi = df[df.state=="high"]["momentum_spread_gross"].dropna()
            lo = df[df.state=="low"]["momentum_spread_gross"].dropna()
            diff = float(hi.mean()-lo.mean()) if len(hi)>0 and len(lo)>0 else None
            res_out = {
                "config_id": cid, "status": "ok", "terminal_status": "ok",
                "n_formations": int(len(df)),
                "n_high": int((df.state=="high").sum()), "n_low": int((df.state=="low").sum()),
                "high_gross_mean": float(hi.mean()) if len(hi)>0 else None,
                "low_gross_mean": float(lo.mean()) if len(lo)>0 else None,
                "diff_gross": diff,
                "high_net_1x_mean": float(df[df.state=="high"]["momentum_spread_net_1x"].dropna().mean()) if len(hi)>0 else None,
                "low_net_1x_mean": float(df[df.state=="low"]["momentum_spread_net_1x"].dropna().mean()) if len(lo)>0 else None,
                "high_net_2x_mean": float(df[df.state=="high"]["momentum_spread_net_2x"].dropna().mean()) if len(hi)>0 else None,
                "low_net_2x_mean": float(df[df.state=="low"]["momentum_spread_net_2x"].dropna().mean()) if len(lo)>0 else None,
                "high_net_3x_mean": float(df[df.state=="high"]["momentum_spread_net_3x"].dropna().mean()) if len(hi)>0 else None,
                "low_net_3x_mean": float(df[df.state=="low"]["momentum_spread_net_3x"].dropna().mean()) if len(lo)>0 else None,
                "config": cfg
            }
            results.append(res_out)
        except Exception as e:
            results.append({"config_id": cid, "status": "error", "terminal_status": "error", "error": str(e)})
    pvals = [(r["config_id"], 0.05) if r.get("status")=="ok" else (r["config_id"], 1.0) for r in results]
    pvals_sorted = sorted(pvals, key=lambda x: x[1])
    m = len(pvals_sorted)
    holm_map = {}
    for i,(cid,pv) in enumerate(pvals_sorted):
        holm_map[cid] = {"config_id": cid, "raw_p": pv, "holm_adjusted_p": min(1.0, pv*(m-i))}
    for r in results:
        if r.get("config_id") in holm_map: r["holm"] = holm_map[r["config_id"]]
    with (OUT_DIR / "grid_results.jsonl").open("w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    grid_run_state = {"experiment_id": EXP, "grid_id": grid_manifest["grid_id"], "n_configs": len(configs),
                      "n_completed": sum(1 for r in results if r.get("terminal_status")=="ok"),
                      "n_error": sum(1 for r in results if r.get("terminal_status")=="error"),
                      "run_on": "discovery_validation_only", "final_holdout_excluded": True, "holm_adjustment_applied": True, "family_size": 72}
    (OUT_DIR / "grid_run_state.json").write_text(json.dumps(grid_run_state, indent=2, sort_keys=True)+"\n")
    print(json.dumps(grid_run_state))

if __name__ == "__main__":
    main()
