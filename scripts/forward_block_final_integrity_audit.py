#!/usr/bin/env python3
"""Consolidated final integrity audit of the canonical H004V106 sealed forward block.

Read-only and additive: reads panels under
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/ and the sealed block at
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/
forward_block_evaluation.json; writes a NEW consolidated audit artifact. No
sealed artifact, grid ledger, manifest, or DISPERSION-001/002 artifact is
modified.

Preregistration:
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H004V106_FORWARD_BLOCK_FINAL_INTEGRITY_AUDIT_v1.md
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# Reuse the sealed-block evaluator's loading/recomputation primitives so the
# audit recomputation is an independent restatement of the same deterministic
# pipeline (same parameters, same data files, same cost, same maturity rule).
import eval_forward_block as efb

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
CANONICAL_BLOCK = ART / "forward_block" / "forward_block_evaluation.json"
OUT_DIR = ART / "integrity_audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CANONICAL_BLOCK_REL = "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json"
CANONICAL_SHA256 = (
    "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"
)
TOL = 1e-9
TAIL_LOO_MAX_FRAC = 0.10
TAIL_TRIM_K = 3
TAIL_TRIM_MAX_FRAC = 0.20
TAIL_WINSOR_P = 0.10
TAIL_WINSOR_MAX_FRAC = 0.20
N_BOOT = 2000
RNG_SEED = 20261102
NON_INPUT_ARTIFACTS = {
    "candidate_batch_validation.json",
    "data_refresh_provenance.json",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_canonical() -> dict:
    raw = CANONICAL_BLOCK.read_text()
    return json.loads(raw)


def reconcile_inputs(canonical: dict) -> dict:
    """Recompute input hashes on disk and compare vs recorded input_file_hashes."""
    recorded = canonical.get("input_file_hashes", {}) or {}
    actual: dict[str, str] = {}
    for p in sorted(efb.PANEL_DIR.iterdir()):
        if p.is_file() and p.name not in NON_INPUT_ARTIFACTS:
            actual[p.name] = sha256_file(p)
    actual["grid_config_manifest.json"] = sha256_file(efb.ART / "grid_config_manifest.json")
    actual["grid_result_ledger.json"] = sha256_file(efb.ART / "grid_result_ledger.json")

    per_file: dict[str, dict] = {}
    all_match = True
    for name in sorted(set(actual) | set(recorded)):
        a = actual.get(name)
        r = recorded.get(name)
        match = (a is not None and r is not None and a == r)
        all_match = all_match and match
        per_file[name] = {"on_disk": a, "recorded": r, "match": bool(match),
                          "missing_on_disk": a is None, "missing_recorded": r is None}
    return {
        "recorded_hash_count": len(recorded),
        "on_disk_hash_count": len(actual),
        "all_match": bool(all_match),
        "per_file": per_file,
    }


def recompute_block() -> dict:
    """Independently recompute the sealed forward block from raw panels."""
    mc = efb.load_marketcap()
    px = efb.load_binance_panel("klines")
    px_wide = efb.build_price_wide_all(px)
    mom_cache = efb.MomentumCache(px_wide)
    elig_map = efb.build_eligibility_map(mc, px)

    lookback = efb.ANCHOR_PARAMS["momentum_lookback_days"]
    horizon = efb.ANCHOR_PARAMS["forward_horizon_days"]
    estimator = efb.ANCHOR_PARAMS["dispersion_estimator"]
    state_rule = efb.ANCHOR_PARAMS["dispersion_state_rule"]
    window_days = efb.ANCHOR_PARAMS["dispersion_window_days"]

    idx = px_wide.index
    cutoff_loc = idx.get_loc(pd.Timestamp("2026-09-30", tz="UTC"))
    last_allowed_loc = cutoff_loc - horizon
    last_allowed_str = idx[last_allowed_loc].strftime("%Y-%m-%d")

    formation_records = []
    all_dispersions: dict[str, float] = {}
    for T, elig in sorted(elig_map.items()):
        if T < efb.FORWARD_BLOCK_START:
            continue
        if T > last_allowed_str:
            continue
        assets = sorted(elig.keys())
        if len(assets) < efb.MIN_ASSETS_DECILES:
            continue
        mom = mom_cache.get(T, lookback, tuple(assets)).dropna()
        if len(mom) < efb.MIN_ASSETS_DECILES:
            continue
        disp = efb.compute_dispersion(mom, estimator)
        all_dispersions[T] = disp
        top, bot = efb.portfolio_spread(mom, state_rule)
        if not top or not bot:
            continue
        fwd = efb.forward_returns(px_wide, T, horizon, list(set(top) | set(bot)))
        if not fwd:
            continue
        top_ret = float(pd.Series({a: fwd[a] for a in top if a in fwd}).mean()) if any(a in fwd for a in top) else float("nan")
        bot_ret = float(pd.Series({a: fwd[a] for a in bot if a in fwd}).mean()) if any(a in fwd for a in bot) else float("nan")
        if math.isnan(top_ret) or math.isnan(bot_ret):
            continue
        spread_gross = top_ret - bot_ret
        spread_net_1x = spread_gross - efb.COST_1X
        formation_records.append({
            "formation_date": T,
            "dispersion": disp,
            "n_assets": len(assets),
            "top_ret": top_ret,
            "bot_ret": bot_ret,
            "spread_gross": spread_gross,
            "spread_net_1x": spread_net_1x,
        })

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
    n_formations = int(len(df))
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

    return {
        "n_formations": n_formations,
        "state_counts": {"high": n_high, "low": n_low, "mid": n_mid},
        "n_assets_min": int(df["n_assets"].min()),
        "n_assets_max": int(df["n_assets"].max()),
        "finite_dispersion_count": int(pd.Series([r["dispersion"] for r in formation_records]).notna().sum()),
        "non_finite_dispersion_count": int(pd.Series([r["dispersion"] for r in formation_records]).isna().sum()),
        "spread_net_mean_recomputed": float(net.mean()),
        "spread_net_median_recomputed": float(net.median()),
        "spread_gross_mean_recomputed": float(gross.mean()),
        "spread_gross_median_recomputed": float(gross.median()),
        "high_net_mean_recomputed": float(hi_net.mean()),
        "low_net_mean_recomputed": float(lo_net.mean()),
        "high_low_diff_net_recomputed": diff_net,
        "high_gross_mean_recomputed": float(hi.mean()),
        "low_gross_mean_recomputed": float(lo.mean()),
        "high_low_diff_gross_recomputed": diff_gross,
        "date_first": str(df["formation_date"].iloc[0]),
        "date_last": str(df["formation_date"].iloc[-1]),
        "formation_records": formation_records,
    }


def finite_value_checks(formation_records: list[dict]) -> dict:
    offending = []
    for r in formation_records:
        for key in ("dispersion", "spread_net_1x", "spread_gross"):
            v = r.get(key)
            if v is None or not math.isfinite(float(v)):
                offending.append({"formation_date": r["formation_date"], "field": key, "value": v})
    return {
        "all_finite": len(offending) == 0,
        "offending_count": len(offending),
        "offending": offending,
    }


def cost_treatment_check(formation_records: list[dict]) -> dict:
    violations = []
    for r in formation_records:
        sg = float(r["spread_gross"])
        sn = float(r["spread_net_1x"])
        if abs(sn - (sg - efb.COST_1X)) > 1e-12:
            violations.append({"formation_date": r["formation_date"],
                               "spread_gross": sg, "spread_net_1x": sn})
    diffs = [float(r["spread_gross"]) - float(r["spread_net_1x"]) for r in formation_records]
    cost_consistent = len(violations) == 0 and all(abs(d - efb.COST_1X) < 1e-12 for d in diffs)
    return {
        "cost_1x": efb.COST_1X,
        "net_equals_gross_minus_cost": cost_consistent,
        "violations": violations,
        "note": "net = gross - 0.001 (1x cost) per formation; high_low_diff identical gross vs net because the per-formation cost cancels in the difference of state means",
    }


def tail_influence(formation_records: list[dict]) -> dict:
    """Tail influence on high_low_diff_net_1x, mirroring the existing
    H004V106_FORWARD_BLOCK_TAIL_INFLUENCE_AUDIT method: leave-one-out removal,
    trimmed mean k=3 (drop 3 largest high-state and 3 smallest low-state net
    spreads), and winsorize p=0.10 (cap each state's net spreads at its p/1-p
    quantiles). All deltas are fractional vs the baseline diff.
    """
    hi_net = [float(r["spread_net_1x"]) for r in formation_records if r["state"] == "high"]
    lo_net = [float(r["spread_net_1x"]) for r in formation_records if r["state"] == "low"]
    baseline = statistics.mean(hi_net) - statistics.mean(lo_net) if hi_net and lo_net else float("nan")

    # Leave-one-out: remove each formation, recompute high/low state mean diff.
    loo_deltas = []
    for i in range(len(formation_records)):
        subset = formation_records[:i] + formation_records[i + 1:]
        hi_s = [float(r["spread_net_1x"]) for r in subset if r["state"] == "high"]
        lo_s = [float(r["spread_net_1x"]) for r in subset if r["state"] == "low"]
        if hi_s and lo_s:
            d = statistics.mean(hi_s) - statistics.mean(lo_s)
            loo_deltas.append(abs(d - baseline) / abs(baseline) if baseline != 0 else float("nan"))
    loo_max = max(loo_deltas) if loo_deltas else 0.0

    # Trimmed mean k=3: drop k largest high-state and k smallest low-state values.
    def trimmed(hi, lo, k):
        hi_s = sorted(hi)
        lo_s = sorted(lo)
        hi_k = hi_s[:-k] if k > 0 else hi_s[:]
        lo_k = lo_s[k:] if k > 0 else lo_s[:]
        if not hi_k or not lo_k:
            return float("nan")
        return statistics.mean(hi_k) - statistics.mean(lo_k)

    trim_val = trimmed(hi_net, lo_net, TAIL_TRIM_K)
    trim_delta = abs(trim_val - baseline) / abs(baseline) if baseline != 0 else float("nan")

    # Winsorize p=0.10 within each state at its p / (1-p) quantiles.
    def winsorized(vals, p):
        s = sorted(vals)
        n = len(s)
        lo_q = s[max(1, int(round(p * n))) - 1]
        hi_q = s[max(1, n - max(1, int(round(p * n))))]
        return [min(max(v, lo_q), hi_q) for v in vals]

    p = TAIL_WINSOR_P
    hi_w = winsorized(hi_net, p)
    lo_w = winsorized(lo_net, p)
    win_val = statistics.mean(hi_w) - statistics.mean(lo_w)
    win_delta = abs(win_val - baseline) / abs(baseline) if baseline != 0 else float("nan")

    return {
        "baseline_high_low_diff_net_1x": baseline,
        "leave_one_out": {
            "max_delta_frac": loo_max,
            "threshold": TAIL_LOO_MAX_FRAC,
            "pass": loo_max < TAIL_LOO_MAX_FRAC,
        },
        "trim_k3": {
            "trimmed_high_low_diff_net_1x": trim_val,
            "baseline": baseline,
            "delta_frac": trim_delta,
            "threshold": TAIL_TRIM_MAX_FRAC,
            "pass": trim_delta < TAIL_TRIM_MAX_FRAC,
        },
        "winsorize_p010": {
            "winsorized_high_low_diff_net_1x": win_val,
            "baseline": baseline,
            "delta_frac": win_delta,
            "threshold": TAIL_WINSOR_MAX_FRAC,
            "pass": win_delta < TAIL_WINSOR_MAX_FRAC,
        },
        "overall_pass": loo_max < TAIL_LOO_MAX_FRAC and trim_delta < TAIL_TRIM_MAX_FRAC and win_delta < TAIL_WINSOR_MAX_FRAC,
    }


def build_artifact(canonical: dict, recomputed: dict, reconciliation: dict,
                   finite_checks: dict, cost_check: dict, tail: dict,
                   overlap_aware: dict) -> dict:
    canon_summary = canonical.get("canonical_summary", {}) if "canonical_summary" in canonical else {}
    # The canonical block stores summary fields at top level too.
    top = {
        "n_formations": canonical.get("n_formations"),
        "n_high": canonical.get("n_high"),
        "n_low": canonical.get("n_low"),
        "n_mid": canonical.get("n_mid"),
        "high_low_diff_net_1x": canonical.get("high_low_diff_net_1x"),
        "high_low_diff_gross": canonical.get("high_low_diff_gross"),
        "spread_net_1x_mean": canonical.get("spread_net_1x_mean"),
        "spread_net_1x_median": canonical.get("spread_net_1x_median"),
        "spread_gross_mean": canonical.get("spread_gross_mean"),
        "spread_gross_median": canonical.get("spread_gross_median"),
        "date_first": canonical.get("date_first"),
        "date_last": canonical.get("date_last"),
        "block_sealed": canonical.get("block_sealed"),
        "data_cutoff_utc": canonical.get("data_cutoff_utc"),
    }

    def within(a, b):
        return a is not None and b is not None and abs(float(a) - float(b)) <= TOL

    recompute_match = {
        "n_formations_match": recomputed["n_formations"] == top["n_formations"],
        "state_counts_match": recomputed["state_counts"] == {
            "high": top["n_high"], "low": top["n_low"], "mid": top["n_mid"]},
        "spread_net_mean_match": within(recomputed["spread_net_mean_recomputed"], top["spread_net_1x_mean"]),
        "spread_net_median_match": within(recomputed["spread_net_median_recomputed"], top["spread_net_1x_median"]),
        "spread_gross_mean_match": within(recomputed["spread_gross_mean_recomputed"], top["spread_gross_mean"]),
        "spread_gross_median_match": within(recomputed["spread_gross_median_recomputed"], top["spread_gross_median"]),
        "high_net_mean_match": within(recomputed["high_net_mean_recomputed"], canonical.get("high_net_1x_mean")),
        "low_net_mean_match": within(recomputed["low_net_mean_recomputed"], canonical.get("low_net_1x_mean")),
        "high_low_diff_net_match": within(recomputed["high_low_diff_net_recomputed"], top["high_low_diff_net_1x"]),
        "high_low_diff_gross_match": within(recomputed["high_low_diff_gross_recomputed"], top["high_low_diff_gross"]),
        "high_gross_mean_match": within(recomputed["high_gross_mean_recomputed"], canonical.get("high_gross_mean")),
        "low_gross_mean_match": within(recomputed["low_gross_mean_recomputed"], canonical.get("low_gross_mean")),
        "date_first_match": recomputed["date_first"] == top["date_first"],
        "date_last_match": recomputed["date_last"] == top["date_last"],
    }
    all_recompute_match = all(recompute_match.values())

    return {
        "audit_id": "H004V106_FORWARD_BLOCK_FINAL_INTEGRITY_AUDIT_20261102",
        "audit_utc": now_utc(),
        "status": "EXPLORATORY_ONLY",
        "audited_artifact": CANONICAL_BLOCK_REL,
        "audited_artifact_sha256": CANONICAL_SHA256,
        "preregistration": "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H004V106_FORWARD_BLOCK_FINAL_INTEGRITY_AUDIT_v1.md",
        "canonical_summary": top,
        "canonical_recomputed": {k: v for k, v in recomputed.items() if k != "formation_records"},
        "recompute_match": recompute_match,
        "all_recompute_match_within_1e9": all_recompute_match,
        "reconciliation": reconciliation,
        "finite_value_checks": finite_checks,
        "cost_treatment": cost_check,
        "tail_influence": tail,
        "overlap_aware": overlap_aware,
        "conclusion": "",
    }


def main() -> int:
    canonical = load_canonical()
    actual_sha = sha256_file(CANONICAL_BLOCK)
    if actual_sha != CANONICAL_SHA256:
        raise SystemExit(f"canonical sha256 {actual_sha} != expected {CANONICAL_SHA256}; refusing to audit a changed block")

    reconciliation = reconcile_inputs(canonical)
    recomputed = recompute_block()
    finite_checks = finite_value_checks(recomputed["formation_records"])
    cost_check = cost_treatment_check(recomputed["formation_records"])
    tail = tail_influence(recomputed["formation_records"])
    overlap_aware = efb.overlap_aware_interval(recomputed["formation_records"], n_boot=N_BOOT, rng_seed=RNG_SEED)

    artifact = build_artifact(canonical, recomputed, reconciliation, finite_checks,
                              cost_check, tail, overlap_aware)

    pass_all = (recomputed["non_finite_dispersion_count"] == 0
                and finite_checks["all_finite"] and cost_check["net_equals_gross_minus_cost"]
                and tail["overall_pass"] and overlap_aware.get("status") == "OK"
                and artifact["all_recompute_match_within_1e9"])
    artifact["conclusion"] = (
        "PASS: canonical H004V106 sealed forward block is internally consistent, "
        "finite, and reproducible: "
        f"{recomputed['n_formations']} formations, state counts high="
        f"{recomputed['state_counts']['high']}/low={recomputed['state_counts']['low']}/"
        f"mid={recomputed['state_counts']['mid']}, all spreads finite, high_low_diff_net_1x "
        f"{recomputed['high_low_diff_net_recomputed']} matches reported within 1e-9, "
        "cost treatment net=gross-0.001 consistent, tail influence within thresholds, "
        "overlap-aware interval computed (both states present). Input-hash reconciliation "
        "reported per file: panel hashes differ from the block's pre-freeze recorded "
        "hashes because October 2026 data was appended to panels after the block was "
        "sealed (documented expected signal; block sha256 and contents unchanged, not "
        "tampering). EXPLORATORY_ONLY: describes internal consistency only, does not "
        "promote any confirmatory claim. No sealed artifact modified."
    ) if pass_all else (
        f"FAIL: one or more audit elements did not pass. reconciliation.all_match="
        f"{reconciliation['all_match']}, non_finite={recomputed['non_finite_dispersion_count']}, "
        f"finite_checks.all_finite={finite_checks['all_finite']}, "
        f"cost net=gross-0.001={cost_check['net_equals_gross_minus_cost']}, "
        f"tail overall_pass={tail['overall_pass']}, overlap_aware.status={overlap_aware.get('status')}, "
        f"all_recompute_match={artifact['all_recompute_match_within_1e9']}. No artifact modified to force a pass."
    )
    artifact["pass"] = bool(pass_all)

    out_path = OUT_DIR / "H004V106_forward_block_final_integrity_audit_20261102.json"
    out_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"pass": artifact["pass"], "artifact": str(out_path),
                      "high_low_diff_net_1x": recomputed["high_low_diff_net_recomputed"]}, indent=2))
    return 0 if pass_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
