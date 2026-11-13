#!/usr/bin/env python3
"""F1 coverage-outcome sensitivity for the frozen H004V106 anchor.

DISP-003-F1SENS-002 (H24, EXPLORATORY_ONLY). The F1COVERAGE-001 repair (H23)
re-acquired the four symbols missing from the committed DISPERSION-003 Binance
archive for 2025-01..2026-09 and raised the descriptive eligible-asset count on
the canonical H004V106 formation dates from 26-27 to 29-31. The frozen canonical
forward block was estimated on 26-27 assets. This script measures whether the
anchor's formation outcome changes when the four repaired kline panels are added,
over the identical sealed canonical window, using the unmodified evaluator
functions imported from ``scripts/eval_forward_block.py``.

It computes no p-value, no multiple-testing family and no promotion. It never
writes to the committed panels, raw archive, canonical block or H10 fresh block;
all inputs are read-only and byte-verified unchanged at the end of the run.

Usage:
    python3 scripts/f1_coverage_outcome_sensitivity.py [--out PATH]

No network: reuses the already-fetched F1 panels on disk.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import eval_forward_block as ef  # noqa: E402  (unmodified evaluator, for fidelity)

OLD_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
NEW_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1SENS-002"
F1_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001"

OLD_PANELS = ROOT / "artifacts" / OLD_EXP / "data" / "panels"
F1_PANELS = ROOT / "artifacts" / F1_EXP / "data" / "panels"
CANONICAL_BLOCK = ROOT / "artifacts" / OLD_EXP / "forward_block" / "forward_block_evaluation.json"
H10_FRESH_BLOCK = ROOT / "artifacts" / OLD_EXP / "forward_block_h10_fresh" / "forward_block_evaluation.json"
AUDIT_DIR = ROOT / "artifacts" / NEW_EXP / "integrity_audit"

F1_SYMBOLS = ["1INCHUSDT", "AAVEUSDT", "ACHUSDT", "AGLDUSDT"]

# Frozen artifact hashes that must be byte-identical after the run.
FROZEN_HASHES = {
    "forward_block/forward_block_evaluation.json":
        "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
    "forward_block_h10_fresh/forward_block_evaluation.json":
        "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f",
}

DATA_CUTOFF = "2026-09-30"
BLOCK_START = ef.FORWARD_BLOCK_START
FIELDS_TOL = 1e-9


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_repaired_klines() -> dict[str, pd.DataFrame]:
    """Load the four F1-repaired kline panels using the evaluator's parsing."""
    out: dict[str, pd.DataFrame] = {}
    for sym in F1_SYMBOLS:
        p = F1_PANELS / f"binance_klines_{sym}.csv"
        df = pd.read_csv(p)
        df = df.rename(columns={"open_time": "ts"})
        df["date"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        out[sym] = df[["date", "close"]].copy()
    return out


def evaluate(px: dict[str, pd.DataFrame], mc: pd.DataFrame) -> dict:
    """Reproduce eval_forward_block.main()'s formation loop for a given panel set.

    Uses only the evaluator's own functions so the arithmetic is identical to the
    frozen block. Returns the same summary fields the committed artifact carries.
    """
    px_wide = ef.build_price_wide_all(px)
    mom_cache = ef.MomentumCache(px_wide)
    elig_map = ef.build_eligibility_map(mc, px)

    idx = px_wide.index
    cutoff_ts = pd.Timestamp(DATA_CUTOFF, tz="UTC")
    if cutoff_ts not in idx:
        raise ValueError(f"data cutoff {DATA_CUTOFF} is not a panel observation date")
    cutoff_loc = idx.get_loc(cutoff_ts)
    horizon = ef.ANCHOR_PARAMS["forward_horizon_days"]
    last_allowed = idx[cutoff_loc - horizon]
    last_allowed_str = last_allowed.strftime("%Y-%m-%d")

    lookback = ef.ANCHOR_PARAMS["momentum_lookback_days"]
    estimator = ef.ANCHOR_PARAMS["dispersion_estimator"]
    window_days = ef.ANCHOR_PARAMS["dispersion_window_days"]
    state_rule = ef.ANCHOR_PARAMS["dispersion_state_rule"]

    formation_records = []
    for T, elig in sorted(elig_map.items()):
        if T < BLOCK_START:
            continue
        if T > last_allowed_str:
            continue
        assets = sorted(elig.keys())
        n_elig = len(assets)
        if n_elig < ef.MIN_ASSETS_DECILES:
            continue
        mom = mom_cache.get(T, lookback, tuple(assets))
        mom = mom.dropna()
        if len(mom) < ef.MIN_ASSETS_DECILES:
            continue
        disp = ef.compute_dispersion(mom, estimator)
        top, bot = ef.portfolio_spread(mom, state_rule)
        if not top or not bot:
            continue
        fwd = ef.forward_returns(px_wide, T, horizon, list(set(top) | set(bot)))
        if not fwd:
            continue
        top_ret = float(pd.Series({a: fwd[a] for a in top if a in fwd}).mean()) if any(a in fwd for a in top) else float("nan")
        bot_ret = float(pd.Series({a: fwd[a] for a in bot if a in fwd}).mean()) if any(a in fwd for a in bot) else float("nan")
        if math.isnan(top_ret) or math.isnan(bot_ret):
            continue
        spread_gross = top_ret - bot_ret
        spread_net_1x = spread_gross - ef.COST_1X
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
        return {"status": "BLOCKED", "reason": "no_formations_passed_data_gate",
                "last_allowed_formation_date": last_allowed_str}

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
    from collections import Counter
    dist = {str(k): v for k, v in sorted(Counter(elig_counts).items())}

    return {
        "status": "OK",
        "last_allowed_formation_date": last_allowed_str,
        "n_formations": n_formations,
        "n_high": n_high,
        "n_low": n_low,
        "n_mid": n_mid,
        "spread_gross_mean": float(gross.mean()) if len(gross) else None,
        "spread_net_1x_mean": float(net.mean()) if len(net) else None,
        "spread_gross_median": float(gross.median()) if len(gross) else None,
        "spread_net_1x_median": float(net.median()) if len(net) else None,
        "high_gross_mean": float(hi.mean()) if len(hi) else None,
        "low_gross_mean": float(lo.mean()) if len(lo) else None,
        "high_net_1x_mean": float(hi_net.mean()) if len(hi_net) else None,
        "low_net_1x_mean": float(lo_net.mean()) if len(lo_net) else None,
        "high_low_diff_gross": diff_gross,
        "high_low_diff_net_1x": diff_net,
        "date_first": df["formation_date"].iloc[0],
        "date_last": df["formation_date"].iloc[-1],
        "eligible_assets_per_date": {
            "mean": float(statistics.mean(elig_counts)) if elig_counts else 0.0,
            "min": int(min(elig_counts)) if elig_counts else 0,
            "max": int(max(elig_counts)) if elig_counts else 0,
            "distribution": dist,
        },
        "overlap_aware_uncertainty": ef.overlap_aware_interval(
            results_rows, n_boot=2000, rng_seed=20261102
        ),
        "formations": [
            {
                "formation_date": r["formation_date"],
                "state": r["state"],
                "dispersion": r["dispersion"],
                "n_assets": r["n_assets"],
                "spread_gross": r["spread_gross"],
                "spread_net_1x": r["spread_net_1x"],
            }
            for r in results_rows
        ],
    }


def fidelity_check(arm_a: dict, block: dict) -> dict:
    """Assert arm A reproduces the committed canonical block within 1e-9."""
    checks = {}
    ok = True
    for field in ("n_formations", "n_high", "n_low", "n_mid",
                  "high_low_diff_net_1x", "spread_net_1x_mean",
                  "spread_net_1x_median", "date_first", "date_last"):
        expected = block.get(field)
        actual = arm_a.get(field)
        if isinstance(expected, float) or isinstance(actual, float):
            match = (expected is not None and actual is not None
                     and abs(float(actual) - float(expected)) <= FIELDS_TOL)
        else:
            match = (actual == expected)
        checks[field] = {"expected": expected, "actual": actual, "match": bool(match)}
        ok = ok and match
    return {"pass": bool(ok), "tolerance": FIELDS_TOL, "fields": checks}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None, help="artifact path (default: integrity_audit/)")
    args = ap.parse_args()

    started = now_utc()

    # Read-only snapshots of committed inputs before computing.
    committed_panel_hashes = {p.name: sha256_file(p) for p in sorted(OLD_PANELS.glob("*.csv"))}
    frozen_before = {}
    for rel in FROZEN_HASHES:
        p = ROOT / "artifacts" / OLD_EXP / rel
        frozen_before[rel] = sha256_file(p)

    mc = ef.load_marketcap()
    px_committed = ef.load_binance_panel("klines")

    # Arm A: committed panels (must reproduce the frozen canonical block).
    arm_a = evaluate(px_committed, mc)

    # Arm B: committed panels with the four F1-repaired klines overriding.
    px_repaired = dict(px_committed)
    repaired = load_repaired_klines()
    for sym, df in repaired.items():
        px_repaired[sym] = df
    arm_b = evaluate(px_repaired, mc)

    block = json.loads(CANONICAL_BLOCK.read_text(encoding="utf-8"))
    fid = fidelity_check(arm_a, block)

    # Primary descriptive contrast.
    contrast = None
    if arm_a.get("status") == "OK" and arm_b.get("status") == "OK":
        a = arm_a["high_low_diff_net_1x"]
        b = arm_b["high_low_diff_net_1x"]
        if a is not None and b is not None:
            contrast = {
                "arm_a_high_low_diff_net_1x": a,
                "arm_b_high_low_diff_net_1x": b,
                "delta_b_minus_a": b - a,
                "n_high_a": arm_a["n_high"], "n_high_b": arm_b["n_high"],
                "n_low_a": arm_a["n_low"], "n_low_b": arm_b["n_low"],
                "n_formations_a": arm_a["n_formations"],
                "n_formations_b": arm_b["n_formations"],
            }

    # Read-only checks after computing.
    committed_panel_hashes_after = {p.name: sha256_file(p) for p in sorted(OLD_PANELS.glob("*.csv"))}
    old_panels_byte_unchanged = (committed_panel_hashes == committed_panel_hashes_after)
    frozen_after = {}
    for rel in FROZEN_HASHES:
        p = ROOT / "artifacts" / OLD_EXP / rel
        frozen_after[rel] = {"expected": FROZEN_HASHES[rel],
                             "actual": sha256_file(p),
                             "match": sha256_file(p) == FROZEN_HASHES[rel]}
    frozen_unchanged = all(v["match"] for v in frozen_after.values())

    # Verdict.
    if not fid["pass"]:
        verdict = "FAIL"
    elif arm_a.get("status") != "OK" or arm_b.get("status") != "OK":
        verdict = "FAIL"
    elif not (old_panels_byte_unchanged and frozen_unchanged):
        verdict = "FAIL"
    else:
        verdict = "PASS"

    artifact = {
        "audit_id": "DISP-003-F1SENS-002",
        "experiment_id": NEW_EXP,
        "hypothesis": "H24",
        "audit_type": "COVERAGE_OUTCOME_SENSITIVITY",
        "status": "EXPLORATORY_ONLY",
        "started_utc": started,
        "completed_utc": now_utc(),
        "offline": True,
        "estimand": "descriptive sensitivity of the frozen H004V106 anchor formation "
                    "outcome to adding the four F1-repaired assets over the identical "
                    "sealed canonical window; no p-value, no multiple-testing family, "
                    "no promotion",
        "inputs": {
            "committed_panels": str(OLD_PANELS.relative_to(ROOT)),
            "f1_repaired_panels": str(F1_PANELS.relative_to(ROOT)),
            "repaired_symbols": F1_SYMBOLS,
            "data_cutoff_utc": f"{DATA_CUTOFF}T00:00:00Z",
            "block_start": BLOCK_START,
            "anchor_parameters": ef.ANCHOR_PARAMS,
            "cost_1x": ef.COST_1X,
            "min_assets_deciles": ef.MIN_ASSETS_DECILES,
        },
        "fidelity_check": fid,
        "arm_a_committed": arm_a,
        "arm_b_repaired": arm_b,
        "primary_contrast": contrast,
        "read_only_checks": {
            "old_panels_byte_unchanged": old_panels_byte_unchanged,
            "committed_panel_sha256": committed_panel_hashes_after,
            "frozen_artifacts": frozen_after,
        },
        "disposition": {
            "frozen_artifacts_modified": not frozen_unchanged,
            "old_panels_modified": not old_panels_byte_unchanged,
            "outcomes_computed": True,
            "note": "outcomes are computed on the already-inspected development "
                    "window for a sensitivity contrast only; this is EXPLORATORY_ONLY "
                    "and is not independent confirmation of any hypothesis",
        },
        "verdict": verdict,
        "notes": [
            "Arm A must reproduce the committed canonical block exactly (fidelity_check); "
            "if it does not, the script fails and writes no comparison.",
            "Arm B substitutes only the four F1-repaired kline panels; every other "
            "input, parameter, cost and rule is identical.",
            "No network: reuses the already-fetched F1 panels on disk.",
            "The canonical block and H10 fresh block are read-only and byte-verified "
            "unchanged at the end of the run.",
        ],
    }

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    if args.out:
        out_path = Path(args.out)
    else:
        out_path = AUDIT_DIR / f"f1_coverage_outcome_sensitivity_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")

    print(f"[f1sens] verdict={verdict} fidelity_pass={fid['pass']}")
    if contrast:
        print(f"[f1sens] arm_a high_low_diff_net_1x={contrast['arm_a_high_low_diff_net_1x']} "
              f"(n_high={contrast['n_high_a']} n_low={contrast['n_low_a']})")
        print(f"[f1sens] arm_b high_low_diff_net_1x={contrast['arm_b_high_low_diff_net_1x']} "
              f"(n_high={contrast['n_high_b']} n_low={contrast['n_low_b']})")
        print(f"[f1sens] delta_b_minus_a={contrast['delta_b_minus_a']}")
    print(f"[f1sens] old_panels_byte_unchanged={old_panels_byte_unchanged} "
          f"frozen_unchanged={frozen_unchanged}")
    try:
        shown = out_path.relative_to(ROOT)
    except ValueError:
        shown = out_path
    print(f"[f1sens] output -> {shown}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())