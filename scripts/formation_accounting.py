"""Formation / return accounting and Phase A/B unconditional momentum baseline.

Reads the point-in-time universe and price/funding panels, then, for each
eligible formation date on a fixed monthly schedule, computes:

  - trailing L-day momentum per eligible asset (compounded daily returns)
  - cross-sectional dispersion (population std of momentum returns)
  - top-minus-bottom decile momentum-spread portfolio (equal-weight)
  - forward H-day return of that spread portfolio

Phase B (unconditional baseline) reports the spread WITHOUT dispersion
conditioning: gross spread and net spread under the registered base-cost case.

No conditional (high/low dispersion) outcomes are computed here; those belong
to Phase C and are gated behind the data gate passing.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-001"
PANEL_DIR = ROOT / "artifacts" / EXP / "data" / "panels"
OUT_DIR = ROOT / "artifacts" / EXP

# Primary-compatible anchor (grid H004G033): 30d momentum / 30d forward / deciles.
MOMENTUM_LOOKBACK = 30
FORWARD_HORIZON = 30
BREAKPOINTS = "deciles"  # q = 10

# Registered base cost (1x): taker fee + conservative slippage per turnover,
# applied per entry/rebalance/exit. Frozen before outcomes are read.
BASE_COST_TURN = 0.0005  # 0.05% per side (fee + slippage placeholder)


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
    """First eligible date of each month (fixed UTC phase, non-overlapping)."""
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
    """Compounded trailing lookback return per asset using complete daily obs."""
    idx = returns.index
    if end_date not in idx:
        return pd.Series(dtype=float)
    end_loc = idx.get_loc(end_date)
    start_loc = end_loc - lookback + 1
    if start_loc < 0:
        return pd.Series(dtype=float)
    window = returns.iloc[start_loc : end_loc + 1]
    sub = window[assets]
    # Require complete observations: asset must have a return every day in window.
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
    records = []

    for T in dates:
        # Eligible point-in-time universe at formation T.
        elig = univ[(univ["date"] == T) & (univ["eligible"])]
        assets = sorted(elig["asset_id"].tolist())
        n = len(assets)
        if n < 20:  # need N >= 2q for deciles
            continue

        mom = momentum(returns, T, MOMENTUM_LOOKBACK, assets)
        mom = mom.dropna()
        if len(mom) < 20:
            continue
        mom_assets = sorted(mom.index.tolist())

        # Dispersion = population std of momentum returns across the cross-section.
        dispersion = float(mom.std(ddof=0))

        # Momentum-spread portfolio: top-bottom decile, equal-weight, tie-break asset asc.
        q = 10
        k = len(mom_assets) // q
        ranked = mom.sort_values(ascending=False)  # desc momentum; index order stable
        # tie-break by asset id asc for equal returns
        ranked = ranked.reindex(
            sorted(ranked.index, key=lambda a: (-ranked[a], a))
        )
        top = ranked.head(k).index.tolist()
        bot = ranked.tail(k).index.tolist()

        # Forward H-day return of the spread portfolio, formed at T.
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

        # Cost: turnover approx = full replacement of both legs each rebalance.
        turnover = 2.0
        cost_1x = BASE_COST_TURN * turnover
        spread_net_1x = spread_gross - cost_1x if not pd.isna(spread_gross) else float("nan")

        records.append({
            "formation_date": T,
            "n_assets": n,
            "dispersion": dispersion,
            "momentum_spread_gross": spread_gross,
            "momentum_spread_net_1x": spread_net_1x,
            "turnover": turnover,
            "cost_1x": cost_1x,
        })

    out = pd.DataFrame(records)
    out_path = OUT_DIR / "formation_returns.csv"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    out_sha = sha256_file(out_path)

    # Phase B summary (unconditional baseline).
    spread = out["momentum_spread_gross"].dropna()
    spread_net = out["momentum_spread_net_1x"].dropna()
    summary = {
        "experiment_id": EXP,
        "phase": "B_unconditional_baseline",
        "formation_schedule": "first eligible date of each month, fixed UTC phase",
        "momentum_lookback_days": MOMENTUM_LOOKBACK,
        "forward_horizon_days": FORWARD_HORIZON,
        "breakpoints": BREAKPOINTS,
        "n_formations": int(len(out)),
        "date_first": out["formation_date"].iloc[0] if len(out) else None,
        "date_last": out["formation_date"].iloc[-1] if len(out) else None,
        "gross_spread_mean": float(spread.mean()) if len(spread) else None,
        "gross_spread_median": float(spread.median()) if len(spread) else None,
        "gross_spread_pos_share": float((spread > 0).mean()) if len(spread) else None,
        "net_1x_spread_mean": float(spread_net.mean()) if len(spread_net) else None,
        "net_1x_spread_pos_share": float((spread_net > 0).mean()) if len(spread_net) else None,
        "formation_returns_path": str(out_path.relative_to(ROOT)),
        "formation_returns_sha256": out_sha,
    }
    (OUT_DIR / "phase_b_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"[formation] formations={len(out)} {summary['date_first']}->{summary['date_last']}")
    print(f"[formation] gross spread mean={summary['gross_spread_mean']} "
          f"net1x mean={summary['net_1x_spread_mean']} "
          f"gross pos share={summary['gross_spread_pos_share']}")
    print(f"[formation] -> {out_path.relative_to(ROOT)} sha={out_sha[:12]}")
    print(f"[formation] phase_b_summary -> artifacts/{EXP}/phase_b_summary.json")


if __name__ == "__main__":
    main()
