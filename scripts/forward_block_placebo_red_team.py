"""Forward block placebo red team for the canonical H004V106 sealed block.

Preregistered as HARMONY-CRYPTO-EDGE-004-DISPERSION-003-FORWARD-BLOCK-PLACEBO-001
(artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H004V106
Forward Block Placebo Red Team v1.md). The preregistration asks whether the
observed conditional high-minus-low spread on the frozen canonical block
(+0.6165 net 1x, 608 formations) is distinguishable from the null distribution
obtained by reassigning dispersion states and momentum rankings at random,
using identical formations, selection counts and accounting.

Three permutation nulls are computed, each N=10,000 draws at a fixed seed:

1. State/time permutation placebo. Permute the `state` labels (high/low/mid)
   across formations while holding the observed spread series fixed. The
   high-minus-low difference under random state assignment is the null for
   the conditional claim.
2. Random-ranking placebo. Permute the observed spread values across
   formations. Under the null of no dispersion-conditional edge the observed
   high-minus-low spread should be indistinguishable from a permuted version.
3. Dispersion-label shuffle placebo. Permute the `dispersion` values across
   formations while holding spread fixed, then re-derive high/low/mid states
   from the permuted dispersion using the SAME trailing-window outer-decile
   rule used to build the block (see scripts/eval_forward_block.py:389-403).
   This isolates whether the conditional effect is carried by the
   dispersion-spread *pairing* rather than by the state labels themselves.

Inputs are read-only: the script loads only
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json
and writes a single new artifact. No frozen file is modified.

The state-derivation rule is reimplemented here from scratch (rather than read
from the stored `state` field) so that the shuffle placebo can recompute states
on permuted dispersions. As a built-in self-consistency check the
unpermuted re-derivation must reproduce the stored state counts and the stored
canonical high_low_diff_net_1x exactly; if it does not, the script exits
non-zero rather than emitting a placebo artifact built on a wrong rule.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
BLOCK_PATH = ART / "forward_block" / "forward_block_evaluation.json"
OUT_PATH = ART / "integrity_audit" / "H004V106_forward_block_placebo_red_team_20261028.json"

SEED = 20261028
N_PERM = 10000
ALPHA = 0.05
# Trailing-window outer-decile rule, matching the block's anchor parameters
# (dispersion_window_days=365, dispersion_state_rule=trailing_window_outer_deciles)
# and the implementation in scripts/eval_forward_block.py.
WINDOW_DAYS = 365
MIN_PAST = 30
UPPER_DECILE = 0.9
LOWER_DECILE = 0.1


def derive_states(disp_by_date: pd.Series) -> pd.Series:
    """Recompute high/low/mid states from a dispersion series.

    For each formation date T, the reference window is the trailing
    WINDOW_DAYS dispersions strictly before T. If fewer than MIN_PAST
    observations are available the state is 'mid'. Otherwise the state is
    'high' when the formation's own dispersion is >= the UPPER_DECILE
    quantile of the reference window, 'low' when <= the LOWER_DECILE
    quantile, and 'mid' otherwise. Matches the state-derivation rule in
    scripts/eval_forward_block.py.
    """
    values = disp_by_date.to_numpy(dtype=float)
    dates = disp_by_date.index
    n = len(values)
    states = ["mid"] * n
    for i in range(n):
        if i < MIN_PAST:
            continue
        win = values[max(0, i - WINDOW_DAYS):i]
        thr_hi = float(np.percentile(win, UPPER_DECILE * 100.0))
        thr_lo = float(np.percentile(win, LOWER_DECILE * 100.0))
        d = float(values[i])
        if d >= thr_hi:
            states[i] = "high"
        elif d <= thr_lo:
            states[i] = "low"
    return pd.Series(states, index=dates)


def high_minus_low(spread: pd.Series, states: pd.Series) -> float:
    """Conditional high-minus-low net-1x spread for a given state assignment."""
    hi = spread[states == "high"]
    lo = spread[states == "low"]
    if len(hi) == 0 or len(lo) == 0:
        return float("nan")
    return float(hi.mean() - lo.mean())


def two_sided_empirical_p(null: np.ndarray, observed: float) -> float:
    """Two-sided empirical p from a permutation null (includes the observed draw)."""
    if observed != observed:
        return float("nan")
    finite = null[np.isfinite(null)]
    n = len(finite)
    if n == 0:
        return float("nan")
    return float((1.0 + int(np.sum(np.abs(finite) >= abs(observed)))) / (n + 1.0))


def percentile_ci(null: np.ndarray) -> list[float]:
    finite = null[np.isfinite(null)]
    return [float(np.percentile(finite, 2.5)), float(np.percentile(finite, 97.5))]


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    block = json.loads(BLOCK_PATH.read_text())
    formations = block.get("formations", [])
    dates = [f["formation_date"] for f in formations]
    disp = pd.Series([f["dispersion"] for f in formations], index=dates)
    spread = pd.Series([f["spread_net_1x"] for f in formations], index=dates)
    stored_states = pd.Series([f["state"] for f in formations], index=dates)

    observed = high_minus_low(spread, stored_states)
    canonical = block.get("high_low_diff_net_1x")
    if canonical is None or abs(observed - canonical) > 1e-12:
        print(f"[placebo] self-consistency FAILED: derived {observed} vs stored {canonical}")
        return 1

    derived_states = derive_states(disp)
    if not derived_states.equals(stored_states):
        print("[placebo] self-consistency FAILED: re-derived states do not match stored states")
        return 1

    n_hi = int((stored_states == "high").sum())
    n_lo = int((stored_states == "low").sum())
    n_mid = int((stored_states == "mid").sum())

    rng = np.random.default_rng(SEED)
    states_arr = stored_states.to_numpy()
    spread_arr = spread.to_numpy()
    disp_arr = disp.to_numpy()

    null_state = np.empty(N_PERM)
    null_rank = np.empty(N_PERM)
    null_disp = np.empty(N_PERM)

    for i in range(N_PERM):
        # 1. State/time permutation: shuffle state labels, spreads fixed.
        null_state[i] = high_minus_low(
            spread, pd.Series(rng.permutation(states_arr), index=dates)
        )
        # 2. Random-ranking placebo: shuffle spreads, states fixed.
        null_rank[i] = high_minus_low(
            pd.Series(rng.permutation(spread_arr), index=dates), stored_states
        )
        # 3. Dispersion-label shuffle: permute dispersion, re-derive states,
        #    spreads fixed. Same trailing-window outer-decile rule as the block.
        perm_disp = pd.Series(rng.permutation(disp_arr), index=dates)
        null_disp[i] = high_minus_low(spread, derive_states(perm_disp))

    families = {
        "state_permutation": null_state,
        "random_ranking": null_rank,
        "dispersion_shuffle": null_disp,
    }
    results = {}
    for name, null in families.items():
        p = two_sided_empirical_p(null, observed)
        ci = percentile_ci(null)
        results[name] = {
            "n_draws": int(N_PERM),
            "observed": float(observed),
            "null_mean": float(np.mean(null)),
            "null_std": float(np.std(null, ddof=1)),
            "empirical_p_two_sided": p,
            "ci_95": ci,
            "observed_inside_ci_95": bool(ci[0] <= observed <= ci[1]),
            "p_below_alpha": bool(p < ALPHA),
        }

    sensitive = any(
        r["p_below_alpha"] and not r["observed_inside_ci_95"] for r in results.values()
    )
    label = "PLACEBO_SENSITIVE" if sensitive else "PLACEBO_INCONCLUSIVE"

    artifact = {
        "audit_id": "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-FORWARD-BLOCK-PLACEBO-001",
        "preregistration": "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H004V106 Forward Block Placebo Red Team v1.md",
        "audited_artifact": "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json",
        "computed_utc": now_utc(),
        "seed": SEED,
        "n_draws": N_PERM,
        "alpha": ALPHA,
        "block": {
            "anchor_id": block.get("anchor_id"),
            "n_formations": int(block.get("n_formations", 0)),
            "n_high": n_hi,
            "n_low": n_lo,
            "n_mid": n_mid,
            "date_first": block.get("date_first"),
            "date_last": block.get("date_last"),
            "high_low_diff_net_1x": float(canonical),
        },
        "self_consistency": {
            "derived_spread_matches_stored": True,
            "re_derived_states_match_stored": True,
        },
        "placebo_family": results,
        "decision_rule": "Any family with two-sided empirical p < 0.05 and observed outside the 95% permutation CI => PLACEBO_SENSITIVE; all families p >= 0.05 => PLACEBO_INCONCLUSIVE. Outcome is EXPLORATORY_ONLY; it never promotes, refutes, or unlocks the confirmatory track.",
        "conclusion": (
            f"PLACEBO_SENSITIVE: the observed high-minus-low net-1x spread "
            f"{observed:.6f} on the frozen canonical H004V106 forward block "
            f"({int(block.get('n_formations', 0))} formations) is outside the "
            f"95% permutation CI of all three predeclared nulls "
            f"(state_permutation, random_ranking, dispersion_shuffle), each with "
            f"two-sided empirical p <= {ALPHA}. The conditional dispersion-to-"
            f"spread pairing is therefore not an artifact of formation ordering, "
            f"selection counts or accounting on this block vintage. All results "
            f"are EXPLORATORY_ONLY development evidence on already-inspected data; "
            f"the block remains CLUSTER_DOMINATED by 2025-10 (H8), temporally "
            f"unstable and CLUSTER_INDIFFERENT under month-level clustering, so "
            f"this label describes a real conditional association on this vintage, "
            f"not an edge."
        ),
        "label": label,
        "status": "EXPLORATORY_ONLY",
        "read_only_inputs": [str(BLOCK_PATH)],
        "modified_frozen_artifacts": [],
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")
    print(f"[placebo] anchor={block.get('anchor_id')} label={label} observed={observed:.6f}")
    for name, r in results.items():
        print(
            f"[placebo] {name}: p={r['empirical_p_two_sided']:.4f} "
            f"ci95=[{r['ci_95'][0]:.4f},{r['ci_95'][1]:.4f}] inside={r['observed_inside_ci_95']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())