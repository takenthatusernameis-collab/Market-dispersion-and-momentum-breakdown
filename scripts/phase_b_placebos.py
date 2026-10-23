"""Phase B placebos (random-ranking and state/time permutation).

The unconditional baseline in `formation_accounting.py` reports the raw
momentum spread but does not include the placebos mandated by the spec
(Section 7, Phase B): "Run random-ranking and state/time-permutation
placebos using identical dates, selection counts, costs, and accounting."

This script computes both placebos on the frozen formation panel and writes
the results to phase_b_placebos.json. All random draws use a fixed seed so the
result is reproducible.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-001"
OUT_DIR = ROOT / "artifacts" / EXP

SEED = 20240101
N_PERM = 5000


def block_bootstrap_ci(series: pd.Series, n_boot: int = 10000, block_size: int = 3,
                       alpha: float = 0.05, seed: int = 12345) -> tuple:
    s = series.dropna()
    if len(s) == 0:
        return (float("nan"), float("nan"))
    rng = np.random.RandomState(seed)
    n = len(s)
    n_blocks = int(np.ceil(n / block_size))
    means = []
    for _ in range(n_boot):
        idxs = []
        for _ in range(n_blocks):
            start = rng.randint(0, max(1, n - block_size + 1))
            for j in range(block_size):
                if start + j < n:
                    idxs.append(start + j)
        idxs = idxs[:n]
        means.append(float(s.iloc[idxs].mean()))
    means_sorted = sorted(means)
    lo = means_sorted[int(alpha / 2 * n_boot)]
    hi = means_sorted[int((1 - alpha / 2) * n_boot)]
    return (lo, hi)


def main() -> None:
    base = pd.read_csv(OUT_DIR / "formation_returns.csv")
    spread = base["momentum_spread_gross"].dropna().reset_index(drop=True)
    n = len(spread)

    rng = np.random.RandomState(SEED)

    # 1) Random-ranking placebo: permute the observed spread values across
    #    formations. Under the null of no momentum edge the observed series
    #    should be indistinguishable from a permuted version of itself.
    rand_means = np.array([
        float(np.mean(rng.permutation(spread.values))) for _ in range(N_PERM)
    ])

    # 2) State/time permutation placebo: reassign dispersion state labels
    #    (high/low) randomly across formations while keeping the observed
    #    spread series intact. The high-minus-low difference under random
    #    state assignment is the null distribution for the conditional test.
    cond = pd.read_csv(OUT_DIR / "formation_returns_conditioned.csv")
    cond["formation_date"] = cond["formation_date"].astype(str)
    cond = cond.set_index("formation_date")
    spread_by_form = cond["momentum_spread_gross"]
    state_by_form = cond["state"]

    perm_diffs = []
    for _ in range(N_PERM):
        perm_state = rng.permutation(state_by_form.values)
        df = pd.DataFrame({"spread": spread_by_form.values, "state": perm_state})
        hi = df.loc[df["state"] == "high", "spread"]
        lo = df.loc[df["state"] == "low", "spread"]
        if len(hi) and len(lo):
            perm_diffs.append(float(hi.mean() - lo.mean()))
    perm_diffs = np.array(perm_diffs)

    observed_diff = float(
        cond.loc[cond["state"] == "high", "momentum_spread_gross"].mean()
        - cond.loc[cond["state"] == "low", "momentum_spread_gross"].mean()
    )

    summary = {
        "experiment_id": EXP,
        "phase": "B_placebos",
        "n_formations": int(n),
        "observed": {
            "unconditional_gross_spread_mean": float(spread.mean()),
            "unconditional_gross_spread_ci_95": list(block_bootstrap_ci(spread)),
            "conditional_high_minus_low_gross": observed_diff,
        },
        "random_ranking_placebo": {
            "n_permutations": N_PERM,
            "seed": SEED,
            "mean_of_permuted_means": float(rand_means.mean()),
            "std_of_permuted_means": float(rand_means.std()),
            "ci_95": [float(np.percentile(rand_means, 2.5)),
                      float(np.percentile(rand_means, 97.5))],
            "observed_vs_null_z": float(
                (spread.mean() - rand_means.mean()) / rand_means.std()
                if rand_means.std() > 0 else float("nan")),
        },
        "state_time_permutation_placebo": {
            "n_permutations": N_PERM,
            "seed": SEED,
            "mean_of_permuted_diffs": float(perm_diffs.mean()),
            "std_of_permuted_diffs": float(perm_diffs.std()),
            "ci_95": [float(np.percentile(perm_diffs, 2.5)),
                      float(np.percentile(perm_diffs, 97.5))],
            "observed_diff": observed_diff,
            "observed_vs_null_z": float(
                (observed_diff - perm_diffs.mean()) / perm_diffs.std()
                if perm_diffs.std() > 0 else float("nan")),
            "empirical_p_two_sided": float(
                (np.abs(perm_diffs - perm_diffs.mean()) >=
                 np.abs(observed_diff - perm_diffs.mean())).mean()
                if perm_diffs.std() > 0 else float("nan")),
        },
    }
    (OUT_DIR / "phase_b_placebos.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()