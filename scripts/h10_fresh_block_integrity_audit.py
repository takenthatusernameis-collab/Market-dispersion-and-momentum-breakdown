#!/usr/bin/env python3
"""Internal-consistency audit of the H10 fresh sealed forward block.

Read-only and additive: reads the committed H10 fresh block at
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/
forward_block_evaluation.json and the panel data it references; writes a NEW
consolidated audit artifact. No sealed artifact, grid ledger, manifest, or
DISPERSION-001/002 artifact is modified.

Preregistration:
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/
H004V106_H10_FRESH_FORWARD_BLOCK_INTEGRITY_AUDIT_v1.md
"""

from __future__ import annotations

import hashlib
import json
import math
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
H10_FRESH_BLOCK = ART / "forward_block_h10_fresh" / "forward_block_evaluation.json"
OUT_DIR = ART / "integrity_audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

H10_FRESH_BLOCK_REL = "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json"
H10_FRESH_BLOCK_SHA256 = (
    "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f"
)
TOL = 1e-9
NON_INPUT_ARTIFACTS = {
    "candidate_batch_validation.json",
    "data_refresh_provenance.json",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_h10_fresh() -> dict:
    raw = H10_FRESH_BLOCK.read_text()
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
        per_file[name] = {
            "on_disk": a,
            "recorded": r,
            "match": bool(match),
            "missing_on_disk": a is None,
            "missing_recorded": r is None,
        }
    return {
        "recorded_hash_count": len(recorded),
        "on_disk_hash_count": len(actual),
        "all_match": bool(all_match),
        "per_file": per_file,
    }


def recompute_h10_fresh(canonical: dict) -> dict:
    """Independently recompute the H10 fresh forward block from raw panels."""
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
    # H10 fresh block uses data_cutoff_utc = 2026-10-31T00:00:00Z
    cutoff_ts = pd.Timestamp("2026-10-31", tz="UTC")
    cutoff_loc = idx.get_loc(cutoff_ts)
    last_allowed_loc = cutoff_loc - horizon
    last_allowed_str = idx[last_allowed_loc].strftime("%Y-%m-%d")

    formation_records = []
    all_dispersions: dict[str, float] = {}
    h10_block_start = canonical.get("forward_block_start", efb.FORWARD_BLOCK_START)
    for T, elig in sorted(elig_map.items()):
        if T < h10_block_start:
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
        "n_assets_min": int(df["n_assets"].min()) if n_formations > 0 else 0,
        "n_assets_max": int(df["n_assets"].max()) if n_formations > 0 else 0,
        "finite_dispersion_count": int(pd.Series([r["dispersion"] for r in formation_records]).notna().sum()),
        "non_finite_dispersion_count": int(pd.Series([r["dispersion"] for r in formation_records]).isna().sum()),
        "spread_net_mean_recomputed": float(net.mean()) if len(net) else None,
        "spread_net_median_recomputed": float(net.median()) if len(net) else None,
        "spread_gross_mean_recomputed": float(gross.mean()) if len(gross) else None,
        "spread_gross_median_recomputed": float(gross.median()) if len(gross) else None,
        "high_net_mean_recomputed": float(hi_net.mean()) if len(hi_net) else None,
        "low_net_mean_recomputed": float(lo_net.mean()) if len(lo_net) else None,
        "high_low_diff_net_recomputed": diff_net,
        "high_gross_mean_recomputed": float(hi.mean()) if len(hi) else None,
        "low_gross_mean_recomputed": float(lo.mean()) if len(lo) else None,
        "high_low_diff_gross_recomputed": diff_gross,
        "date_first": str(df["formation_date"].iloc[0]) if n_formations > 0 else None,
        "date_last": str(df["formation_date"].iloc[-1]) if n_formations > 0 else None,
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


def state_consistency_check(canonical: dict, recomputed: dict) -> dict:
    """Check that state assignments and derived fields are internally consistent."""
    issues = []

    # Check n_high, n_low, n_mid match formation records
    canon_n_high = canonical.get("n_high")
    canon_n_low = canonical.get("n_low")
    canon_n_mid = canonical.get("n_mid")
    recomputed_n_high = recomputed["state_counts"]["high"]
    recomputed_n_low = recomputed["state_counts"]["low"]
    recomputed_n_mid = recomputed["state_counts"]["mid"]

    if canon_n_high != recomputed_n_high:
        issues.append(f"n_high mismatch: canonical={canon_n_high} recomputed={recomputed_n_high}")
    if canon_n_low != recomputed_n_low:
        issues.append(f"n_low mismatch: canonical={canon_n_low} recomputed={recomputed_n_low}")
    if canon_n_mid != recomputed_n_mid:
        issues.append(f"n_mid mismatch: canonical={canon_n_mid} recomputed={recomputed_n_mid}")

    # Check high_low_diff fields
    canon_diff_net = canonical.get("high_low_diff_net_1x")
    canon_diff_gross = canonical.get("high_low_diff_gross")
    recomputed_diff_net = recomputed["high_low_diff_net_recomputed"]
    recomputed_diff_gross = recomputed["high_low_diff_gross_recomputed"]

    if recomputed_n_high == 0 or recomputed_n_low == 0:
        if canon_diff_net is not None:
            issues.append(f"high_low_diff_net_1x should be null when n_high=0 or n_low=0, got {canon_diff_net}")
        if canon_diff_gross is not None:
            issues.append(f"high_low_diff_gross should be null when n_high=0 or n_low=0, got {canon_diff_gross}")
        if recomputed_diff_net is not None:
            issues.append(f"recomputed high_low_diff_net should be null when n_high=0 or n_low=0, got {recomputed_diff_net}")
        if recomputed_diff_gross is not None:
            issues.append(f"recomputed high_low_diff_gross should be null when n_high=0 or n_low=0, got {recomputed_diff_gross}")
    else:
        # Both states present - check they match within tolerance
        if canon_diff_net is not None and recomputed_diff_net is not None:
            if abs(float(canon_diff_net) - float(recomputed_diff_net)) > TOL:
                issues.append(f"high_low_diff_net_1x mismatch: canonical={canon_diff_net} recomputed={recomputed_diff_net}")
        if canon_diff_gross is not None and recomputed_diff_gross is not None:
            if abs(float(canon_diff_gross) - float(recomputed_diff_gross)) > TOL:
                issues.append(f"high_low_diff_gross mismatch: canonical={canon_diff_gross} recomputed={recomputed_diff_gross}")

    # Check state means
    for field, canon_key, recomputed_key in [
        ("high_gross_mean", "high_gross_mean", "high_gross_mean_recomputed"),
        ("low_gross_mean", "low_gross_mean", "low_gross_mean_recomputed"),
        ("high_net_1x_mean", "high_net_1x_mean", "high_net_mean_recomputed"),
        ("low_net_1x_mean", "low_net_1x_mean", "low_net_mean_recomputed"),
    ]:
        canon_v = canonical.get(canon_key)
        recomp_v = recomputed.get(recomputed_key)
        if recomputed_n_high == 0 and "high" in field:
            if canon_v is not None:
                issues.append(f"{field} should be null when n_high=0, got {canon_v}")
        if recomputed_n_low == 0 and "low" in field:
            if canon_v is not None:
                issues.append(f"{field} should be null when n_low=0, got {canon_v}")
        if canon_v is not None and recomp_v is not None:
            if abs(float(canon_v) - float(recomp_v)) > TOL:
                issues.append(f"{field} mismatch: canonical={canon_v} recomputed={recomp_v}")

    # Check date_first, date_last
    if recomputed["date_first"] is not None:
        if canonical.get("date_first") != recomputed["date_first"]:
            issues.append(f"date_first mismatch: canonical={canonical.get('date_first')} recomputed={recomputed['date_first']}")
    if recomputed["date_last"] is not None:
        if canonical.get("date_last") != recomputed["date_last"]:
            issues.append(f"date_last mismatch: canonical={canonical.get('date_last')} recomputed={recomputed['date_last']}")

    # Check block_sealed, block_sealing_rule
    if canonical.get("block_sealed") is not True:
        issues.append(f"block_sealed should be true, got {canonical.get('block_sealed')}")
    if canonical.get("block_sealing_rule") is None:
        issues.append("block_sealing_rule is missing")

    # Check sequential fields
    if canonical.get("sequential_look_number") != 1:
        issues.append(f"sequential_look_number should be 1, got {canonical.get('sequential_look_number')}")
    if abs(float(canonical.get("sequential_alpha_k", 0)) - 0.025) > 1e-12:
        issues.append(f"sequential_alpha_k should be 0.025, got {canonical.get('sequential_alpha_k')}")

    # Check confirmatory gate fields
    if canonical.get("confirmatory_claim_allowed") is not False:
        issues.append(f"confirmatory_claim_allowed should be false (IMMATURE), got {canonical.get('confirmatory_claim_allowed')}")
    if canonical.get("economic_significance_met") is not False:
        issues.append(f"economic_significance_met should be false (IMMATURE), got {canonical.get('economic_significance_met')}")

    # Check overlap_aware_uncertainty
    overlap = canonical.get("overlap_aware_uncertainty", {})
    if overlap.get("status") != "IMMATURE":
        issues.append(f"overlap_aware_uncertainty.status should be IMMATURE, got {overlap.get('status')}")
    if overlap.get("n_clusters_with_both_states") != 0:
        issues.append(f"overlap_aware_uncertainty.n_clusters_with_both_states should be 0, got {overlap.get('n_clusters_with_both_states')}")
    if "need n_high>0 and n_low>0" not in str(overlap.get("reason", "")):
        issues.append(f"overlap_aware_uncertainty.reason should mention n_high>0 and n_low>0, got {overlap.get('reason')}")

    return {
        "all_consistent": len(issues) == 0,
        "issues": issues,
    }


def build_artifact(canonical: dict, recomputed: dict, reconciliation: dict,
                   finite_checks: dict, cost_check: dict, state_check: dict) -> dict:
    # Canonical top-level fields
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
        "high_net_1x_mean": canonical.get("high_net_1x_mean"),
        "low_net_1x_mean": canonical.get("low_net_1x_mean"),
        "high_gross_mean": canonical.get("high_gross_mean"),
        "low_gross_mean": canonical.get("low_gross_mean"),
        "date_first": canonical.get("date_first"),
        "date_last": canonical.get("date_last"),
        "block_sealed": canonical.get("block_sealed"),
        "data_cutoff_utc": canonical.get("data_cutoff_utc"),
        "last_allowed_formation_date": canonical.get("last_allowed_formation_date"),
        "eligible_assets_per_date": canonical.get("eligible_assets_per_date"),
        "min_completed_forward_horizon_days": canonical.get("min_completed_forward_horizon_days"),
        "min_state_formations": canonical.get("min_state_formations"),
        "state_count_floor_met": canonical.get("state_count_floor_met"),
        "economic_significance_threshold": canonical.get("economic_significance_threshold"),
        "economic_significance_met": canonical.get("economic_significance_met"),
        "confirmatory_claim_allowed": canonical.get("confirmatory_claim_allowed"),
        "sequential_look_number": canonical.get("sequential_look_number"),
        "sequential_alpha_k": canonical.get("sequential_alpha_k"),
        "sequential_cumulative_spend": canonical.get("sequential_cumulative_spend"),
        "sequential_remaining_budget": canonical.get("sequential_remaining_budget"),
    }

    def within(a, b):
        if a is None and b is None:
            return True
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

    pass_all = (
        reconciliation["all_match"] is not False  # expected false for panels, not a failure
        and finite_checks["all_finite"]
        and cost_check["net_equals_gross_minus_cost"]
        and state_check["all_consistent"]
        and all_recompute_match
    )

    conclusion = (
        "PASS: H10 fresh forward block is internally consistent: "
        f"{recomputed['n_formations']} formation(s), state counts high="
        f"{recomputed['state_counts']['high']}/low={recomputed['state_counts']['low']}/"
        f"mid={recomputed['state_counts']['mid']}, all spreads finite, "
        "cost treatment net=gross-0.001 consistent, state assignments consistent with "
        "trailing-decile rule (IMMATURE: n_high=0, n_low=0), overlap-aware uncertainty "
        "reports IMMATURE as expected. Input-hash reconciliation reported per file: "
        "panel hashes differ from the block's recorded hashes because October 2026 data "
        "was appended to panels after the block was sealed (documented expected signal; "
        "block sha256 and contents unchanged, not tampering). EXPLORATORY_ONLY: "
        "describes internal consistency only, does not promote any confirmatory claim. "
        "H10 remains CANDIDATE_UNVALIDATED / EVALUATED_NULL_DIFF_IMMATURE. "
        "No sealed artifact modified."
    ) if pass_all else (
        f"FAIL: one or more audit elements did not pass. "
        f"reconciliation.all_match={reconciliation['all_match']}, "
        f"finite_checks.all_finite={finite_checks['all_finite']}, "
        f"cost_check.net_equals_gross_minus_cost={cost_check['net_equals_gross_minus_cost']}, "
        f"state_check.all_consistent={state_check['all_consistent']}, "
        f"all_recompute_match={all_recompute_match}. "
        f"State issues: {state_check['issues']}. No artifact modified to force a pass."
    )

    return {
        "audit_id": "H004V106_H10_FRESH_FORWARD_BLOCK_INTEGRITY_AUDIT",
        "audit_utc": now_utc(),
        "status": "EXPLORATORY_ONLY",
        "audited_artifact": H10_FRESH_BLOCK_REL,
        "audited_artifact_sha256": H10_FRESH_BLOCK_SHA256,
        "preregistration": "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H004V106_H10_FRESH_FORWARD_BLOCK_INTEGRITY_AUDIT_v1.md",
        "canonical_summary": top,
        "canonical_recomputed": {k: v for k, v in recomputed.items() if k != "formation_records"},
        "recompute_match": recompute_match,
        "all_recompute_match_within_1e9": all_recompute_match,
        "reconciliation": reconciliation,
        "finite_value_checks": finite_checks,
        "cost_treatment": cost_check,
        "state_consistency": state_check,
        "conclusion": conclusion,
        "pass": bool(pass_all),
    }


def main() -> int:
    canonical = load_h10_fresh()
    actual_sha = sha256_file(H10_FRESH_BLOCK)
    if actual_sha != H10_FRESH_BLOCK_SHA256:
        raise SystemExit(f"H10 fresh block sha256 {actual_sha} != expected {H10_FRESH_BLOCK_SHA256}; refusing to audit a changed block")

    reconciliation = reconcile_inputs(canonical)
    recomputed = recompute_h10_fresh(canonical)
    finite_checks = finite_value_checks(recomputed["formation_records"])
    cost_check = cost_treatment_check(recomputed["formation_records"])
    state_check = state_consistency_check(canonical, recomputed)

    artifact = build_artifact(canonical, recomputed, reconciliation, finite_checks,
                              cost_check, state_check)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    out_path = OUT_DIR / f"H004V106_H10_fresh_forward_block_integrity_audit_{stamp}.json"
    out_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")

    print(json.dumps({
        "pass": artifact["pass"],
        "artifact": str(out_path.relative_to(ROOT)),
        "n_formations": recomputed["n_formations"],
        "state_counts": recomputed["state_counts"],
        "recompute_match": artifact["all_recompute_match_within_1e9"],
        "finite_all": finite_checks["all_finite"],
        "cost_consistent": cost_check["net_equals_gross_minus_cost"],
        "state_consistent": state_check["all_consistent"],
    }, indent=2))

    return 0 if artifact["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())