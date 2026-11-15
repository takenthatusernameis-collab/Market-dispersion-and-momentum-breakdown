# Preregistration: H004V106 Grid Ledger Internal-Consistency Audit

**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003
**Audit ID:** H004V106_GRID_LEDGER_INTERNAL_CONSISTENCY
**Hypothesis ID:** H32 (next_sequence_number 31 → 32)
**Created:** 2026-11-15T08:50:00Z
**Status:** PREREGISTERED BEFORE COMPUTATION

## Change log

- 2026-11-15T08:50:00Z — initial preregistration, written before the audit script is run.

## Objective

Verify that every one of the 216 committed DISPERSION-003 grid cells is
*internally self-consistent*: its per-formation accounting, state counts,
aggregate statistics, date range, eligible-asset coverage, p-value and Holm
flag all agree with a recomputation from that cell's own `formations` array.

This is a bounded, read-only integrity audit on already-committed artifacts.
No frozen DISPERSION-001/002/003 artifacts/configs/inputs, frontier, registry
entry (other than this allocation) or sealed holdout is modified.

## Why this is not already covered

- H29 (`H004V106_GRID_ANCHOR_CROSSCHECK`) recomputes the **anchor** cell
  (H004V106) from its own formation records.
- H30 (`H004V106_GRID_SUMMARY_LEDGER_CROSSCHECK`) compares the two **primary
  anchor** aggregates in `grid_summary.json` against the ledger cells.
- H31 (`H004V106_H10_FRESH_FORWARD_BLOCK_INTEGRITY_AUDIT`) audits the single
  H10 fresh sealed forward block.
- `tests/test_ledger_manifest_binding.py` pins the **parameter** binding between
  the ledger and the frozen manifest; it does not check per-cell accounting.
- `tests/test_momentum_accounting.py` only checks that dispersion magnitudes are
  order-one.

No existing artifact audits the per-cell accounting invariants across **all 216
cells** (the non-anchor cells are never re-derived). This audit closes that gap.

## Scope

- **Input artifact (read-only):**
  - `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/grid_result_ledger.json`
    (216-cell committed ledger with per-cell `formations` arrays)

- **Output artifact:**
  - `integrity_audit/H004V106_grid_ledger_internal_consistency_<timestamp>.json`

## Predeclared checks (per cell, for all 216 cells)

For each cell `c` with `formations = c["formations"]`:

1. `n_formations` equals `len(formations)`, and the cell has at least one formation.
2. Formation `formation_date` values are strictly increasing and unique.
3. Every formation `state` is one of `{high, low, mid}`.
4. Every formation `dispersion` is finite and `>= 0`.
5. Every formation `n_assets` is a positive integer.
6. **Accounting invariant:** the implied per-formation cost
   `spread_gross - spread_net_1x` is constant within the cell (max − min
   `<= 1e-12`) and equals the declared baseline 1x cost `0.001`
   (`abs(implied_cost - 0.001) <= 1e-12`).
7. **State counts:** `n_high`, `n_low`, `n_mid` equal the counts of
   `state == "high" / "low" / "mid"` over the cell's formations.
8. **Aggregates:** recomputed from the formations, within `1e-12`:
   `high_gross_mean`, `low_gross_mean`, `high_net_1x_mean`, `low_net_1x_mean`,
   `high_low_diff_gross = high_gross_mean - low_gross_mean`,
   `high_low_diff_net_1x = high_net_1x_mean - low_net_1x_mean`,
   `spread_gross_mean`, `spread_net_1x_mean`, `spread_gross_median`,
   `spread_net_1x_median` (each over the matching state subset or all
   formations, as named; `None` when the subset is empty).
9. **Date range:** `date_first` and `date_last` equal `min`/`max` formation date.
10. **Eligible coverage:** `eligible_assets_per_date.min` / `.max` equal
    `min`/`max` of formation `n_assets`, and `.mean` matches the arithmetic
    mean within `1e-9`.
11. **Inference fields:** `pvalue_bootstrap_two_sided` is in `[0, 1]` (or `None`)
    and `holm_rejected` is a boolean.

## Global (ledger-level) checks

12. `expected_cells == 216 == len(cells)`; every `config_id` is unique.
13. `cells_ok`, `cells_evaluated`, `cells_failed`, `cells_blocked` agree with the
    observed terminal `status` distribution.
14. `holm_rejected_count` equals the number of cells with `holm_rejected == True`.

## Decision rules

- **PASS:** all per-cell checks (1–11) and all global checks (12–14) hold, with
  zero violations.
- **FAIL:** any violation is reported with the cell id, the check, the expected
  value and the observed value. A FAIL is recorded, not silently dropped; no
  artifact is promoted.

## Notes

- The audit script is import-safe (`main()` is `__main__`-guarded), uses only the
  standard library, reads one committed JSON artifact, and writes only the
  integrity_audit output.
- This is an internal-consistency audit of already-inspected development
  evidence. It is **not** a fresh holdout, **not** independent confirmation, and
  does **not** validate/refute/unlock H1/H6/H7/H8/H9/H10/H11.
- No cost, return, state, p-value or inference is recomputed for a new economic
  claim; the checks only compare a cell's own recorded fields against its own
  formation records.