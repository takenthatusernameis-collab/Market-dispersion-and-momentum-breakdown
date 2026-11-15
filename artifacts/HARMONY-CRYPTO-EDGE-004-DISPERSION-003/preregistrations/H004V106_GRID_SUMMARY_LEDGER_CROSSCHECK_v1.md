# Preregistration: H004V106 Grid Summary / Ledger Cross-Check Audit

**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003
**Hypothesis ID:** H30 (next_sequence_number 29 → 30)
**Created:** 2026-11-15T06:30:00Z
**Status:** PREREGISTERED BEFORE COMPUTATION

## Objective

Verify that the aggregate statistics reported in `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/grid_summary.json` for the primary anchors (H004V105 legacy28_comparator and H004V106 expanding_point_in_time) are internally consistent with the per-cell formation records in `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/grid_result_ledger.json`.

This is a bounded, read-only integrity audit on already-committed artifacts. No frozen DISPERSION-001/002/003 artifacts/configs/inputs or the sealed holdout are modified.

## Scope

- **Input artifacts (read-only):**
  - `grid_result_ledger.json` — 216-cell committed ledger with per-cell `formations` arrays
  - `grid_summary.json` — summary with `primary_anchor_legacy_H004V105` and `primary_anchor_expanding_H004V106` sections containing full formation arrays

- **Output artifact:**
  - `integrity_audit/H004V106_grid_summary_ledger_crosscheck_<timestamp>.json`

## Method

For each primary anchor (H004V105, H004V106):

1. Load the cell from `grid_result_ledger.json["cells"][anchor_id]`.
2. Load the corresponding anchor section from `grid_summary.json`.
3. Recompute the following aggregates from the ledger cell's `formations` array:
   - `n_formations`
   - `n_high`, `n_low`, `n_mid` (state counts)
   - `high_gross_mean`, `low_gross_mean` (mean of `spread_gross` for high/low states)
   - `high_net_1x_mean`, `low_net_1x_mean` (mean of `spread_net_1x` for high/low states)
   - `high_low_diff_gross` = `high_gross_mean - low_gross_mean`
   - `high_low_diff_net_1x` = `high_net_1x_mean - low_net_1x_mean`
   - `spread_gross_mean`, `spread_net_1x_mean` (overall means across all states)
   - `spread_gross_median`, `spread_net_1x_median` (overall medians across all states)
   - `date_first`, `date_last` (formation date range)
   - `eligible_assets_per_date` (mean, min, max from formation records)

4. Compare each recomputed value against the corresponding field in `grid_summary.json` for that anchor.
5. Tolerance: exact match for integer/count fields; 1e-12 absolute tolerance for float fields (matching the grid anchor crosscheck fidelity standard).

## Decision Rules

- **PASS:** All recomputed aggregates match the summary within tolerance for both anchors.
- **FAIL:** Any mismatch beyond tolerance. Report which anchor, which field, ledger value, summary value, and difference.

## Notes

- The `grid_summary.json` contains full formation arrays for the primary anchors, while the `grid_result_ledger.json` also contains them per cell. This audit verifies they agree.
- This is an internal-consistency audit of already-inspected development evidence (the committed DISPERSION-003 grid). It is NOT a fresh holdout, NOT independent confirmation, and does NOT validate/refute/unlock H1/H6/H7/H8/H9/H10/H11.
- The audit script must be import-safe, use only stdlib + numpy/pandas, and write only to the integrity_audit directory.
- If the audit FAILs, no artifact is promoted; the finding is recorded for investigation.