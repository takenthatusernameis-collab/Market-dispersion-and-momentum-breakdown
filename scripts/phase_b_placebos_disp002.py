"""Phase B placebos (random-ranking and state/time permutation) for DISPERSION-002.

DISPERSION-002 is an immutable closed record (AGENTS.md: "Preserve
DISPERSION-001/002 configs, inputs, artifacts and findings"). This script is
read-only on its frozen inputs: it loads artifacts/HARMONY-CRYPTO-EDGE-004-
DISPERSION-002/formation_returns_conditioned.csv and writes a single new
artifact artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/phase_b_placebos.json.
No existing DISPERSION-002 file is modified.

The protocol mirrors scripts/phase_b_placebos.py (DISPERSION-001) exactly:
identical seeds, permutation counts, block-bootstrap parameters and summary
schema, so the two experiments are comparable. The DISPERSION-001 red-team
artifact already exists; this closes the symmetric gap on the frozen
DISPERSION-002 conditioned panel.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-002"
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
    panel_path = OUT_DIR / "formation_returns_conditioned.csv"
    if not panel_path.exists():
        raise SystemExit(f"missing frozen input panel: {panel_path}")

    cond = pd.read_csv(panel_path)
    cond["formation_date"] = cond["formation_date"].astype(str)
    n = int(len(cond))

    spread_by_form = cond["momentum_spread_gross"]
    state_by_form = cond["state"]

    rng = np.random.RandomState(SEED)

    # 1) Random-ranking placebo: permute the observed spread values across
    #    formations. Under the null of no momentum edge the observed series
    #    should be indistinguishable from a permuted version of itself.
    rand_means = np.array([
        float(np.mean(rng.permutation(spread_by_form.values))) for _ in range(N_PERM)
    ])

    # 2) State/time permutation placebo: reassign dispersion state labels
    #    (high/low) randomly across formations while keeping the observed
    #    spread series intact. The high-minus-low difference under random
    #    state assignment is the null distribution for the conditional test.
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
        "n_formations": n,
        "observed": {
            "unconditional_gross_spread_mean": float(spread_by_form.mean()),
            "unconditional_gross_spread_ci_95": list(block_bootstrap_ci(spread_by_form)),
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
                (spread_by_form.mean() - rand_means.mean()) / rand_means.std()
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
    out_path = OUT_DIR / "phase_b_placebos.json"
    out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()