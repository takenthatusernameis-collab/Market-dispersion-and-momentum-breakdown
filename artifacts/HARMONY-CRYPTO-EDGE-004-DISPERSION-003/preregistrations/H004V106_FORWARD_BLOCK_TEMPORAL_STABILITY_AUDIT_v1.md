# Preregistration — H004V106 Forward Block Temporal Stability Audit (DISP-003-TEMPSTABILITY-001)

**Program:** HARMONY-CRYPTO-EDGE-004
**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-TEMPSTABILITY-001
**Status:** EXPLORATORY_ONLY
**Created:** 2026-10-30T16:35:00Z
**Author:** automated research agent (this session)

---

## 1. Why this experiment exists (trigger)

The repository operating contract (AGENTS.md) requires that the canonical
H004V106 forward block be audited for "reconciliation, finite-value checks,
state counts, mean/median, tail influence, cost treatment, overlap-aware
uncertainty and independent metric recomputation" before it may be treated as a
winner. Prior sessions completed all of those components **except temporal
stability**: the audit artifact
`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/H004V106_forward_block_temporal_stability_20261029.json`
and its script `scripts/forward_block_temporal_stability.py` were committed
without a preregistration document, so the durable state was internally
inconsistent (an audit existed with no pre-declared method). This session closes
that gap by writing the missing preregistration **before** re-running the
script, so the document is now genuinely prospective.

The canonical block is already inspected development/exploratory evidence
(cutoff 2026-09-30, last formation 2026-08-31, 608 formations). It is NOT a fresh
holdout and is NOT independent confirmation. This audit cannot validate, replace
or unlock the frozen confirmatory track (H1/H6/H7), which remains gated on a
genuinely fresh sealed forward block with formations after 2026-09-29.

## 2. Question and estimand

**Question:** Is the canonical +0.617 high-minus-low net-1x spread difference a
stable property of the block across its own history, or does it depend on which
part of the block is observed?

**Estimand:** mean(high spread_net_1x) - mean(low spread_net_1x) over the
canonical block, recomputed separately on the first half and second half of the
formation series ordered by formation date, with formation-month cluster
bootstrap SE/CI for each half.

## 3. Method (frozen before computation)

1. Load `artifacts/HARMONY-CRYPTO-EDGE-004-DISPRESSION-003/forward_block/forward_block_evaluation.json`
   (608 formations). Read-only.
2. Sort formations by `formation_date`. Split at the median formation date
   (`len // 2` = 304 formations per half; split date 2025-11-01).
3. For each half compute: n_formations, n_high, n_low, n_mid,
   high_low_diff_net_1x, spread_net_1x_median, date_first, date_last,
   n_months, n_months_with_both_states, and a formation-month cluster bootstrap
   (N_BOOT=2000, RNG seed 20261029) giving mean, SE, 2.5/97.5 percentile CI and
   whether the CI includes zero.
4. Report the full-block baseline difference for reference.
5. No parameters, thresholds, assets, costs or grid cells are tuned. No new data
   are fetched. No frozen artifact is modified.

## 4. Decision rule (predeclared)

- If the two halves have the same sign and overlapping 95% CIs, label
  `TEMPORALLY_STABLE`.
- If the two halves have different signs, or non-overlapping CIs, label
  `TEMPORALLY_UNSTABLE` / `sign not temporally stable`.
- In all branches the result is `EXPLORATORY_ONLY`; no promotion to confirmatory
  status is possible from this study.

## 5. Safeguards (not relaxed)

- No look-ahead: the block is already sealed (last formation 2026-08-31, cutoff
  2026-09-30); no truncated outcomes are computed.
- No forward-fill, no synthetic data, no paid sources, no trading.
- The canonical artifact is read-only. This study writes a new audit artifact
  under `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/`, a
  new script under `scripts/`, a new test under `tests/`, and updates the
  hypothesis registry, run manifest, frontier and handoff. Nothing in
  `forward_block/`, `grid_checkpoints/`, `grid_result_ledger.json`,
  `grid_summary.json`, DISPERSION-001 or DISPERSION-002 is touched.

## 6. Expected output

- `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/H004V106_forward_block_temporal_stability_20261029.json`
- `scripts/forward_block_temporal_stability.py`
- `tests/test_forward_block_temporal_stability.py`
- Registry addendum for H8, manifest entry, handoff update.

## 7. Open questions for the next agent

- The temporal-stability split is a median split of the formation series, not a
  causal split: formations in the second half are also those closer to the
  cutoff, so a half-level difference could reflect either a time trend or the
  sparseness of high states after 2025-10 (H8). Which interpretation is more
  plausible?
- Does the temporal instability interact with the cluster-bootstrap finding
  (DISP-003-CLUSTERBOOT-001, CI includes zero)? Both point to the same conclusion
  - that the +0.617 estimate is not robust - but they use different uncertainty
  models. Are they mutually reinforcing or partially redundant?