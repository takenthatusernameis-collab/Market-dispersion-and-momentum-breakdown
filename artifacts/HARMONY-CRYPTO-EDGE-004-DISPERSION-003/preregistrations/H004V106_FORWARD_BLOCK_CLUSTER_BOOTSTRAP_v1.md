# Preregistration — H004V106 Forward Block Formation-Month Cluster Bootstrap (DISP-003-CLUSTERBOOT-001)

**Program:** HARMONY-CRYPTO-EDGE-004
**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-CLUSTERBOOT-001
**Status:** EXPLORATORY_ONLY
**Created:** 2026-10-29T09:00:00Z
**Author:** automated research agent (this session)
**Note:** This preregistration was authored after the audit artifact was already
committed (artifact `integrity_audit/H004V106_forward_block_cluster_bootstrap_20261029.json`,
script `scripts/forward_block_cluster_bootstrap.py`, test
`tests/test_forward_block_cluster_bootstrap.py`). It is written here as the
missing record of the pre-declared decision rule so that the audit's inference
method is documented; the artifact, script and test were NOT regenerated or
altered to fit this document. The audit itself is read-only on the canonical
block and is development/exploratory evidence only.

---

## 1. Why this experiment exists (trigger)

The canonical H004V106 sealed forward block is estimated with Newey-West HAC
lagged at 29 trading days, which assumes a single time-series dependence
structure. That assumption is not verified for the cross-sectional
high-minus-low contrast, and the block is already known (H8) to be
CLUSTER_DOMINATED by the 2025-10 calendar-month cluster. This audit measures
inference under formation-month clustering explicitly: resample whole months
with replacement and recompute the high-minus-low net-1x difference.

The canonical block is already inspected development/exploratory evidence
(cutoff 2026-09-30, last formation 2026-08-31, 608 formations). It is NOT a
fresh holdout and is NOT independent confirmation. This audit cannot validate,
replace or unlock the frozen confirmatory track (H1/H6/H7), which remains
gated on a genuinely fresh sealed forward block with formations after
2026-09-29.

## 2. Question and estimand

**Question:** If formations are treated as clustered by calendar month rather
than as independent draws, what is the distribution of the high-minus-low
net-1x spread difference, and does the 95% interval exclude zero?

**Estimand:** mean(high spread_net_1x) - mean(low spread_net_1x) over the
canonical block, recomputed after resampling months with replacement.

## 3. Method (frozen before computation)

1. Load `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`
   (608 formations). Read-only.
2. Group formation indices by YYYY-MM. There are 20 calendar months in the block.
3. Compute the baseline difference over all formations.
4. For each of N_BOOT=2000 resamples, draw len(months) month indices with
   replacement (uniform), concatenate their formations, and recompute the
   difference. Discard resamples where a state is empty.
5. Report bootstrap mean, median, standard error (ddof=1), 2.5th and 97.5th
   percentiles, and whether the interval includes zero.
6. Report the number of calendar months that contain BOTH a high and a low
   formation (effective independent-cluster count).
7. RNG seed 20261029, fixed. No parameters, thresholds, assets, costs or grid
   cells are tuned. No new data are fetched. No frozen artifact is modified.

## 4. Decision rule (predeclared)

- If the month-cluster bootstrap 95% percentile CI excludes zero, label
  `CLUSTER_SIGNIFICANT` and note it as exploratory positive-direction evidence.
- Otherwise label `CLUSTER_INDIFFERENT` (CI includes zero).
- In all branches the result is `EXPLORATORY_ONLY`; no promotion to confirmatory
  status is possible from this study.

## 5. Safeguards (not relaxed)

- No look-ahead: the block is already sealed (last formation 2026-08-31,
  cutoff 2026-09-30); no truncated outcomes are computed.
- No forward-fill, no synthetic data, no paid sources, no trading.
- The canonical artifact is read-only. This study writes a new audit artifact
  under `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/`,
  a new script under `scripts/`, a new test under `tests/`, and updates the
  hypothesis registry, run manifest, frontier and handoff. Nothing in
  `forward_block/`, `grid_checkpoints/`, `grid_result_ledger.json`,
  `grid_summary.json`, DISPERSION-001 or DISPERSION-002 is touched.

## 6. Expected output

- `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/H004V106_forward_block_cluster_bootstrap_20261029.json`
- `scripts/forward_block_cluster_bootstrap.py`
- `tests/test_forward_block_cluster_bootstrap.py`
- Registry addendum for H8, manifest entry, handoff update.

## 7. Open questions for the next agent

- Only 2 of 20 calendar months contain both a high and a low formation; how much
  information is actually available at the cluster level, and is a month-level
  bootstrap well-powered here?
- Does the CI including zero change any interpretation already recorded in H8
  (CLUSTER_DOMINATED) or the temporal-stability addendum (sign not stable)?
  It should not: all are development/exploratory and none unlocks the
  confirmatory track.