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
    WINDOW_DAYS dispersions strictly before T (dser.loc[:T].iloc[:-1].
    tail(WINDOW_DAYS)). If fewer than MIN_PAST observations are available the
    state is 'mid'. Otherwise the state is 'high' when the formation's own
    dispersion is >= the UPPER_DECILE quantile of the reference window, 'low'
    when <= the LOWER_DECILE quantile, and 'mid' otherwise.
    """
    states = {}
    for T in disp_by_date.index:
        past = disp_by_date.loc[:T].iloc[:-1].tail(WINDOW_DAYS)
        if len(past) < MIN_PAST:
            states[T] = "mid"
            continue
        thr_hi = float(past.quantile(UPPER_DECILE))
        thr_lo = float(past.quantile(LOWER_DECILE))
        d = float(disp_by_date.loc[T])
        if d >= thr_hi:
            states[T] = "high"
        elif d <= thr_lo:
            states[T] = "low"
        else