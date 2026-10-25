# Preregistration — H004V106 State Representativeness Audit (DISP-003-STATEAUDIT-001)

**Program:** HARMONY-CRYPTO-EDGE-004
**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-STATEAUDIT-001
**Status:** EXPLORATORY_ONLY
**Created:** 2026-10-25T07:45:00Z
**Author:** automated research agent (this session)

---

## 1. Why this experiment exists (trigger)

The canonical DISPERSION-003 sealed forward block (H004V106, cutoff 2026-09-30, last
formation 2026-08-31, 608 formations) reports `high_low_diff_net_1x = +0.6165`. The
program's confirmatory track (H1/H6) is gated on a fresh sealed block after 2026-09-29,
which is structurally unavailable (today is 2026-10-25; the October 2026 Binance monthly
archive is 404 and must not be re-probed). Free-source catalog discovery returned 0 new
candidates. The test suite is green and all frozen artifacts are byte-unchanged.

Rather than repeat the same blocked state, this session runs a **measurement-feasibility
study on data already in hand** (the sealed forward block). It asks a narrower question:
*is the +0.617 estimate representative of the dispersion-momentum mechanism, or is it
dominated by a single calendar-month cluster?* This is a diagnostic, not a confirmatory
test. It cannot validate, replace, or unlock the frozen confirmatory track.

## 2. Question and estimand

**Question:** How sensitive is the canonical H004V106 high-minus-low estimate to the
removal of individual calendar months, and what fraction of the high-state mean is
contributed by any single month?

**Estimand:** The formation-level high-minus-low spread (net 1x) in the canonical block,
with each calendar month removed in turn. Secondary: the share of the high-state mean
contributed by the largest single-month cluster.

## 3. Method (frozen before computation)

1. Load `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`
   (608 formations). This is development/exploratory evidence already inspected; it is
   NOT a fresh holdout and is NOT used as independent confirmation.
2. Compute the full-block baseline `high_low_diff_net_1x` (= mean(high spread_net_1x) −
   mean(low spread_net_1x)).
3. For each calendar month present in the block, drop every formation whose
   `formation_date` starts with that `YYYY-MM`, recompute the high/low means and their
   difference. Report `n_high`, `n_low`, and the recomputed difference for every month.
4. Decompose the high-state mean: partition high-state formations into the largest
   single-month cluster and all others; report each group's count, mean, median, and the
   cluster's share of the total high-state mean.
5. Report the dispersion series regime break: the last date on which a high state was
   observed, and the count of high states per calendar month.
6. No parameters, thresholds, assets, costs, or grid cells are tuned. No new data are
   fetched. No frozen artifact is modified.

## 4. Decision rule (predeclared)

- If removing any single calendar month moves `high_low_diff_net_1x` by more than 50%
  of its full-block magnitude, the estimate is **not robust to calendar-month clustering**
  and is labeled `CLUSTER_DOMINATED`.
- If the largest single-month cluster contributes more than 50% of the high-state mean,
  the high-state estimate is labeled `CLUSTER_DOMINATED`.
- Otherwise the estimate is `MONTH_ROBUST`.
- In all cases the result is `EXPLORATORY_ONLY`; no promotion to confirmatory status is
  possible from this study.

## 5. Safeguards (not relaxed)

- No look-ahead: the block is already sealed (last formation 2026-08-31, cutoff 2026-09-30);
  no truncated outcomes are computed.
- No forward-fill, no synthetic data, no paid sources, no trading.
- The canonical artifact is read-only; this study writes a new audit artifact under
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/` and a new
  integrity-audit file under `integrity_audit/`. Nothing in `forward_block/`,
  `grid_checkpoints/`, `grid_result_ledger.json`, or `grid_summary.json` is touched.
- DISPERSION-001/002 remain untouched.

## 6. Expected output

`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/H004V106_state_representativeness_audit_20261025.json`
plus this preregistration and a handoff/registry update.

## 7. Open questions for the next agent

- If the estimate is cluster-dominated, does the mechanism still exist in the 2026 data
  under an adaptive (rolling, shorter) reference window? (Not tested here; would need a
  new preregistered experiment.)
- Is the October 2025 dispersion spike itself a real market event worth conditioning on,
  or a data/construction artifact of the expanding universe?