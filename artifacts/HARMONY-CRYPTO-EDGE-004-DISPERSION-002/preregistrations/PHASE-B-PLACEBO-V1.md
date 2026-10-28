# Preregistration — Phase B Placebo Red-Team on DISPERSION-002

**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-002-PHASE-B-PLACEBO
**Preregistered:** 2026-10-28T23:35Z
**Status:** EXPLORATORY_ONLY (development evidence on frozen data)

## Purpose
DISPENSITY-001 received a Phase B placebo red-team (random-ranking and
state/time permutation placebos, artifact `phase_b_placebos.json`). DISPENSITY-002
is an immutable closed record with an identical conditioned formation panel
(`formation_returns_conditioned.csv`, 53 formations, anchor H004F033) but the
symmetric red-team was never executed. This preregistration closes that gap.

## Data and scope
- **Inputs (frozen, read-only):** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/formation_returns_conditioned.csv`
- **Output (new artifact only):** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPENSITY-002/phase_b_placebos.json`
- No existing DISPENSITY-002 file is modified. DISPENSITY-001/002 findings unchanged.

## Placebo 1 — Random-ranking
Permute the observed `momentum_spread_gross` values across formations (N=5000,
seed 20240101). Under the null of no momentum edge the observed unconditional
mean should be indistinguishable from the permuted distribution. Report mean,
std, 95% percentile CI and observed-vs-null z.

## Placebo 2 — State/time permutation
Randomly reassign the `state` labels (high/low) across formations while keeping
the observed spread series intact (N=5000, seed 20240101). The high-minus-low
difference under random state assignment is the null distribution for the
conditional test. Report mean, std, 95% CI, observed diff, z and two-sided
empirical p.

## Decision rule
- If the observed conditional high-minus-low diff (+0.1747 gross) lies outside
  the state/time permutation 95% CI, the conditional edge survives the
  permutation null **descriptively**. This is development evidence only.
- If it lies inside, record `CONDITIONAL_EDGE_NOT_DISTINGUISHABLE_FROM_RANDOM`.
- Either way the result is **EXPLORATORY_ONLY** and cannot validate, refute or
  unlock any frozen hypothesis. Promotion requires a fresh sealed forward block.

## Constraints honored
Free public data only, historical-only, point-in-time, no forward-fill, no
trading, no secrets. Block-bootstrap parameters (block size 3, 10000 reps, seed
12345) match the DISPENSITY-001 red-team for comparability.