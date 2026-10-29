#!/usr/bin/env python3
"""H004V106 forward block tail-influence audit (DISP-003-TAILAUDIT-001).

Reads the canonical sealed forward block (read-only) and measures how
sensitive the high-minus-low net-1x estimate is to (a) symmetric trimming of
the formation-level spread tails, (b) symmetric winsorization, and (c)
single-formation leave-one-out, plus tail-concentration shares. Writes a new
audit artifact under artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/.
No frozen artifact is modified.

Decision rule (predeclared in preregistration H004V106_FORWARD_BLOCK_TAIL_INFLUENCE_AUDIT_v1.md):
- trimming 3 formations from each state moves diff by >20% of baseline -> TAIL_SENSITIVE
- 10% winsorization moves diff by >20% of baseline -> TAIL_SENSITIVE
- any single-formation leave-one-out moves diff by >10% of baseline -> TAIL_SENSITIVE
- otherwise TAIL_ROBUST
All branches are EXPLORATORY_ONLY; no promotion to confirmatory status.
"""

from __future__ import annotations

import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
BLOCK_PATH = ART / "forward_block" / "forward_block_evaluation.json"
OUT_PATH = ART / "integrity_audit" / "H004V106_forward_block_tail_influence_20261029.json"

TRIM_K = (0, 1, 2, 3)
WINSOR_P = (0.05, 0.10)
TRIM_DELTA_FRAC = 0.20
WINSOR_DELTA_FRAC = 0.20
LOO_DELTA_FRAC = 0.10
TAIL_PCT = (0.01, 0.05, 0.10)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fisher_pearson_skew(values):
    n = len(values)
    if n < 3:
        return None
    mean = statistics.mean(values)
    pstdev = statistics.pstdev(values)
    if pstdev == 0:
        return 0.0
    return (n / ((n - 1) * (n - 2))) * sum(((v - mean) / pstdev) ** 3 for v in values)


def mean_diff(high_vals, low_vals):
    if not high_vals or not low_vals:
        return None
    return statistics.mean(high_vals) - statistics.mean(low_vals)


def trim_series(values, k):
    if k == 0 or len(values) <= 2 * k:
        return list(values)
    ordered = sorted(values)
    return ordered[k:len(values) - k]


def winsorize_series(values, p):
    n = len(values)
    if n == 0:
        return []
    arr = np.asarray(values, dtype=float)
    lo_q = np.percentile(arr, p * 100)
    hi_q = np.percentile(arr, (1 - p) * 100)
    return [float(min(max(v, lo_q), hi_q)) for v in values]


def tail_share(values, pct, upper):
    """Share of the total sum carried by the top pct (by magnitude/sign).

    upper=True: largest positive values. upper=False: most negative values.
    Returns (share, count_used, tail_sum, total_sum).
    """
    n = len(values)
    if n == 0:
        return (None, 0, None, None)
    k = max(1, math.ceil(n * pct))
    ordered = sorted(values, reverse=upper)
    tail = ordered[:k]
    total = sum(values)
    tail_sum = sum(tail)
    share = (tail_sum / total) if total != 0 else None
    return (share, k, tail_sum, total)


def main() -> int:
    block = json.loads(BLOCK_PATH.read_text(encoding="utf-8"))
    formations = block["formations"]
    baseline = block["high_low_diff_net_1x"]

    high = [r["spread_net_1x"] for r in formations if r["state"] == "high"]
    low = [r["spread_net_1x"] for r in formations if r["state"] == "low"]

    state_stats = {}
    for name, vals in (("high", high), ("low", low)):
        state_stats[name] = {
            "n": len(vals),
            "mean": statistics.mean(vals),
            "median": statistics.median(vals),
            "min": min(vals),
            "max": max(vals),
            "skew": fisher_pearson_skew(vals),
            "sum": sum(vals),
        }

    # (a) symmetric trimming
    trimming = {}
    for k in TRIM_K:
        hi_k = trim_series(high, k)
        lo_k = trim_series(low, k)
        diff = mean_diff(hi_k, lo_k)
        trimming[f"k_{k}"] = {
            "k": k,
            "n_high_kept": len(hi_k),
            "n_low_kept": len(lo_k),
            "high_low_diff_net_1x": diff,
            "delta_vs_baseline": (diff - baseline) if diff is not None else None,
            "delta_frac_vs_baseline": ((diff - baseline) / baseline)
            if (diff is not None and baseline) else None,
        }

    # (b) symmetric winsorization
    winsorization = {}
    for p in WINSOR_P:
        hi_w = winsorize_series(high, p)
        lo_w = winsorize_series(low, p)
        diff = mean_diff(hi_w, lo_w)
        winsorization[f"p_{p}"] = {
            "p": p,
            "n_high": len(hi_w),
            "n_low": len(lo_w),
            "high_low_diff_net_1x": diff,
            "delta_vs_baseline": (diff - baseline) if diff is not None else None,
            "delta_frac_vs_baseline": ((diff - baseline) / baseline)
            if (diff is not None and baseline) else None,
        }

    # (c) single-formation leave-one-out
    sum_high = sum(high)
    sum_low = sum(low)
    n_high = len(high)
    n_low = len(low)
    mean_high = sum_high / n_high
    mean_low = sum_low / n_low

    loo_records = []
    max_abs_delta = 0.0
    extreme = None
    for r in formations:
        if r["state"] not in ("high", "low"):
            # Mid-state formations do not enter the high-minus-low contrast;
            # their removal leaves the estimand unchanged (delta = 0).
            continue
        v = r["spread_net_1x"]
        if r["state"] == "high":
            new_mean_high = (sum_high - v) / (n_high - 1) if n_high > 1 else None
            new_diff = (new_mean_high - mean_low) if new_mean_high is not None else None
            removed_state = "high"
        else:
            new_mean_low = (sum_low - v) / (n_low - 1) if n_low > 1 else None
            new_diff = (mean_high - new_mean_low) if new_mean_low is not None else None
            removed_state = "low"
        if new_diff is None:
            continue
        delta = new_diff - baseline
        delta_frac = delta / baseline if baseline else None
        abs_delta = abs(delta)
        rec = {
            "formation_date": r["formation_date"],
            "state": r["state"],
            "spread_net_1x": v,
            "n_high_after": n_high - (1 if removed_state == "high" else 0),
            "n_low_after": n_low - (1 if removed_state == "low" else 0),
            "high_low_diff_net_1x": new_diff,
            "delta_vs_baseline": delta,
            "delta_frac_vs_baseline": delta_frac,
        }
        loo_records.append(rec)
        if abs_delta > max_abs_delta:
            max_abs_delta = abs_delta
            extreme = rec

    loo_by_state = {"high": [], "low": []}
    for rec in loo_records:
        loo_by_state[rec["state"]].append(rec)
    max_high = max(loo_by_state["high"], key=lambda x: abs(x["delta_vs_baseline"])) if loo_by_state["high"] else None
    max_low = max(loo_by_state["low"], key=lambda x: abs(x["delta_vs_baseline"])) if loo_by_state["low"] else None

    # (d) tail concentration
    tail_concentration = {}
    for name, vals, upper in (("high", high, True), ("low", low, False)):
        entry = {}
        for pct in TAIL_PCT:
            share, k, tail_sum, total = tail_share(vals, pct, upper)
            entry[f"top_{int(pct * 100)}pct_by_magnitude"] = {
                "pct": pct,
                "count": k,
                "tail_sum": tail_sum,
                "total_sum": total,
                "share_of_total": share,
            }
        tail_concentration[name] = entry

    # Decision rule (predeclared)
    tail_sensitive = False
    reasons = []
    k3 = trimming["k_3"]
    if k3["delta_frac_vs_baseline"] is not None and abs(k3["delta_frac_vs_baseline"]) > TRIM_DELTA_FRAC:
        tail_sensitive = True
        reasons.append(f"trim_k3 delta_frac {k3['delta_frac_vs_baseline']:+.4f} exceeds {TRIM_DELTA_FRAC}")
    w10 = winsorization["p_0.1"]
    if w10["delta_frac_vs_baseline"] is not None and abs(w10["delta_frac_vs_baseline"]) > WINSOR_DELTA_FRAC:
        tail_sensitive = True
        reasons.append(f"winsor_p0.10 delta_frac {w10['delta_frac_vs_baseline']:+.4f} exceeds {WINSOR_DELTA_FRAC}")
    if extreme is not None and abs(extreme["delta_frac_vs_baseline"]) > LOO_DELTA_FRAC:
        tail_sensitive = True
        reasons.append(f"LOO {extreme['formation_date']} {extreme['state']} delta_frac {extreme['delta_frac_vs_baseline']:+.4f} exceeds {LOO_DELTA_FRAC}")
    label = "TAIL_SENSITIVE" if tail_sensitive else "TAIL_ROBUST"

    audit = {
        "audit_id": "H004V106_FORWARD_BLOCK_TAIL_INFLUENCE_AUDIT_20261029",
        "experiment_id": "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-TAILAUDIT-001",
        "preregistration": "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H004V106_FORWARD_BLOCK_TAIL_INFLUENCE_AUDIT_v1.md",
        "audited_artifact": "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json",
        "computed_utc": now_utc(),
        "status": "EXPLORATORY_ONLY",
        "data_cutoff_utc": block["data_cutoff_utc"],
        "date_first": block["date_first"],
        "date_last": block["date_last"],
        "n_formations": block["n_formations"],
        "baseline_high_low_diff_net_1x": baseline,
        "baseline_spread_net_mean": block["spread_net_1x_mean"],
        "baseline_spread_net_median": block["spread_net_1x_median"],
        "state_stats": state_stats,
        "state_counts": {"high": n_high, "low": n_low, "mid": block["n_mid"]},
        "trimming": trimming,
        "winsorization": winsorization,
        "single_formation_leave_one_out": {
            "n_formations_tested": len(loo_records),
            "max_abs_delta": max_abs_delta,
            "max_abs_delta_frac_vs_baseline": (max_abs_delta / baseline) if baseline else None,
            "extreme_formation": extreme,
            "max_high_state_removal": max_high,
            "max_low_state_removal": max_low,
            "all_records": loo_records,
        },
        "tail_concentration": tail_concentration,
        "decision_rule": {
            "trim_k3_threshold_frac": TRIM_DELTA_FRAC,
            "winsor_p010_threshold_frac": WINSOR_DELTA_FRAC,
            "loo_threshold_frac": LOO_DELTA_FRAC,
            "label": label,
            "reasons": reasons,
        },
        "conclusion": label,
        "safeguards": [
            "read-only forward block; last formation 2026-08-31, cutoff 2026-09-30; no truncated outcomes",
            "no look-ahead, no forward-fill, no synthetic data, no paid sources, no trading",
            "no parameters, thresholds, assets, costs or grid cells tuned; no new data fetched",
            "no frozen artifact modified; new audit artifact only",
        ],
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "audit_id": audit["audit_id"],
        "status": audit["status"],
        "conclusion": label,
        "baseline": baseline,
        "max_abs_loo_delta": max_abs_delta,
        "max_abs_loo_delta_frac": (max_abs_delta / baseline) if baseline else None,
        "trim_k3_delta_frac": k3["delta_frac_vs_baseline"],
        "winsor_p010_delta_frac": w10["delta_frac_vs_baseline"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
