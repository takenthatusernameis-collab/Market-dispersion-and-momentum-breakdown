#!/usr/bin/env python3
"""H004V106 rolling dispersion-window robustness diagnostic (DISP-003-REGIME-002).

Executes preregistration artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/
preregistrations/H004V106_ROLLING_DISPERSION_WINDOW_v1.md.

Reads the canonical sealed forward block (read-only) and re-runs the anchor's
trailing-window outer-decile state assignment with reference windows
W in {30, 90, 180, 270, 365} observations. W=365 reproduces the anchor
exactly (predeclared internal control; if it does not, the script has a bug
and the run is invalid).

For each window, using only formations assigned high or low state:
  n_high, n_low, mean spread_net_1x per state, high_low_diff_net_1x,
  and the 2025-10 leave-one-out high_low_diff_net_1x with its delta fraction
  vs the full-window estimate.

Per-window label (predeclared): SPARSE if n_high < 5 or n_low < 5, else
SIGN_POSITIVE / SIGN_NEGATIVE / SIGN_ZERO by the sign of the diff.
Overall label (predeclared): ROLLING_ROBUST only if every adequate window
(n_high >= 5 and n_low >= 5) is SIGN_POSITIVE and every such window's
2025-10 leave-one-out delta fraction lies within [-0.50, +0.50];
otherwise ROLLING_FRAGILE.

All analyses are EXPLORATORY_ONLY; no inference claims, no promotion, no
frozen artifact modified. Writes a new audit artifact under integrity_audit/.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
BLOCK_PATH = ART / "forward_block" / "forward_block_evaluation.json"
OUT_DIR = ART / "integrity_audit"
OUT_PATH = OUT_DIR / "H004V106_rolling_dispersion_window_20261028.json"
PREREG_PATH = ART / "preregistrations" / "H004V106_ROLLING_DISPERSION_WINDOW_v1.md"

EXPERIMENT_ID = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-REGIME-002"
REFERENCE_HIGH_LOW_DIFF_NET_1X = 0.6165223953929935
WINDOWS = (30, 90, 180, 270, 365)
MIN_PRIOR_OBS = 30
MIN_PER_STATE = 5
DELTA_FRAC_BAND = 0.50
REPRO_TOLERANCE = 1e-9


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def assign_states(formations: list[dict], window_days: int) -> list[dict]:
    """Recompute anchor state labels with a trailing reference window.

    Mirrors scripts/eval_forward_block.py: past = dispersions of formations
    up to (but not including) the current one, capped at window_days
    observations; state requires >= MIN_PRIOR_OBS prior observations; outer
    deciles of the past define high / low, everything else mid.
    """
    dser = pd.Series(
        {r["formation_date"]: r["dispersion"] for r in formations}
    ).sort_index()
    labeled = []
    for r in formations:
        T = r["formation_date"]
        past = dser.loc[:T].iloc[:-1].tail(window_days)
        state = "mid"
        if len(past) >= MIN_PRIOR_OBS:
            thr_hi = float(past.quantile(0.9))
            thr_lo = float(past.quantile(0.1))
            if r["dispersion"] >= thr_hi:
                state = "high"
            elif r["dispersion"] <= thr_lo:
                state = "low"
        row = dict(r)
        row["state"] = state
        labeled.append(row)
    return labeled


def window_metrics(rows: list[dict]) -> dict:
    hi = [r["spread_net_1x"] for r in rows if r["state"] == "high"]
    lo = [r["spread_net_1x"] for r in rows if r["state"] == "low"]
    n_high, n_low = len(hi), len(lo)
    diff = (float(pd.Series(hi).mean()) - float(pd.Series(lo).mean())) if hi and lo else None
    return {
        "n_formations": len(rows),
        "n_high": n_high,
        "n_low": n_low,
        "n_mid": len(rows) - n_high - n_low,
        "mean_high_net_1x": float(pd.Series(hi).mean()) if hi else None,
        "mean_low_net_1x": float(pd.Series(lo).mean()) if lo else None,
        "high_low_diff_net_1x": diff,
    }


def window_label(n_high: int, n_low: int, diff) -> str:
    if n_high < MIN_PER_STATE or n_low < MIN_PER_STATE:
        return "SPARSE"
    if diff is None:
        return "SIGN_ZERO"
    if diff > 0:
        return "SIGN_POSITIVE"
    if diff < 0:
        return "SIGN_NEGATIVE"
    return "SIGN_ZERO"


def main() -> int:
    block = json.loads(BLOCK_PATH.read_text(encoding="utf-8"))
    formations = block["formations"]
    baseline = block["high_low_diff_net_1x"]
    no_oct_rows = [r for r in formations if not r["formation_date"].startswith("2025-10")]

    window_results = []
    for W in WINDOWS:
        labeled = assign_states(formations, W)
        full = window_metrics([r for r in labeled if r["state"] in ("high", "low")])
        diff_full = full["high_low_diff_net_1x"]

        labeled_no_oct = assign_states(no_oct_rows, W)
        excl = window_metrics(
            [r for r in labeled_no_oct if r["state"] in ("high", "low")]
        )
        diff_excl = excl["high_low_diff_net_1x"]
        delta_frac = (
            (diff_excl - diff_full) / diff_full
            if diff_full is not None and diff_full != 0
            else None
        )

        label = window_label(full["n_high"], full["n_low"], diff_full)
        adequate = full["n_high"] >= MIN_PER_STATE and full["n_low"] >= MIN_PER_STATE
        window_results.append({
            "W": W,
            "n_formations": full["n_formations"],
            "n_high": full["n_high"],
            "n_low": full["n_low"],
            "n_mid": full["n_mid"],
            "mean_high_net_1x": full["mean_high_net_1x"],
            "mean_low_net_1x": full["mean_low_net_1x"],
            "high_low_diff_net_1x": diff_full,
            "high_low_diff_net_1x_without_2025_10": diff_excl,
            "delta_fraction_vs_full": delta_frac,
            "label": label,
            "adequate": adequate,
            "note": "2025-10 leave-one-out recomputes state assignment on the sample excluding 2025-10 formations.",
        })

    w365 = window_results[-1]
    reproduction_ok = (
        w365["high_low_diff_net_1x"] is not None
        and abs(w365["high_low_diff_net_1x"] - REFERENCE_HIGH_LOW_DIFF_NET_1X)
        <= REPRO_TOLERANCE
    )
    if not reproduction_ok:
        print(
            "[rolling-window] INVALID RUN: W=365 "
            f"{w365['high_low_diff_net_1x']} != reference "
            f"{REFERENCE_HIGH_LOW_DIFF_NET_1X}"
        )
        return 2

    adequate = [wr for wr in window_results if wr["adequate"]]
    overall = (
        "ROLLING_ROBUST"
        if adequate
        and all(wr["label"] == "SIGN_POSITIVE" for wr in adequate)
        and all(
            wr["delta_fraction_vs_full"] is not None
            and abs(wr["delta_fraction_vs_full"]) <= DELTA_FRAC_BAND
            for wr in adequate
        )
        else "ROLLING_FRAGILE"
    )

    out = {
        "audit_id": "H004V106_ROLLING_DISPERSION_WINDOW_20261028",
        "experiment_id": EXPERIMENT_ID,
        "status": "EXPLORATORY_ONLY",
        "preregistration": (
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/"
            "preregistrations/H004V106_ROLLING_DISPERSION_WINDOW_v1.md"
        ),
        "audited_artifact": (
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/"
            "forward_block/forward_block_evaluation.json"
        ),
        "computed_utc": now_utc(),
        "baseline": {
            "n_formations": block["n_formations"],
            "n_high": block["n_high"],
            "n_low": block["n_low"],
            "n_mid": block["n_mid"],
            "high_low_diff_net_1x": baseline,
            "data_cutoff_utc": block["data_cutoff_utc"],
            "date_first": block["date_first"],
            "date_last": block["date_last"],
        },
        "anchor_reproduction_check": {
            "W": 365,
            "high_low_diff_net_1x": w365["high_low_diff_net_1x"],
            "reference_high_low_diff_net_1x": REFERENCE_HIGH_LOW_DIFF_NET_1X,
            "tolerance": REPRO_TOLERANCE,
            "match": reproduction_ok,
            "note": "W=365 must reproduce the canonical anchor exactly; otherwise the script has a bug and the run is invalid.",
        },
        "window_results": window_results,
        "overall_label": overall,
        "decision_rule": (
            "ROLLING_ROBUST only if every adequate window (n_high>=5 and "
            "n_low>=5) is SIGN_POSITIVE and every such window's 2025-10 "
            f"leave-one-out delta fraction is within [-{DELTA_FRAC_BAND}, "
            f"+{DELTA_FRAC_BAND}]; otherwise ROLLING_FRAGILE. All "
            "EXPLORATORY_ONLY."
        ),
        "conclusion": (
            "Rolling dispersion-window reassignment is EXPLORATORY_ONLY: it "
            "tests state-construction sensitivity on the already-inspected "
            "sealed forward block. No result promotes a hypothesis, unlocks "
            "the confirmatory track, or serves as independent confirmation. "
            "A genuinely fresh sealed forward block with formations after "
            "2026-09-29 remains required for any confirmatory claim."
        ),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"[rolling-window] overall={overall} "
        f"w365_diff={w365['high_low_diff_net_1x']} reproduction_ok={reproduction_ok} "
        f"out={OUT_PATH.relative_to(ROOT)}"
    )
    for wr in window_results:
        print(
            f"[rolling-window] W={wr['W']} n_high={wr['n_high']} n_low={wr['n_low']} "
            f"diff={wr['high_low_diff_net_1x']} "
            f"diff_excl_2025_10={wr['high_low_diff_net_1x_without_2025_10']} "
            f"delta_frac={wr['delta_fraction_vs_full']} label={wr['label']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
