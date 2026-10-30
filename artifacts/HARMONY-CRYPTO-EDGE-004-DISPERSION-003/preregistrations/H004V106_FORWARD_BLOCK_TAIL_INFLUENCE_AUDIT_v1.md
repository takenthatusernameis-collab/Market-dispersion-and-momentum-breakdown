# Preregistration — H004V106 Forward Block Tail Influence Audit (DISP-003-TAILAUDIT-001)

**Program:** HARMONY-CRYPTO-EDGE-004
**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-TAILAUDIT-001
**Status:** EXPLORATORY_ONLY
**Created:** 2026-10-28T23:30:00Z (see correction note below)
**Author:** automated research agent (this session)
**Correction note (2026-10-30T17:15Z):** The declared `Created` time
(2026-10-28T23:30:00Z) precedes both the audit artifact it describes
(computed 2026-10-29T06:07:05Z) and the document's commit time
(commit 3d58d80, 2026-10-28T23:33:54Z). This is a **prospective**
preregistration authored before the audit ran, not a backdating: the
declared time is retained as written and is not claimed to be a
retroactive correction. The commit time is the earliest verifiable
repository timestamp. The audit artifact, script
(`scripts/forward_block_tail_influence.py`) and test
(`tests/test_forward_block_tail_influence.py`) were NOT regenerated or
altered to fit this document, and the audit's decision rule is unchanged.

---

## 1. Why this experiment exists (trigger)

The repository operating contract (AGENTS.md line 58) requires that the canonical
H004V106 forward block be audited for "reconciliation, finite-value checks, state
counts, mean/median, tail influence, cost treatment, overlap-aware uncertainty and
independent metric recomputation" before it may be treated as a winner.

Prior sessions completed reconciliation, finite-value checks, state counts,
mean/median, cost treatment, overlap-aware uncertainty (HAC addendum) and
independent recomputation. **Tail influence was not previously computed.** This
session closes that gap.

The canonical block is already inspected development/exploratory evidence
(cutoff 2026-09-30, last formation 2026-08-31, 608 formations). It is NOT a fresh
holdout and is NOT independent confirmation. This audit cannot validate, replace
or unlock the frozen confirmatory track (H1/H6/H7), which remains gated on a
genuinely fresh sealed forward block with formations after 2026-09-29.

## 2. Question and estimand

**Question:** How much of the canonical +0.617 high-minus-low estimate is carried by
the extreme tails of the formation-level spread distribution, and how sensitive is
the estimate to the removal of single formations?

**Estimand:** The formation-level high-minus-low spread (net 1x) in the canonical
block, under (a) no trimming, (b) symmetric trimming, (c) symmetric winsorization,
and (d) single-formation leave-one-out. The high and low state series are treated
separately because they have different sample sizes (61 vs 90) and different
skewness.

## 3. Method (frozen before computation)

1. Load `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`
   (608 formations). Read-only.
2. Partition formations by `state` into high (n=61) and low (n=90). Compute per-state
   count, mean, median, min, max, and Fisher-Pearley standardized skewness.
3. **Trimming:** for k in {0, 1, 2, 3}, drop the k smallest and k largest of each state
   series and recompute mean(high) - mean(low). Report the difference and its ratio to
   the full-block baseline.
4. **Winsorization:** for p in {0.05, 0.10}, clip each state series to its
   [p, 1-p] quantile and recompute the difference and its ratio to baseline.
5. **Single-formation leave-one-out:** for each formation in turn, remove it and
   recompute the difference. Report the maximum absolute delta and its ratio to
   baseline, separately for high-state and low-state removals, and identify the
   extreme formation responsible.
6. **Tail concentration:** report the share of the high-state mean contributed by the
   top 1, top 5 and top 10% of high-state formations (by spread magnitude), and the
   analogous bottom-tail share for the low state.
7. No parameters, thresholds, assets, costs or grid cells are tuned. No new data are
   fetched. No frozen artifact is modified.

## 4. Decision rule (predeclared)

- If symmetric trimming of any 3 formations from each state moves the difference by
  more than 20% of baseline, label `TAIL_SENSITIVE`.
- If 10% winsorization moves the difference by more than 20% of baseline, label
  `TAIL_SENSITIVE`.
- If any single-formation leave-one-out moves the difference by more than 10% of
  baseline, label `TAIL_SENSITIVE`.
- Otherwise label `TAIL_ROBUST`.
- In all branches the result is `EXPLORATORY_ONLY`; no promotion to confirmatory
  status is possible from this study.

## 5. Safeguards (not relaxed)

- No look-ahead: the block is already sealed (last formation 2026-08-31, cutoff
  2026-09-30); no truncated outcomes are computed.
- No forward-fill, no synthetic data, no paid sources, no trading.
- The canonical artifact is read-only. This study writes a new audit artifact under
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/`, a new script
  under `scripts/`, a new test under `tests/`, and updates the hypothesis registry,
  run manifest, frontier and handoff. Nothing in `forward_block/`,
  `grid_checkpoints/`, `grid_result_ledger.json`, `grid_summary.json`,
  DISPERSION-001 or DISPERSION-002 is touched.

## 6. Expected output

- `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/H004V106_forward_block_tail_influence_20261028.json`
- `scripts/forward_block_tail_influence.py`
- `tests/test_forward_block_tail_influence.py`
- Registry addendum for H7/H8, manifest entry, handoff update.

## 7. Open questions for the next agent

- If the high state is right-skewed with a heavy upper tail, is the +0.617 mean
  driven by a small number of large positive outliers rather than a systematic
  high-state shift? Would a median-based or winsorized estimator change the
  conclusion?
- Does the tail concentration interact with the 2025-10 cluster dominance already
  recorded in H8?