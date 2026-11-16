# Preregistration: DISP-003-RANKBREADTH-REPRO-001 (H42)

- **Preregistration ID:** RANKBREADTH_REPRO_001_v1
- **Experiment / artifact family:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-REPRO-001
- **Hypothesis registry ID:** H42
- **Status:** EXPLORATORY_ONLY (computational reproducibility + raw-series integrity only; not confirmatory)
- **Label:** `RANK_BREADTH_REPRODUCED` / `RANK_BREADTH_REPRODUCTION_FAILED` (predeclared rule §5)
- **Created (UTC):** 2026-11-16T13:13:01Z
- **Scope:** Read-only, stdlib-only, offline. Independently re-derive the H39 `RANK_BREADTH_MEASURABLE` verdict from the committed raw cap archive + committed kline daily index + committed candidate validation using a SEPARATE implementation (csv/json only, no pandas), and characterize raw candidate-cap series integrity (page-chunked ordering, duplicate/conflicting dates, non-finite/non-positive values, availability/no-forward-fill). No network, no outcomes.

## 1. Why this study exists (real, demonstrable gap)

`HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-FEAS-001` (H39) measured the
point-in-time market-cap rankable universe and concluded `RANK_BREADTH_MEASURABLE`.
A repository-wide search shows **no committed artifact independently reproduces
that verdict from the raw committed inputs**, and **no artifact characterizes the
committed candidate `CapMrktEstUSD` series format/integrity** (the raw files are
page-chunked and therefore non-monotonic in file order; duplicate-date and
non-finite handling are implicit in H39's loader). This study fills both gaps with
an independent code path so a silent loader regression or an undocumented data
hazard cannot leave the H39 verdict un-reproducible.

This is **not** an independent data-source verification: it re-derives H39 from
the *same* committed inputs. It therefore does **not** change
`universe_frontier.json:historical_rank_coverage_state` (which correctly remains
`NOT_PROVEN_COMPLETE`) and does not promote any confirmatory track.

## 2. Inputs (committed, read-only)

- H39 audit: `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-FEAS-001/integrity_audit/H004V106_rank_breadth_feasibility_2026-11-16T06-57-08Z.json`
- `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/candidate_batch_validation.json`
- `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/raw/coinmetrics_candidates/*_CapMrktEstUSD.json`
- `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/marketcap_panel.csv`
- `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/binance_klines_BTCUSDT.csv`
- Frozen references (hash-checked before and after, unchanged): canonical forward
  block, h10_fresh block, grid_result_ledger, universe_frontier, grid v3 config.

## 3. Method (frozen before computation)

1. **Universe (must equal H39):** legacy arm = the 32 `marketcap_panel.csv`
   assets; candidate arm = assets with `binance.exists==true` in committed
   validation that have a non-empty committed raw `CapMrktEstUSD` series; universe
   = union (220 expected).
2. **Cap observations:** candidate arm from raw JSON (date = `time[:10]`,
   last value per date wins); legacy arm from `marketcap_panel.csv` (date =
   `date[:10]`, numeric, last wins); legacy is authoritative where both exist.
3. **Study dates:** sorted unique UTC dates from the committed BTCUSDT kline
   `open_time` (ms) index.
4. **Ranks:** per date, descending cap, tie-break asset id ascending; fixed
   descending bands `[1-20] [21-50] [51-100] [101-200] [201-+]`; linear-
   interpolation percentiles identical in definition to H39.
5. **Integrity scan:** per asset record `n_rows`, `n_distinct_dates`,
   `n_duplicate_date_rows`, `n_conflicting_dates` (same date, >1 distinct value),
   `n_nonfinite_or_nonpositive`, `first_date`, `last_date`, `n_descents`
   (adjacent in-file time decreases = page-chunk boundaries), `strictly_increasing`.
6. **Availability:** verify no forward-fill is used (each value keyed to its own
   observation date) and count duplicate-date conflicts.

## 4. Comparison targets (from H39 artifact)

`universe_size`, `n_assets_with_nonempty_series`, `rankable_size_stats.p50`
(median N(d)), `rankable_size_stats` full distribution, `band_stats[*].frac_dates_count_ge_min`,
`band_stats[*]` full distributions, and per-asset `committed_panel_rank_coverage.per_asset[*]`
(`n_dates_ranked`, `frac_study_dates_ranked`, `rank_min`, `rank_p50`, `rank_max`).

## 5. Decision rule (predeclared, outcome-blind)

Label **`RANK_BREADTH_REPRODUCED`** iff ALL:
- (a) recomputed `universe_size` == H39 and `n_assets_with_nonempty_series` == H39;
- (b) recomputed median N(d) and every band's `frac_dates_count_ge_min` equal H39
  within `1e-9`, and every band/N(d) distribution statistic (min/p10/p50/mean/p90/max/n)
  equals H39 within `1e-9`;
- (c) every legacy per-asset rank statistic matches H39 (`n_dates_ranked`, `rank_min`,
  `rank_max` exact; `frac_study_dates_ranked`, `rank_p50` within `1e-9`);
- (d) integrity: every union asset has a committed cap source, no conflicting
  duplicate dates, and no non-finite/non-positive value used in any rank.

Otherwise **`RANK_BREADTH_REPRODUCTION_FAILED`** with the explicit failing criteria.

Either label is `EXPLORATORY_ONLY` / `INCONCLUSIVE` for confirmatory purposes; it
cannot validate, replace, or unlock any confirmatory track and is not independent
confirmation.

## 6. Safeguards (hard constraints honored)

- Free public/committed data only; **no network**; no fabricated/forward-filled
  observations; no today's rank as history.
- No outcomes: no returns, spreads, dispersion states, p-values, costs, funding
  attribution, or inference.
- All frozen DISPERSION-001/002/003 artifacts/configs/inputs, canonical/H10
  forward blocks, grid ledger, universe frontier, sealed holdout, and the H39
  audit are read-only and hash-checked.
- Inspected canonical forward block is not reused as fresh evidence.
- Track separation: does not promote H39 or any confirmatory result.

## 7. Required outputs

- Preregistration (this file).
- Read-only script: `scripts/rank_breadth_reproducibility_audit.py` (import-safe
  pure helpers + CLI writing audit JSON).
- Deterministic audit artifact:
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-REPRO-001/integrity_audit/H004V106_rank_breadth_reproducibility_<ts>.json`.
- Hermetic tests: `tests/test_rank_breadth_reproducibility_audit.py` pinning the
  decision rule, independent recomputation vs H39 (excluding wall-clock/output
  path), integrity-scan behavior on synthetic fixtures, and frozen hashes.
- Registry H42 entry and `tests/test_continuous_research_contract.py` sequence bump
  in the same change.

## 8. Non-claims

Does not claim archive availability, data completeness beyond the committed
inputs, H3 rank-band outcome feasibility, tradability, statistical significance,
economic edge, or confirmatory evidence. A green script/test proves only what the
tests cover.