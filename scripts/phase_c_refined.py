"""Phase C: registered dispersion-conditioned test (H004G033 anchor), refined."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-001"
PANEL_DIR = ROOT / "artifacts" / EXP / "data" / "panels"
OUT_DIR = ROOT / "artifacts" / EXP

# Primary-compatible anchor (grid H004G033)
MOMENTUM_LOOKBACK = 30
FORWARD_HORIZON = 30
BREAKPOINTS = "deciles"
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

    dates = formation_dates(prices, univ)

    # First pass: compute dispersion for each formation (same as Phase B)
    formations = []
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
        dispersion = float(mom.std(ddof=0))
        formations.append({
            "formation_date": T,
            "dispersion": dispersion,
            "mom": mom,
            "mom_assets": mom_assets,
            "n_assets": n
        })

    # State assignment: trailing 365d outer deciles using only valid dispersion
    # observations strictly earlier than formation timestamp within preceding 365 calendar days
    # require at least 180 valid prior daily observations
    # For monthly formations, look back over prior formations? Or daily?
    # "valid dispersion observations strictly earlier than the formation timestamp within the preceding 365 calendar days"
    # - so look at dispersion values from observations in past 365 days before T
    out_rows = []
    for i, form in enumerate(formations):
        T = form["formation_date"]
        T_dt = pd.Timestamp(T)
        # collect past dispersions from formations strictly earlier than T, within 365 days
        past_disps = []
        for j in range(i):  # strictly earlier
            prev = formations[j]
            prev_dt = pd.Timestamp(prev["formation_date"])
            if (T_dt - prev_dt).days <= 365 and (T_dt - prev_dt).days > 0:
                past_disps.append(prev["dispersion"])
        state = "mid"
        if len(past_disps) >= 180:  # require at least 180 valid prior daily observations
            # use type-7 quantiles (linear)
            past_ser = pd.Series(past_disps)
            thr_lo = past_ser.quantile(0.1, interpolation='linear')
            thr_hi = past_ser.quantile(0.9, interpolation='linear')
            if form["dispersion"] <= thr_lo:
                state = "low"
            elif form["dispersion"] >= thr_hi:
                state = "high"
            else:
                state = "mid"
        else:
            state = "mid"  # not enough history

        mom = form["mom"]
        mom_assets = form["mom_assets"]
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
            "dispersion": form["dispersion"],
            "state": state,
            "spread_gross": spread_gross,
            "spread_net_1x": spread_net_1x,
            "n_assets": form["n_assets"]
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
        "high_n": int(len(hi)),
        "low_n": int(len(lo)),
    }
    (OUT_DIR / "phase_c_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
