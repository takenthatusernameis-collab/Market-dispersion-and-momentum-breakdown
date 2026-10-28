# Preregistration — H004V106 Forward Block Placebo Red Team v1

**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-FORWARD-BLOCK-PLACEBO-001
**Preregistered:** 2026-10-28T17:30:00Z
**Status:** EXPLORATORY_ONLY
**Track:** Exploratory (confirmatory track untouched; H004V106 forward block remains frozen and already-inspected)

## 1. Purpose

The canonical H004V106 sealed forward block reports a positive high-minus-low
dispersion-momentum spread of +0.6165 (net 1x, 608 formations) that is not
statistically significant under Newey-West HAC (t~1.55, CI [-0.164, 1.397]).
The state-representativeness audit (H8) showed this estimate is
cluster-dominated by calendar month 2025-10.

This preregistration specifies a **placebo red-team** on the same frozen block:
it asks whether the observed conditional high-minus-low spread is
distinguishable from the null distribution obtained by reassigning dispersion
states and momentum rankings at random, using identical formations, selection
counts and accounting. It does **not** compute new forward outcomes, does **not**
open the holdout, and does **not** alter any frozen artifact.

## 2. Inputs (read-only)

- `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`
  (canonical sealed block; 608 formations; state, dispersion, spread_gross, spread_net_1x).
- No price panels, no market-cap panels, no funding panels, no network access.
- No DISPERSION-001 or DISPRESSION-002 files touched.

## 3. Placebo family (complete, predeclared)

Three permutation nulls, each with N=10,000 draws at a fixed seed:

1. **State/time permutation placebo.** Permute the `state` labels (high/low/mid)
   across formations while holding the observed spread series fixed. The
   high-minus-low difference under random state assignment is the null for the
   conditional claim. Two-sided empirical p and 95% CI from the permutation
   distribution.
2. **Random-ranking placebo.** Permute the observed spread values across
   formations. Under the null of no dispersion-conditional edge, the observed
   high-minus-low spread should be indistinguishable from a permuted version.
3. **Dispersion-label shuffle placebo.** Permute the `dispersion` values across
   formations while holding spread and state fixed, then re-derive high/low
   states from the permuted dispersion using the same trailing-window outer-decile
   rule. This isolates whether the conditional effect is carried by the
   dispersion-spread *pairing* rather than by the state labels themselves.

All three are reported. No one-sided test is chosen after seeing outcomes.

## 4. Decision rule (predeclared)

- If **any** placebo family yields an empirical two-sided p < 0.05 (with the
  observed statistic outside the 95% permutation CI), label the conditional
  result `PLACEBO_SENSITIVE` and conclude the observed +0.617 is not robust to
  random reassignment.
- If **all** families yield p >= 0.05 (observed inside all CIs), label
  `PLACEBO_INCONCLUSIVE` — the block is too small or too cluster-dominated for
  the permutation null to separate signal from noise.
- In no case does a placebo result promote, refute, or unlock the confirmatory
  track. Outcome is `EXPLORATORY_ONLY`.

## 5. safeguards

- Fixed seed; deterministic; reproducible.
- Read-only on all frozen artifacts; byte-diff verified after the run.
- No look-ahead: the block is already sealed (last formation 2026-08-31,
  cutoff 2026-09-30); permutation is over already-completed formations only.
- No forward-fill, no fabricated fills, no truncated outcomes, no cost tuning.
- No new sealed forward block is created; this is a measurement/diagnostic only.

## 6. Output

`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/H004V106_forward_block_placebo_red_team_20261028.json`
plus a regression test in `tests/test_forward_block_placebo_red_team.py`.

## 7. Change log

- v1 (2026-10-28): initial preregistration before any computation.