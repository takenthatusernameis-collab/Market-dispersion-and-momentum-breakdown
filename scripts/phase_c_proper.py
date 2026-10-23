"""Phase C: registered dispersion-conditioned test (H004G033 anchor), proper implementation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-001"
PANEL_DIR = ROOT / "artifacts" / EXP / "data" / "panels"
OUT_DIR = ROOT / "artifacts" / EXP

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
    df = pd.read_csv(p, dtype={"CapMrktEstUSD": str, "CapMrktCurUSD": str})
    df["date"] = df["date"].astype(str).str.slice(0, 10)
    df["eligible"] = df["eligible"].eq("yes")
    df["CapMrktEstUSD"] = pd.to_numeric(df["CapMrktEstUSD"], errors="coerce")
    return df


def formation_dates(prices: pd.DataFrame, univ: pd.DataFrame) -> list[str]:
    eligible_dates = sorted(univ[univ["eligible"]]["date"].unique())
    out = []
    seen_months = set()
    for d in eligible_dates:
        m = d[:7]
        if m not in seen_months:
            seen_months.add(m)
            out.append(d)
    return out


def momentum(returns: pd.DataFrame, end_date: str, lookback: int, assets: list[str]) -> pd.Series:
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


def main() -> None:
    prices = load_price_panel()
    univ = load_universe()
    returns = prices.pct_change()

    # Build daily dispersion series (population stddev of trailing 30d momentum across eligible assets)
    daily_disp = {}
    for idx_date in prices.index:
        elig_today = univ[(univ["date"] == str(idx_date)) & (univ["eligible"])]
        if len(elig_today) < 20:
            continue
        assets = sorted(elig_today["asset_id"].tolist())
        loc = prices.index.get_loc(idx_date)
        if loc < MOMENTUM_LOOKBACK - 1:
            continue
        win = returns.iloc[loc - MOMENTUM_LOOKBACK + 1 : loc + 1][assets]
        comp = (1.0 + win).prod() - 1.0
        comp = comp.dropna()
        if len(comp) < 20:
            continue
        disp = float(comp.std(ddof=0))
        daily_disp[str(idx_date)] = disp

    dates = formation_dates(prices, univ)
    out_rows = []

    for T in dates:
        elig = univ[(univ["date"] == T) & (univ["eligible"])]
        assets = sorted(elig["asset_id"].tolist())
        n = len(assets)
        if n < 20:
            continue
        mom = momentum(returns, T, MOMENTUM_LOOKBACK, assets)
        mom = mom.dropna()
        if len(mom) < 20:
            continue
        mom_assets = sorted(mom.index.tolist())
        dispersion_T = float(mom.std(ddof=0))  # current dispersion at formation

        # State assignment: use only valid dispersion observations strictly earlier than formation timestamp
        # within preceding 365 calendar days; require at least 180 valid prior daily observations
        T_dt = pd.Timestamp(T)
        past_disps = []
        for dday, dval in daily_disp.items():
            ddt = pd.Timestamp(dday)
            if ddt < T_dt:  # strictly earlier
                if (T_dt - ddt).days <= 365:
                    past_disps.append(dval)
        state = "mid"
        if len(past_disps) >= 180:
            past_ser = pd.Series(past_disps)
            thr_lo = past_ser.quantile(0.1, interpolation='linear')  # type-7 linear
            thr_hi = past_ser.quantile(0.9, interpolation='linear')
            if dispersion_T <= thr_lo:
                state = "low"
            elif dispersion_T >= thr_hi:
                state = "high"
            else:
                state = "mid"
        else:
            state = "mid"

        q = 10
        k = len(mom_assets) // q
        ranked = mom.sort_values(ascending=False)
        ranked = ranked.reindex(sorted(ranked.index, key=lambda a: (-ranked[a], a)))
        top = ranked.head(k).index.tolist()
        bot = ranked.tail(k).index.tolist()

        T_loc = prices.index.get_loc(T)
        forward_window = prices.iloc[T_loc + 1 : T_loc + FORWARD_HORIZON + 1]
        if forward_window.empty:
            continue
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
        spread_net_1x = spread_gross - cost_1x if not pd.isna(spread_gross) else float("nan")

        out_rows.append({
            "formation_date": T,
            "dispersion": dispersion_T,
            "state": state,
            "spread_gross": spread_gross,
            "spread_net_1x": spread_net_1x,
            "n_assets": n
        })

    df = pd.DataFrame(out_rows)
    df.to_csv(OUT_DIR / "phase_c_returns.csv", index=False)

    hi = df[df.state == "high"]["spread_gross"].dropna()
    lo = df[df.state == "low"]["spread_gross"].dropna()
    diff = float(hi.mean() - lo.mean()) if len(hi) and len(lo) else None
    summary = {
        "experiment_id": EXP,
        "phase": "C_dispersion_conditioned",
        "anchor": "H004G033",
        "n_formations": int(len(df)),
        "n_high": int((df.state == "high").sum()),
        "n_low": int((df.state == "low").sum()),
        "n_mid": int((df.state == "mid").sum()),
        "high_gross_mean": float(hi.mean()) if len(hi) else None,
        "low_gross_mean": float(lo.mean()) if len(lo) else None,
        "difference_gross": diff,
    }
    (OUT_DIR / "phase_c_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
