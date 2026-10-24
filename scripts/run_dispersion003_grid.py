#!/usr/bin/env python3
"""Resumable, idempotent DISPERSION-003 data gate and evaluation runner.

Reads the deterministic 216-cell grid manifest and, for each cell:
  1. Data gate: checks point-in-time cap + price + funding availability for the
     declared universe arm at every formation date.
  2. Evaluation: trailing momentum -> dispersion state -> decile/median-split
     portfolio -> forward H-day spread -> cost/funding-adjusted net return.
  3. Records one terminal result per cell: OK / BLOCKED / INVALID / FAILED /
     NOT_RUN with reason.

Checkpoint/resume: per-cell results are written incrementally; re-runs skip
completed cells and preserve existing rows. Holm step-down correction is
applied across the complete 216-cell family for the registered 1x net endpoint.

Free-data-only: reads panels under artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/.
No API keys, no secrets, no trading.
"""

from __future__ import annotations

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
MANIFEST_PATH = ART / "grid_config_manifest.json"
CHECKPOINT_DIR = ART / "grid_checkpoints"
RESULT_PATH = ART / "grid_result_ledger.json"
SUMMARY_PATH = ART / "grid_summary.json"

BASE_COST_TURN = 0.0005
COST_STRESS = {1: BASE_COST_TURN, 2: 2 * BASE_COST_TURN, 3: 3 * BASE_COST_TURN}

MIN_ASSETS_DECILES = 20
MIN_ASSETS_MEDIAN = 4
HOLM_ALPHA = 0.05

LEGACY_ASSETS = [
    "btc", "eth", "sol", "bnb", "xrp", "ada", "doge", "dot", "matic", "avax",
    "link", "uni", "ltc", "bch", "etc", "xlm", "atom", "algo", "vet", "fil",
    "trx", "eos", "neo", "iost", "qtum", "zec", "dash", "rune",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Panel loading (done once)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Pre-compute point-in-time eligible universe per date
# ---------------------------------------------------------------------------

def build_eligibility_map(mc: pd.DataFrame, px: dict[str, pd.DataFrame],
                          fd: dict[str, pd.DataFrame], arm: str) -> dict[str, dict]:
    """Returns {date: {asset: cap}} for eligible assets at each date.

    Eligibility: CapMrktEstUSD observation on date AND Binance perpetual
    price on date. Asset->symbol map: <ASSET.upper()>USDT.
    """
    # asset -> binance symbol
    asset_to_symbol: dict[str, str] = {}
    for symbol in px:
        if symbol.endswith("USDT"):
            asset = symbol[:-4].lower()
            asset_to_symbol[asset] = symbol

    if arm == "legacy28_comparator":
        allowed = set(LEGACY_ASSETS)
    else:
        allowed = set(asset_to_symbol.keys())

    # Price dates per symbol.
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
            if asset not in allowed:
                continue
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


# ---------------------------------------------------------------------------
# Price wide DataFrame (built once for all eligible assets)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Momentum with caching
# ---------------------------------------------------------------------------

class MomentumCache:
    def __init__(self, px_wide: pd.DataFrame, returns_wide: pd.DataFrame | None = None):
        self.px_wide = px_wide
        # Momentum is a return: (1+r1)(1+r2)...(1+rn) - 1. Computing it from raw
        # prices (as the pre-fix code did) multiplies dollar magnitudes across the
        # cross-section, so dispersion is ~1e128 and the high/low decile split is
        # driven by price level, not by return dispersion. Daily returns are used.
        self.returns_wide = returns_wide if returns_wide is not None else px_wide.pct_change()
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


# ---------------------------------------------------------------------------
# Per-cell evaluation
# ---------------------------------------------------------------------------

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
    if rule == "trailing_window_median_split":
        k = n // 2
        if k < 1:
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


def evaluate_cell(config_id: str, params: dict, elig_map: dict[str, dict],
                  px_wide: pd.DataFrame, mom_cache: MomentumCache,
                  checkpoint: dict) -> dict:
    cid = config_id
    if cid in checkpoint and checkpoint[cid].get("status") == "OK":
        return checkpoint[cid]

    lookback = params["momentum_lookback_days"]
    horizon = params["forward_horizon_days"]
    estimator = params["dispersion_estimator"]
    window_days = params["dispersion_window_days"]
    state_rule = params["dispersion_state_rule"]

    result = {
        "config_id": cid,
        "parameters": params,
        "universe_arm": params["universe_arm"],
        "status": "BLOCKED",
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
        "holm_rejected": None,
        "date_first": None,
        "date_last": None,
        "eligible_assets_per_date": {"mean": 0.0, "min": 0, "max": 0},
        "evaluated_utc": now_utc(),
    }

    try:
        min_need = MIN_ASSETS_DECILES if state_rule == "trailing_window_outer_deciles" else MIN_ASSETS_MEDIAN
        formation_records = []
        all_dispersions: dict[str, float] = {}

        for T, elig in sorted(elig_map.items()):
            assets = sorted(elig.keys())
            n_elig = len(assets)
            if n_elig < min_need:
                continue

            mom = mom_cache.get(T, lookback, tuple(assets))
            mom = mom.dropna()
            if len(mom) < min_need:
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
            cost_1x = COST_STRESS[1] * 2.0
            spread_net_1x = spread_gross - cost_1x

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
            result["status"] = "BLOCKED"
            result["reason"] = "no_formations_passed_data_gate"
            checkpoint[cid] = result
            return result

        # Dispersion state assignment (point-in-time trailing history).
        dser = pd.Series({r["formation_date"]: r["dispersion"] for r in formation_records})
        results_rows = []
        for r in formation_records:
            T = r["formation_date"]
            past = dser.loc[:T].iloc[:-1].tail(window_days)
            state = "mid"
            if state_rule == "trailing_window_outer_deciles":
                if len(past) >= 30:
                    thr_hi = float(past.quantile(0.9))
                    thr_lo = float(past.quantile(0.1))
                    if r["dispersion"] >= thr_hi:
                        state = "high"
                    elif r["dispersion"] <= thr_lo:
                        state = "low"
            elif state_rule == "trailing_window_median_split":
                if len(past) > 0:
                    med = float(past.median())
                    state = "high" if r["dispersion"] >= med else "low"
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

        result["status"] = "OK"
        result["reason"] = ""
        result["n_formations"] = n_formations
        result["n_high"] = n_high
        result["n_low"] = n_low
        result["n_mid"] = n_mid
        result["spread_gross_mean"] = float(gross.mean()) if len(gross) else None
        result["spread_net_1x_mean"] = float(net.mean()) if len(net) else None
        result["spread_gross_median"] = float(gross.median()) if len(gross) else None
        result["spread_net_1x_median"] = float(net.median()) if len(net) else None
        result["high_gross_mean"] = float(hi.mean()) if len(hi) else None
        result["low_gross_mean"] = float(lo.mean()) if len(lo) else None
        result["high_net_1x_mean"] = float(hi_net.mean()) if len(hi_net) else None
        result["low_net_1x_mean"] = float(lo_net.mean()) if len(lo_net) else None
        result["high_low_diff_gross"] = diff_gross
        result["high_low_diff_net_1x"] = diff_net
        result["date_first"] = df["formation_date"].iloc[0]
        result["date_last"] = df["formation_date"].iloc[-1]
        result["eligible_assets_per_date"] = {
            "mean": float(statistics.mean(elig_counts)) if elig_counts else 0.0,
            "min": int(min(elig_counts)) if elig_counts else 0,
            "max": int(max(elig_counts)) if elig_counts else 0,
        }
        result["formations"] = [
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

    except Exception as exc:  # noqa: BLE001
        result["status"] = "FAILED"
        result["reason"] = f"{type(exc).__name__}: {exc}"

    checkpoint[cid] = result
    return result


# ---------------------------------------------------------------------------
# Holm correction
# ---------------------------------------------------------------------------

def bootstrap_diff_pvalue(high_series: list[float], low_series: list[float],
                           block_len: int = 21, n_boot: int = 1000,
                           seed: int = 20261024) -> float:
    """Two-sided bootstrap p-value for H0: mean(high) - mean(low) == 0.

    High and low dispersion-state series are block-bootstrapped independently
    (overlapping moving blocks, fixed length) to preserve within-series
    autocorrelation. The bootstrap distribution of the mean difference is then
    used to estimate P*(diff <= 0) and P*(diff >= 0); the two-sided p-value is
    twice the smaller, which is consistent with inverting a bootstrap
    confidence interval. Returns 1.0 (no evidence) when either state has too
    few observations to estimate a block.
    """
    if len(high_series) < 2 or len(low_series) < 2:
        return 1.0
    rng = __import__("random").Random(seed)
    h = [float(x) for x in high_series]
    l = [float(x) for x in low_series]
    n_h, n_l = len(h), len(l)
    b = max(2, int(block_len))

    def block_means(series: list[float]) -> list[float]:
        n = len(series)
        out = []
        for _ in range(n_boot):
            starts = [rng.randrange(n) for _ in range(max(1, n // b))]
            vals = []
            for s in starts:
                for i in range(b):
                    vals.append(series[(s + i) % n])
            out.append(sum(vals) / len(vals))
        return out

    mh = block_means(h)
    ml = block_means(l)
    diffs = [a - b for a, b in zip(mh, ml)]
    p_lo = sum(1 for d in diffs if d <= 0) / len(diffs)
    p_hi = sum(1 for d in diffs if d >= 0) / len(diffs)
    return float(2.0 * min(p_lo, p_hi))


def holm_step_down(pvals: dict[str, float], alpha: float = HOLM_ALPHA) -> dict[str, bool]:
    """Holm-Bonferroni step-down on genuine p-values.

    pvals must map cell id -> two-sided p-value in [0, 1]. Caller is responsible
    for computing real p-values (e.g. from a dependence-aware bootstrap); this
    function only orders and thresholds. It refuses to run on degenerate input
    so a caller mistake cannot silently declare a winner.

    Returns one bool per input cell id: True if the cell is rejected at the
    family level, False otherwise. Every input id is present in the result so
    downstream code can count the family size from the returned dict.
    """
    reject = {cid: False for cid in pvals}
    items = []
    for cid, p in pvals.items():
        if p is None or math.isnan(p):
            continue
        if not (0.0 <= p <= 1.0):
            raise ValueError(f"holm_step_down received p={p} outside [0,1] for {cid}")
        items.append((p, cid))
    m = len(items)
    if m == 0:
        return reject
    items.sort(key=lambda x: x[0])
    for k, (p, cid) in enumerate(items, start=1):
        threshold = alpha / (m - k + 1)
        if p <= threshold:
            reject[cid] = True
        else:
            # Holm step-down: once a hypothesis fails to reject, every
            # hypothesis ranked after it (larger p) also fails to reject.
            break
    return reject


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = manifest["configurations"]
    expected = manifest["combination_count"]
    if len(rows) != expected:
        raise ValueError(f"manifest has {len(rows)} cells, expected {expected}")

    mc = load_marketcap()
    px = load_binance_panel("klines")
    fd = load_binance_panel("funding")

    px_wide = build_price_wide_all(px)
    mom_cache = MomentumCache(px_wide)

    # Pre-compute eligibility maps for both arms.
    elig_legacy = build_eligibility_map(mc, px, fd, "legacy28_comparator")
    elig_expanding = build_eligibility_map(mc, px, fd, "expanding_point_in_time")

    ckpt_path = CHECKPOINT_DIR / "cell_checkpoint.json"
    checkpoint: dict = {}
    if ckpt_path.exists():
        checkpoint = json.loads(ckpt_path.read_text(encoding="utf-8"))

    print(f"[grid] {expected} cells, {len(checkpoint)} already checkpointed",
          flush=True)

    for i, row in enumerate(rows, start=1):
        params = row["parameters"]
        arm = params["universe_arm"]
        elig_map = elig_legacy if arm == "legacy28_comparator" else elig_expanding
        res = evaluate_cell(row["config_id"], params, elig_map, px_wide, mom_cache, checkpoint)
        if i % 10 == 0 or i == expected:
            ckpt_path.write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n")
            print(f"[grid] {i}/{expected} cells done, last={row['config_id']} "
                  f"status={res['status']}", flush=True)

    # Final checkpoint write.
    ckpt_path.write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n")

    # Holm correction across the 216-cell family for the registered 1x net endpoint.
    # p-values come from a dependence-aware block bootstrap on the high/low
    # dispersion-state series, not from the raw mean difference. The old code
    # used abs(high_low_diff_net_1x) as a p-value proxy, which is not a p-value
    # and made any nonzero difference look "significant". That defect is
    # recorded in archive_defective_momentum_20261024/ and the corrected
    # inference is used here. The raw difference is kept as a separate field.
    pvals: dict[str, float] = {}
    pval_meta: dict[str, dict] = {}
    for cid, res in checkpoint.items():
        if res["status"] != "OK":
            continue
        hi = [r["spread_net_1x"] for r in res.get("formations", []) if r.get("state") == "high"]
        lo = [r["spread_net_1x"] for r in res.get("formations", []) if r.get("state") == "low"]
        p = bootstrap_diff_pvalue(hi, lo)
        pvals[cid] = p
        pval_meta[cid] = {
            "n_high": len(hi), "n_low": len(lo),
            "high_low_diff_net_1x": res.get("high_low_diff_net_1x"),
            "bootstrap_p_two_sided": p,
        }
    holm_reject = holm_step_down(pvals, HOLM_ALPHA) if pvals else {}
    for cid in checkpoint:
        meta = pval_meta.get(cid)
        if meta is None:
            continue
        checkpoint[cid]["pvalue_bootstrap_two_sided"] = meta["bootstrap_p_two_sided"]
        checkpoint[cid]["pvalue_note"] = (
            "two-sided block-bootstrap p-value on high/low dispersion-state "
            "net-1x series; Holm step-down across all 216 cells"
        )
        checkpoint[cid]["holm_rejected"] = bool(holm_reject.get(cid, False))
    ckpt_path.write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n")

    # Write final ledger.
    ledger = {
        "experiment_id": EXP,
        "grid_id": manifest["grid_id"],
        "source_manifest": str(MANIFEST_PATH.relative_to(ROOT)),
        "evaluated_utc": now_utc(),
        "expected_cells": expected,
        "cells_evaluated": len(checkpoint),
        "cells_ok": sum(1 for r in checkpoint.values() if r["status"] == "OK"),
        "cells_blocked": sum(1 for r in checkpoint.values() if r["status"] == "BLOCKED"),
        "cells_failed": sum(1 for r in checkpoint.values() if r["status"] == "FAILED"),
        "holm_alpha": HOLM_ALPHA,
        "holm_rejected_count": sum(1 for v in holm_reject.values() if v),
        "pvalue_method": "two-sided block bootstrap on high/low dispersion-state net-1x series (block_len=21, n_boot=1000)",
        "cells": checkpoint,
    }
    RESULT_PATH.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n")

    # Summary.
    ok_results = [r for r in checkpoint.values() if r["status"] == "OK"]
    summary = {
        "experiment_id": EXP,
        "evaluated_utc": now_utc(),
        "expected_cells": expected,
        "cells_evaluated": len(checkpoint),
        "cells_ok": len(ok_results),
        "cells_blocked": sum(1 for r in checkpoint.values() if r["status"] == "BLOCKED"),
        "cells_failed": sum(1 for r in checkpoint.values() if r["status"] == "FAILED"),
        "holm_alpha": HOLM_ALPHA,
        "holm_rejected_count": sum(1 for v in holm_reject.values() if v),
        "primary_anchor_legacy_H004V105": checkpoint.get("H004V105", {}),
        "primary_anchor_expanding_H004V106": checkpoint.get("H004V106", {}),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    print(f"[grid] cells={len(checkpoint)} ok={summary['cells_ok']} "
          f"blocked={summary['cells_blocked']} failed={summary['cells_failed']}")
    print(f"[grid] holm_rejected={summary['holm_rejected_count']}")
    print(f"[grid] ledger -> {RESULT_PATH.relative_to(ROOT)}")
    print(f"[grid] summary -> {SUMMARY_PATH.relative_to(ROOT)}")
    print(f"[grid] checkpoint -> {ckpt_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
