# Preregistration — H004V106 Expanding Universe Eligibility Coverage Audit

**Program:** HARMONY-CRYPTO-EDGE-004
**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-EXP-ELIG-001
**Hypothesis ID:** H33 (next_sequence_number 32 → 33)
**Status:** EXPLORATORY_ONLY
**Created:** 2026-11-15T10:15:00Z
**Author:** automated research agent

## 1. Why this audit exists

The DISPERSION-003 grid ledger records `eligible_assets_per_date` summary statistics (min/mean/max/median) for each of the 108 expanding-universe cells. These summaries show three distinct mean values across dispersion reference windows (29.03, 29.02, 28.99), reflecting different formation date sets per window. However, no committed artifact independently reconstructs the point-in-time eligibility map from raw panels and validates it against the ledger, nor does any artifact report the per-date eligible asset count, rank distribution, contract lifecycle events (listing/delisting), or exclusion reasons across the full expanding universe arm.

This audit fills that gap: it independently recomputes the expanding-universe eligibility map from the committed raw panels (marketcap, klines, funding) using the same point-in-time rules as `run_dispersion003_grid.py::build_eligibility_map`, and produces a diagnostic coverage artifact. It does NOT compute returns, spreads, states, p-values, costs, or inference. It is a read-only measurement/feasibility study on already-committed development inputs.

## 2. Question and estimand

**Question:** At each formation date in the DISPERSION-003 expanding universe arm, what is the exact set of eligible assets, their historical market-cap ranks, contract symbols, listing/delisting status, and exclusion reasons? How does the eligible count evolve over time, and does the independently reconstructed map match the ledger's recorded `eligible_assets_per_date` summaries?

**Estimand:** Per-formation-date eligibility detail (asset list, ranks, caps, contract lifecycle, exclusion reasons) and aggregate coverage statistics (time series of eligible count, rank distribution, listing/delisting events). Comparison of independently reconstructed eligible counts per date to the ledger's per-cell summaries.

## 3. Method (frozen before computation)

1. **Inputs (read-only, committed):**
   - `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/marketcap_panel.csv`
   - `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/binance_klines_*.csv`
   - `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/binance_funding_*.csv`
   - `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/grid_result_ledger.json` (for comparison only)

2. **Eligibility logic (mirrors `run_dispersion003_grid.py::build_eligibility_map` for `expanding_point_in_time` arm):**
   - Asset → Binance symbol mapping: `<ASSET.upper()>USDT` (from klines panel filenames)
   - At each date present in marketcap panel:
     - Require `CapMrktEstUSD` observation (non-NaN) on that exact date (no forward-fill)
     - Require price (klines) observation for the mapped symbol on that exact date
     - Rank eligible assets by `CapMrktEstUSD` descending, tie-break by asset id ascending
     - Record contract lifecycle: listing date = first price date, delisting date = last price date
     - Exclusion reasons: `no_market_cap_observation`, `no_perpetual_contract`, `not_yet_listed`, `delisted`

3. **Comparison to ledger:**
   - For each expanding-universe cell in the grid ledger, extract its formation dates and the `eligible_assets_per_date` summary.
   - Compare the independently reconstructed eligible count per formation date to the ledger's implied counts (the ledger stores min/mean/max/median; we verify the per-date counts are consistent with those summaries).

4. **Outputs (written only under `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/`):**
   - `H004V106_expanding_universe_eligibility_coverage_<timestamp>.json` containing:
     - Per-date eligibility detail (date, eligible_count, assets_with_ranks, listing_events, delisting_events, exclusion_counts)
     - Aggregate coverage statistics (eligible_count time series, rank distribution percentiles, total listing/delisting events)
     - Ledger comparison: per-cell formation date set vs reconstructed eligibility, summary statistic consistency check
     - Frozen hash verification (canonical block, H10 fresh block, grid ledger, universe frontier)
   - Status: EXPLORATORY_ONLY. No hypothesis conclusion, no promotion, no sealed holdout opened.

## 4. Decision rule (predeclared)

- **PASS:** Audit runs to completion without exception; all per-date eligible counts are non-negative integers; ledger comparison reports consistency (reconstructed counts fall within ledger min/max per cell, mean within 1.0 of ledger mean); frozen hashes unchanged.
- **FAIL:** Any exception, negative eligible count, or ledger inconsistency beyond tolerance.
- **EXPLORATORY_ONLY:** Regardless of PASS/FAIL, this audit does not validate, replace, or unlock any confirmatory track (H1/H6/H7/H10). It is a descriptive measurement on development data only.

## 5. Safeguards (not relaxed)

- No look-ahead: eligibility uses only data available on the formation date.
- No forward-fill, synthetic data, invented fills, paid sources, live/paper trading.
- The canonical forward block, H10 fresh block, grid ledger, grid summary, and all frozen DISPERSION-001/002/003 artifacts/configs/inputs are read-only and never modified.
- Today's ranks are never used as historical ranks; all ranks are point-in-time from `CapMrktEstUSD`.

## 6. Expected output

- Preregistration record here (this file).
- Audit artifact under `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/H004V106_expanding_universe_eligibility_coverage_<timestamp>.json`.
- Hypothesis registry entry H33 (EXPLORATORY_ONLY).
- Test updates: `tests/test_continuous_research_contract.py` (next_sequence_number 33), `tests/test_preregistration_coverage_audit.py` (main_audits_scanned +1), `tests/test_integrity_audit_reference_consistency.py` (main_integrity_audit_files_scanned +1), `tests/test_preregistration_completeness.py` (AUDIT_TO_HYPOTHESIS + ALIASES), `scripts/audit_preregistration_coverage.py` (ALIASES).
- Full suite green after changes.

## 7. No relaxation

This audit does not relax the 30-day maturity rule, the MIN_ASSETS_DECILES=20 gate, the trailing-decile state rule, the Holm family, or any confirmatory criterion. It is a standalone descriptive diagnostic.