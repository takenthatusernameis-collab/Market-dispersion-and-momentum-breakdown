# Preregistration — F1 Coverage-Outcome Sensitivity (DISP-003-F1SENS-002)

**Program:** HARMONY-CRYPTO-EDGE-004
**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1SENS-002
**Hypothesis (registry):** H24
**Status:** EXPLORATORY_ONLY
**Created:** 2026-11-13T02:58:57Z
**Author:** automated research agent (this session)

## 1. Why this experiment exists (trigger)

`DISP-003-F1COVERAGE-001` (H23) re-acquired the four symbols missing from the
committed DISPERSION-003 Binance archive for 2025-01..2026-09
(`1INCHUSDT`, `AAVEUSDT`, `ACHUSDT`, `AGLDUSDT`) and rebuilt their panels into a
new experiment directory. That repair raised the descriptive eligible-asset
count on the canonical H004V106 block formation dates from **26-27 to 29-31**
(mean 26.23 -> 30.08, dates_increased=638, dates_decreased=0), and the F1
preregistration's own `next_test` states:

> "Any future confirmatory use of the repaired panels requires a new ID, a new
> preregistration and new artifact paths."

The frozen canonical H004V106 forward block (`forward_block/forward_block_evaluation.json`,
cutoff 2026-09-30, 608 formations, `high_low_diff_net_1x = +0.6165223953929935`)
was estimated on **26-27 assets** — the very coverage limitation the F1 repair
exists to address. **No committed artifact yet measures whether the anchor's
outcome changes when the four repaired assets are added.** This experiment
supplies that missing measurement under a new ID, new preregistration and new
artifact paths, exactly as H23's `next_test` requires.

The H10 fresh sealed forward block remains calendar-gated to the November 2026
data vintage (not before 2026-11-30) and re-probing November before that date is
prohibited, so this is a bounded, no-cost, on-disk task that advances the
program without touching any frozen artifact.

## 2. Estimand (descriptive sensitivity — NOT a confirmation)

The estimand is the **anchor H004V106 formation outcome under two eligible
universes**, evaluated over the identical sealed canonical formation window
(2025-01-01 .. 2026-08-31, data cutoff 2026-09-30), using the identical frozen
anchor parameters, cost model and state rule:

- **Arm A (committed):** the 32-symbol committed panels exactly as the frozen
  canonical block was computed (26-27 eligible assets per date).
- **Arm B (repaired):** the committed panels with the four F1-repaired kline
  panels overriding `1INCHUSDT`, `AAVEUSDT`, `ACHUSDT`, `AGLDUSDT`
  (29-31 eligible assets per date).

For each arm the script reports: `n_formations`, `n_high`, `n_low`, `n_mid`,
`high_low_diff_net_1x`, `spread_net_1x_mean`, `spread_net_1x_median`, the
formation-month cluster-bootstrap interval, and the eligible-asset distribution.
The primary descriptive contrast is `high_low_diff_net_1x(arm B) - high_low_diff_net_1x(arm A)`.

This is **EXPLORATORY_ONLY** descriptive evidence. It is computed on the already
inspected development window (the canonical block is a strict subset of the grid
ledger's development window and has been inspected for many sessions). It does
**not** validate, replace, unlock or re-run any frozen experiment, does not open
any sealed holdout, and cannot promote H1/H6/H7/H8/H9/H10/H11 or any other
hypothesis. It is not a fresh holdout and not independent confirmation.

## 3. Method (frozen before any computation)

1. **Fidelity check (mandatory first step).** Import the unmodified functions
   from `scripts/eval_forward_block.py` (`load_marketcap`, `load_binance_panel`,
   `build_price_wide_all`, `MomentumCache`, `build_eligibility_map`,
   `compute_dispersion`, `portfolio_spread`, `forward_returns`,
   `overlap_aware_interval`) and reproduce the frozen canonical block from the
   **committed panels only**. Assert the reproduced `n_formations`,
   `n_high`, `n_low`, `high_low_diff_net_1x`, `spread_net_1x_mean`,
   `spread_net_1x_median`, `date_first`, `date_last` match the committed
   `forward_block_evaluation.json` to within 1e-9 (absolute). If this fails,
   the script aborts with status `FIDELITY_FAILED` and writes no comparison.
2. **Arm A** = the fidelity reproduction above (committed panels).
3. **Arm B** = the same computation with the four repaired kline panels
   (from `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001/data/panels/binance_klines_<SYM>.csv`)
   substituted for the four symbols, all else identical (same anchor params,
   same cost `COST_1X = 0.001`, same 365-trailing-decile state rule, same
   `MIN_ASSETS_DECILES = 20`, same 30-day forward horizon, same 2025-01-01
   block start, same 2026-09-30 cutoff).
4. Emit a single artifact
   `integrity_audit/f1_coverage_outcome_sensitivity_<UTC>.json` recording: the
   fidelity check, both arms' full formation records and summary statistics, the
   per-date eligible-asset distribution for each arm, the primary contrast, and
   explicit verification that the committed panels, raw zips, canonical block
   and H10 fresh block are byte-unchanged.

## 4. Decision rule (predeclared)

- **PASS** if the fidelity check reproduces the committed canonical block
  exactly (all listed fields within 1e-9), both arms compute with no error, and
  every committed input and frozen artifact hash is unchanged.
- **FAIL** if the fidelity check does not reproduce the committed block, if
  either arm cannot be computed, or if any committed input or frozen artifact
  changes.

In all branches the result is EXPLORATORY_ONLY. It cannot promote any hypothesis
and does not re-open the sealed canonical block.

## 5. Safeguards (never relaxed)

- No overwriting of `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/` or
  any frozen artifact; new ID and new paths only.
- Free public data only; **no network** in this experiment (reuses the already
  fetched F1 zips/panels on disk); no credentials, no secrets, no trading.
- No look-ahead, no forward-fill, no synthetic rows, no silent exclusions, no
  fabricated fills. Same 30-day maturity rule; no truncated outcomes.
- Point-in-time cap only: today's rank is never backfilled as historical rank.
- The canonical block and the H10 fresh block are read-only inputs and are
  byte-verified unchanged at the end of the run.
- This is a sensitivity measurement, not a hypothesis test; no p-value, no
  multiple-testing family, no promotion.

## 6. Expected output

- `scripts/f1_coverage_outcome_sensitivity.py` (new, imports the unmodified
  evaluator for fidelity).
- `integrity_audit/f1_coverage_outcome_sensitivity_<UTC>.json` with both arms,
  the fidelity check, the contrast and the read-only checks.
- `tests/test_f1_coverage_outcome_sensitivity.py` regression guard.
- Registry entry H24 (next_sequence_number 23 -> 24); handoff and task-message
  update.

## 7. Change log

- 2026-11-13T02:58:57Z — created before any computation. No grid, hypothesis
  conclusion, cost model, parameter, panel or frozen artifact changed.