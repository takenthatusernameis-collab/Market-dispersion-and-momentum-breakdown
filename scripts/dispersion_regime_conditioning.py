#!/usr/bin/env python3
"""H004V106 dispersion-regime conditioning diagnostic (DISP-003-REGIME-001).

Executes preregistration artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/
preregistrations/H004V106_DISPERSION_REGIME_CONDITIONING_v1.md.

Reads the canonical sealed forward block (read-only) and runs four
descriptive/exploratory analyses:
  A. Continuous dispersion-spread association (Pearson/Spearman), all 608
     formations and with 2025-10 excluded.
  B. Dispersion-regime split by full-block median dispersion; high-minus-low
     diff per regime.
  C. 2025-10 conditioning: high-minus-low diff with vs without 2025-10.
  D. Dispersion decile-bucket profile of mean spread_net_1x.

All analyses are EXPLORATORY_ONLY; no inference claims, no promotion, no
frozen artifact modified. Writes a new audit artifact under integrity_audit/.
"""

from __future__ import annotations

import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
BLOCK_PATH = ART / "forward_block" / "forward_block_evaluation.json"
OUT_DIR = ART / "integrity_audit"
OUT_PATH = OUT_DIR / "H004V106_dispersion_regime_conditioning_20261028.json"
PREREG_PATH = ART / "preregistrations" / "H004V106_DISPERSION_REGIME_CONDITIONING_v1.md"

EXPERIMENT_ID = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-REGIME-001"
CONTINUOUS_ASSOC_THRESHOLD = 0.30
REGIME_MIN_PER_STATE = 10


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx = statistics.mean(xs)
    my = statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def ranks(vals):
    ordered = sorted((v, i) for i, v in enumerate(vals))
    out = [0.0] * len(vals)
    i = 0
    while i < len(ordered):
        j = i
        while j + 1 < len(ordered) and ordered[j + 1][0] == ordered[i][0]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[ordered[k][1]] = avg_rank
        i = j + 1
    return out


def spearman(xs, ys):
    return pearson(ranks(xs), ranks(ys))


def high_low_diff(rows):
    hi = [r["spread_net_1x"] for r in rows if r["state"] == "high"]
    lo = [r["spread_net_1x"] for r in rows if r["state"] == "low"]
    if not hi or not lo:
        return None, len(hi), len(lo)
    return statistics.mean(hi) - statistics.mean(lo), len(hi), len(lo)


def main() -> int:
    block = json.loads(BLOCK_PATH.read_text(encoding="utf-8"))
    formations = block["formations"]
    baseline = block["high_low_diff_net_1x"]

    # --- A. Continuous dispersion-spread association ---
    disp_all = [r["dispersion"] for r in formations]
    spr_all = [r["spread_net_1x"] for r in formations]
    r_pearson_all = pearson(disp_all, spr_all)
    r_spearman_all = spearman(disp_all, spr_all)

    no_oct = [r for r in formations if not r["formation_date"].startswith("2025-10")]
    disp_no_oct = [r["dispersion"] for r in no_oct]
    spr_no_oct = [r["spread_net_1x"] for r in no_oct]
    r_pearson_no_oct = pearson(disp_no_oct, spr_no_oct)
    r_spearman_no_oct = spearman(disp_no_oct, spr_no_oct)

    cont_label = ("CONTINUOUS_ASSOCIATION_PRESENT"
                  if (r_spearman_no_oct is not None and abs(r_spearman_no_oct) >= CONTINUOUS_ASSOC_THRESHOLD)
                  else "WEAK_CONTINUOUS_ASSOCIATION")

    # --- B. Dispersion-regime split by full-block median dispersion ---
    median_disp = statistics.median(disp_all)
    reg_lo = [r for r in formations if r["dispersion"] <= median_disp]
    reg_hi = [r for r in formations if r["dispersion"] > median_disp]
    diff_lo, nh_lo, nl_lo = high_low_diff(reg_lo)
    diff_hi, nh_hi, nl_hi = high_low_diff(reg_hi)

    same_sign = True
    if diff_lo is not None and diff_hi is not None:
        same_sign = (diff_lo > 0) == (diff_hi > 0)
    regime_ok = (diff_lo is not None and diff_hi is not None
                 and same_sign
                 and nh_lo >= REGIME_MIN_PER_STATE and nl_lo >= REGIME_MIN_PER_STATE
                 and nh_hi >= REGIME_MIN_PER_STATE and nl_hi >= REGIME_MIN_PER_STATE)
    regime_label = "REGIME_ROBUST" if regime_ok else "REGIME_SPARSE_OR_SIGN_FLIP"

    # --- C. 2025-10 conditioning ---
    diff_included, nh_inc, nl_inc = high_low_diff(formations)
    diff_excluded, nh_exc, nl_exc = high_low_diff(no_oct)
    delta_frac = ((diff_excluded - baseline) / baseline) if baseline else None

    # --- D. Dispersion decile-bucket profile ---
    order = sorted(range(len(formations)), key=lambda i: formations[i]["dispersion"])
    n = len(order)
    bucket_size = n // 10
    buckets = []
    for b in range(10):
        start = b * bucket_size
        end = n if b == 9 else (b + 1) * bucket_size
        idx = order[start:end]
        bucket_rows = [formations[i] for i in idx]
        dmin = min(r["dispersion"] for r in bucket_rows)
        dmax = max(r["dispersion"] for r in bucket_rows)
        diff_b, nh_b, nl_b = high_low_diff(bucket_rows)
        buckets.append({
            "bucket": b + 1,
            "n": len(bucket_rows),
            "dispersion_min": dmin,
            "dispersion_max": dmax,
            "n_high": nh_b,
            "n_low": nl_b,
            "mean_spread_net_1x": statistics.mean(r["spread_net_1x"] for r in bucket_rows),
            "high_low_diff_net_1x": diff_b,
        })

    out = {
        "audit_id": "H004V106_DISPERSION_REGIME_CONDITIONING_20261028",
        "experiment_id": EXPERIMENT_ID,
        "status": "EXPLORATORY_ONLY",
        "preregistration": "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H004V106_DISPERSION_REGIME_CONDITIONING_v1.md",
        "audited_artifact": "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json",
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
        "A_continuous_dispersion_spread_association": {
            "all_formations": {
                "n": len(formations),
                "pearson_r": r_pearson_all,
                "spearman_rho": r_spearman_all,
            },
            "excluding_2025_10": {
                "n": len(no_oct),
                "pearson_r": r_pearson_no_oct,
                "spearman_rho": r_spearman_no_oct,
            },
            "threshold_abs_rho": CONTINUOUS_ASSOC_THRESHOLD,
            "label": cont_label,
        },
        "B_dispersion_regime_split": {
            "median_dispersion": median_disp,
            "regime_low_dispersion": {
                "n": len(reg_lo),
                "n_high": nh_lo,
                "n_low": nl_lo,
                "high_low_diff_net_1x": diff_lo,
            },
            "regime_high_dispersion": {
                "n": len(reg_hi),
                "n_high": nh_hi,
                "n_low": nl_hi,
                "high_low_diff_net_1x": diff_hi,
            },
            "same_sign_in_both_regimes": same_sign,
            "min_per_state": REGIME_MIN_PER_STATE,
            "label": regime_label,
        },
        "C_2025_10_conditioning": {
            "with_2025_10": {
                "n": len(formations),
                "n_high": nh_inc,
                "n_low": nl_inc,
                "high_low_diff_net_1x": diff_included,
            },
            "without_2025_10": {
                "n": len(no_oct),
                "n_high": nh_exc,
                "n_low": nl_exc,
                "high_low_diff_net_1x": diff_excluded,
            },
            "baseline_high_low_diff_net_1x": baseline,
            "delta_fraction_vs_baseline": delta_frac,
            "note": "Reproduces H8 leave-one-out finding descriptively; no label change.",
        },
        "D_dispersion_decile_buckets": {
            "n_buckets": 10,
            "buckets": buckets,
            "note": "Descriptive profile; inspect monotonicity of mean spread across dispersion deciles.",
        },
        "conclusion": (
            "All four analyses are EXPLORATORY_ONLY descriptive diagnostics on the "
            "already-inspected sealed forward block. No result promotes a hypothesis, "
            "unlocks the confirmatory track, or serves as independent confirmation. "
            "A genuinely fresh sealed forward block with formations after 2026-09-29 "
            "remains required for any confirmatory claim."
        ),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[regime-conditioning] cont={cont_label} regime={regime_label} "
          f"pearson_excl_oct={r_pearson_no_oct} out={OUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
