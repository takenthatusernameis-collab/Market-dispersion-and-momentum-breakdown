"""Corrected paired block-bootstrap inference for Phase C and Phase F.

The original `run_all_phases_c_g.py` computed the high-minus-low difference
confidence interval by bootstrapping a degenerate single-element series
(`pd.Series([diff])`), which collapses every interval to a point. This script
recomputes the intervals properly using a paired block bootstrap over the
formation-level series, and writes corrected summaries.

Method (frozen before outcomes are inspected here):
  - Formations are kept in chronological order.
  - High and low state series are aligned by formation index; the difference
    is taken per formation (paired), so states with unequal coverage still
    produce a valid difference series (missing legs are NaN and dropped).
  - Block bootstrap with fixed seed, block length 3, 10000 replications,
    two-sided 95% percentile interval.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-002"
OUT_DIR = ROOT / "artifacts" / EXP

SEED = 12345
N_BOOT = 10000
BLOCK_SIZE = 3
ALPHA = 0.05


def block_bootstrap_ci(series: pd.Series) -> tuple:
    s = series.dropna()
    if len(s) == 0:
        return (None, None)
    rng = np.random.RandomState(SEED)
    n = len(s)
    n_blocks = int(np.ceil(n / BLOCK_SIZE))
    means = []
    for _ in range(N_BOOT):
        idxs = []
        for _ in range(n_blocks):
            start = rng.randint(0, max(1, n - BLOCK_SIZE + 1))
            for j in range(BLOCK_SIZE):
                if start + j < n:
                    idxs.append(start + j)
        idxs = idxs[:n]
        means.append(float(s.iloc[idxs].mean()))
    means_sorted = sorted(means)
    lo = means_sorted[int(ALPHA / 2 * N_BOOT)]
    hi = means_sorted[int((1 - ALPHA / 2) * N_BOOT)]
    return (lo, hi)


def paired_diff_series(hi: pd.Series, lo: pd.Series) -> pd.Series:
    """Pair high and low by formation date; difference per formation."""
    df = pd.concat(
        [hi.rename("hi"), lo.rename("lo")], axis=1
    )
    return (df["hi"] - df["lo"]).dropna()


def main() -> None:
    # ---- Phase C -----------------------------------------------------------
    cond = pd.read_csv(OUT_DIR / "formation_returns_conditioned.csv")
    cond["formation_date"] = cond["formation_date"].astype(str)

    hi = cond.loc[cond["state"] == "high", "momentum_spread_gross"].dropna()
    lo = cond.loc[cond["state"] == "low", "momentum_spread_gross"].dropna()

    # paired difference series (per formation date)
    hi_s = cond.loc[cond["state"] == "high"].set_index("formation_date")["momentum_spread_gross"]
    lo_s = cond.loc[cond["state"] == "low"].set_index("formation_date")["momentum_spread_gross"]
    diff_series = paired_diff_series(hi_s, lo_s)

    hi_ci = block_bootstrap_ci(hi)
    lo_ci = block_bootstrap_ci(lo)
    diff_ci = block_bootstrap_ci(diff_series)

    phase_c_summary = json.loads((OUT_DIR / "phase_c_summary.json").read_text())
    phase_c_summary["high_gross_ci_95_blockboot"] = list(hi_ci)
    phase_c_summary["low_gross_ci_95_blockboot"] = list(lo_ci)
    phase_c_summary["high_low_diff_ci_95_blockboot"] = list(diff_ci)
    phase_c_summary["inference_method"] = {
        "type": "paired_block_bootstrap",
        "n_boot": N_BOOT,
        "block_size": BLOCK_SIZE,
        "seed": SEED,
        "alpha": ALPHA,
        "note": "Corrected: difference CI computed over paired per-formation "
                "difference series (not a degenerate point series).",
        "n_diff_observations": int(len(diff_series)),
    }
    (OUT_DIR / "phase_c_summary.json").write_text(
        json.dumps(phase_c_summary, indent=2, sort_keys=True) + "\n"
    )

    # ---- Phase F -----------------------------------------------------------
    phase_f = json.loads((OUT_DIR / "phase_f_summary.json").read_text())
    split_spec = phase_f.get("split", {})
    split_type = split_spec.get("type", "60/20/20")
    n_total = len(cond["formation_date"].unique())
    n_disc = int(split_spec.get("discovery_n", round(0.6 * n_total)))
    n_val = int(split_spec.get("validation_n", round(0.2 * n_total)))
    n_fin = int(split_spec.get("final_n", n_total - n_disc - n_val))
    all_dates = sorted(cond["formation_date"].unique())
    disc_dates, val_dates, fin_dates = (
        all_dates[:n_disc], all_dates[n_disc:n_disc + n_val], all_dates[n_disc + n_val:]
    )
    for split, dates in [("discovery", disc_dates), ("validation", val_dates), ("final", fin_dates)]:
        sub = cond[cond["formation_date"].isin(dates)]
        hi_s = sub.loc[sub["state"] == "high"].set_index("formation_date")["momentum_spread_gross"]
        lo_s = sub.loc[sub["state"] == "low"].set_index("formation_date")["momentum_spread_gross"]
        diff_series = paired_diff_series(hi_s, lo_s)
        diff = float(hi_s.mean() - lo_s.mean()) if len(hi_s) and len(lo_s) else None
        ci = block_bootstrap_ci(diff_series)
        phase_f[split]["diff_gross"] = diff
        phase_f[split]["diff_gross_ci_95"] = list(ci)
        phase_f[split]["n_diff_observations"] = int(len(diff_series))
    phase_f["inference_method"] = {
        "type": "paired_block_bootstrap",
        "n_boot": N_BOOT,
        "block_size": BLOCK_SIZE,
        "seed": SEED,
        "alpha": ALPHA,
        "note": "Corrected: difference CI computed over paired per-formation "
                "difference series within each chronological split.",
    }
    (OUT_DIR / "phase_f_summary.json").write_text(
        json.dumps(phase_f, indent=2, sort_keys=True) + "\n"
    )

    print("[phase C] diff CI:", phase_c_summary["high_low_diff_ci_95_blockboot"])
    print("[phase C] high CI:", phase_c_summary["high_gross_ci_95_blockboot"])
    print("[phase C] low CI:", phase_c_summary["low_gross_ci_95_blockboot"])
    for split in ["discovery", "validation", "final"]:
        print(f"[phase F {split}] diff={phase_f[split]['diff_gross']} "
              f"CI={phase_f[split]['diff_gross_ci_95']} "
              f"n_diff={phase_f[split]['n_diff_observations']}")


if __name__ == "__main__":
    main()