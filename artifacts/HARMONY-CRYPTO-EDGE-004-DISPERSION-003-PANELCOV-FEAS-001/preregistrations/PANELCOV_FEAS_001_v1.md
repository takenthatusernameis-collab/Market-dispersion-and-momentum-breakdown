# Preregistration — H004V106 Committed-Panel Coverage Extension Feasibility

**Program:** HARMONY-CRYPTO-EDGE-004
**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-FEAS-001
**Hypothesis ID:** H40 (next_sequence_number 39 → 40)
**Status:** EXPLORATORY_ONLY
**Created:** 2026-11-16T08:10:00Z
**Author:** automated research agent

## 1. Why this study exists

`HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-FEAS-001` (H39, `EXPLORATORY_ONLY`, `RANK_BREADTH_MEASURABLE`) established that point-in-time rank breadth is measurable over a 220-asset union (32 legacy panel assets + 188 candidate assets with committed Coin Metrics `CapMrktEstUSD` and verified Binance USD-M perpetual). H39 caveat: only the 32 legacy assets have committed Binance kline/funding panels; the 188 candidate-union assets lack committed price/funding panels, so a full H3 rank-band outcome study is price-panel-limited at 32 assets.

Before any outcome study, a prior planning question must be answered using only committed free artifacts: **is extending committed Binance kline/funding panel coverage to the 188 PIT-eligible candidate-union assets feasible in principle given committed metadata, and what is the bounded ingestion/coverage scope?**

This is a descriptive/measurement and planning feasibility study (least-damaging relaxation). No market returns, spreads, dispersion states, p-values, costs, or inference are computed.

## 2. Question and estimand

**Question:** For each of the 188 H39 universe assets without committed kline panels, do committed artifacts provide a deterministic Binance symbol mapping, verified Binance perpetual existence, and Coin Metrics cap observations in the H39 study window (2023-01-01..2026-10-31)? What is the implied monthly archive scope (46 study months × 2 series kinds = 92 files/asset upper bound) if all months were available?

**Estimand (descriptive only):** per-asset coverage/planning record `{asset, symbol, binance_exists, validation_status, cap_obs_in_study_window, cap_first_in_window, cap_last_in_window, cap_coverage_frac, committed_raw_kline_dir, committed_raw_funding_dir, committed_kline_panel, committed_funding_panel, required_months, expected_zip_kinds, expected_zip_files_upper_bound}` and aggregate counts. **No network probing, no archive fetch, no panel construction, no outcome computation.**

## 3. Method (frozen before computation)

1. **Input set:** the 188 `universe_assets_without_committed_kline_panel` from committed `H004V106_rank_breadth_feasibility_2026-11-16T06-57-08Z.json` (read-only).
2. **Symbol/validation source:** committed `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/candidate_batch_validation.json` (verified Binance USD-M perpetual records).
3. **Cap observations:** committed raw Coin Metrics candidate `CapMrktEstUSD` files under `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/raw/coinmetrics_candidates/`, intersected with the committed BTCUSDT kline daily index dates in `2023-01-01..2026-10-31`.
4. **Committed panel/raw presence:** check only committed paths under `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/raw/binance/{klines,funding}/<SYMBOL>` and `data/panels/binance_{klines,funding}_<SYMBOL>.csv`.
5. **Study months:** sorted unique `YYYY-MM` from study dates (46 months, 2023-01..2026-10).
6. **Frozen-hash check (read-only):** verify canonical forward block, H10 fresh block, grid result ledger, universe frontier, grid v3 config, and H39 rank-breadth audit SHA256s before and after.

## 4. Decision rule (predeclared, outcome-blind)

Label **`PANEL_EXTENSION_FEASIBLE_IN_PRINCIPLE`** if and only if ALL:
- (a) all 188 assets are present in committed candidate validation with `binance.exists == true` and `status == "verified"`;
- (b) all 188 have `cap_obs_in_study_window >= 1`;
- (c) none have committed raw kline/funding dirs or committed kline/funding panel CSVs (confirming the gap is real and unfilled);
- (d) deterministic symbol mapping exists for every asset.

Otherwise label **`PANEL_EXTENSION_LIMITED`**.

Either label is `EXPLORATORY_ONLY` / `INCONCLUSIVE` for confirmatory purposes. This study cannot validate, replace, unlock, or promote any confirmatory track and is not independent confirmation. It does not claim archive publication for any specific month/symbol.

## 5. Safeguards (never relaxed)

- No network access, no archive fetch, no fabricated observations, no synthetic data, no forward fill, no today's rank as history.
- No outcomes, returns, spreads, states, p-values, costs, or inference.
- All frozen DISPERSION-001/002/003 artifacts/configs/inputs, canonical/H10 forward blocks, grid ledger, universe frontier, sealed holdout, and H39 audit are read-only.
- Inspected canonical forward block not used as fresh evidence.

## 6. Expected outputs

- This preregistration.
- `integrity_audit/H004V106_panel_coverage_extension_feasibility_<ts>.json`.
- `scripts/panel_coverage_extension_feasibility.py`.
- `tests/test_panel_coverage_extension_feasibility.py`.
- Registry H40 entry (`EXPLORATORY_ONLY`, `feasibility_only`) and `tests/test_continuous_research_contract.py` bump in same change.
