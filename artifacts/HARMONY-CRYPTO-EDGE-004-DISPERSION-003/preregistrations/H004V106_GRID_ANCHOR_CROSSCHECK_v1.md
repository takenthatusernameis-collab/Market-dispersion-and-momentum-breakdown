# H004V106 Grid Anchor Cross-Check Preregistration

**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-GRID-ANCHOR-CROSSCHECK-001
**Preregistered:** 2026-11-15T04:00:00Z
**Status:** PREREGISTERED_BEFORE_COMPUTATION

## Objective

Cross-check the H004V106 anchor configuration across three committed DISPERSION-003 grid artifacts to verify internal consistency of the full grid evaluation window (2023-01-31 to 2026-09-29, 1338 formations).

## Artifacts to Audit

1. **grid_summary.json** - `primary_anchor_expanding_H004V106` object containing the anchor's formation records and summary statistics
2. **grid_checkpoints/cell_checkpoint.json** - `H004V106` entry containing the same anchor's formation records and summary statistics
3. **grid_result_ledger.json** - `cells.H004V106` entry containing the same anchor's formation records and summary statistics

## Pre-declared Checks

### Formation-Level Consistency
- All three artifacts contain exactly 1338 formations for H004V106
- Formation dates match exactly across all three artifacts (same dates, same order)
- For each formation: dispersion, n_assets, spread_gross, spread_net_1x, state match within 1e-12 tolerance
- No formation is missing or extra in any artifact

### Summary Statistics Consistency
- n_formations: identical across all three (expected 1338)
- n_high, n_low, n_mid: identical across all three
- date_first: "2023-01-31" in all three
- date_last: "2026-09-29" in all three
- high_low_diff_net_1x: identical across all three within 1e-12
- high_low_diff_gross: identical across all three within 1e-12
- spread_net_1x_mean, spread_net_1x_median: identical within 1e-12
- spread_gross_mean, spread_gross_median: identical within 1e-12
- high_net_1x_mean, low_net_1x_mean, high_gross_mean, low_gross_mean: identical within 1e-12
- status: "OK" in cell_checkpoint and grid_result_ledger

### Data Integrity
- All dispersion values are finite (no NaN, inf)
- All spread_gross and spread_net_1x values are finite
- No duplicate formation dates within each artifact
- Formation dates are strictly increasing

## Methodology

1. Load all three artifacts from disk
2. Extract H004V106 data from each
3. Perform pairwise comparisons (grid_summary ↔ cell_checkpoint, grid_summary ↔ grid_result_ledger, cell_checkpoint ↔ grid_result_ledger)
4. Record all matches/mismatches with specific formation indices where differences occur
5. Produce a single audit artifact with PASS/FAIL conclusion

## Decision Rules

- **PASS**: All pre-declared checks pass (all formation records match within tolerance, all summary statistics match within tolerance, all data integrity checks pass)
- **FAIL**: Any pre-declared check fails; specific failures are reported with formation indices and field names

## Scope

This audit is **read-only** and **additive**: it produces a new integrity audit artifact under `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/`. No existing artifact, config, input, frontier, registry, or sealed holdout is modified.

## Output Artifact

`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/H004V106_grid_anchor_crosscheck_20261115.json`

## Regression Test

A corresponding test will be added under `tests/test_grid_anchor_crosscheck_seams.py` to verify the cross-check logic on synthetic data.