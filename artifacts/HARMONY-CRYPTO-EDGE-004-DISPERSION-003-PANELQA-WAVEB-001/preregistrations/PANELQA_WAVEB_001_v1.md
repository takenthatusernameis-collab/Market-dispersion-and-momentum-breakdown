# PANELQA-WAVEB-001 (H54) — Wave-B (ARK/ASTR) extension panel usability and coverage audit

- **Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELQA-WAVEB-001
- **Hypothesis ID:** H54
- **Status:** EXPLORATORY_ONLY
- **Label:** source_coverage_panel_quality
- **Created:** 2026-11-19T18:55:00Z (preregistered before any metric was computed)
- **Program:** HARMONY-CRYPTO-EDGE-004

## Motivation and distinctness

H53 verified that the 166 H52 wave-B archives normalize into 4 DISP-003-schema CSVs with exact
row accounting, sha256 reconciliation and no duplicate timestamps. H53 did **not** measure whether
those panels are usable as a forward-time series: calendar-day continuity, gap structure, OHLC
plausibility, zero-volume days, funding cadence heterogeneity, cross-asset date overlap and
end-of-panel staleness were never computed. H54 measures exactly those properties, read-only, with
no outcomes, no returns-based inference and no network I/O.

This is a distinct route from H39–H53: no hypothesis is re-run, no probe is repeated, no freeze is
touched. It is the smallest useful diagnostic for whether a future mechanism test on wave-B data
would be measuring market structure or measuring data gaps.

## Inputs (pinned, read-only)

- 4 committed panels under
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-WAVEB-001/panels/`
  (ARKUSDT klines, ARKUSDT funding, ASTRUSDT klines, ASTRUSDT funding).
- H53 audit `…/PANELNORM-WAVEB-001/integrity_audit/panel_wave_b_normalization_2026-11-19T054929Z.json`
  for the per-panel sha256 and row counts to reconcile against.
- Frozen hashes re-verified: canonical forward block, h10_fresh block, grid v3 config, universe frontier.

No archive bytes, no `data/` cache and no network are read.

## Predeclared measurements (deterministic, stdlib only)

Per panel:

1. Recompute file sha256; compare to the H53 recorded sha256 and row count.
2. `n_rows`, `first_ts_utc`, `last_ts_utc`, observed distinct calendar dates.
3. Klines only:
   - `expected_days` = (last_date − first_date) + 1 in UTC calendar days;
   - `completeness_ratio` = observed distinct dates / expected_days;
   - `n_missing_days`, `missing_days`, `max_gap_run_days` (largest run of consecutive missing days);
   - `n_nonpositive_price` (any of open/high/low/close ≤ 0);
   - `n_ohlc_inconsistent` (high < max(open, close), low > min(open, close), or high < low);
   - `n_negative_volume`, `n_zero_volume_days`.
4. Funding only:
   - `funding_interval_hours_histogram`;
   - `n_nonfinite_rate`, `n_abs_rate_gt_0_1` (sanity bound; Binance per-interval rates are far smaller);
   - `n_zero_rate`;
   - `n_duplicate_calc_time`, `rows_per_day` (descriptive only).
5. Staleness: `days_stale` = 2026-10-31 minus last observation date (panel end from the H50 trim).
6. Cross-panel: count of calendar dates present in both ARK and ASTR klines panels; count present in
   one only.

## Predeclared verdict rule

- `PANELQA_WAVEB_SCOPE_MISMATCH` if the panel set is not exactly the 4 expected files or any H53
  sha256/row-count reconciliation fails.
- `PANELQA_WAVEB_ISSUES_FOUND` if any of: klines `completeness_ratio < 0.98`; `n_nonpositive_price > 0`;
  `n_ohlc_inconsistent > 0`; `n_negative_volume > 0`; duplicate calc_time > 0; `n_nonfinite_rate > 0`;
  an interval value outside {1, 2, 4, 8} hours; `days_stale > 3`.
- `PANELQA_WAVEB_COMPLETE` only when all of the above are clean.

Issue verdicts are recorded with counts and the offending dates/rows summarised; nothing is deleted,
repaired, interpolated or excluded.

## Explicit non-claims

- A quality audit is not market evidence and not an economic result.
- No returns, spreads, dispersion states, momentum signals, p-values, costs or inference are computed.
- No candidate is promoted; no confirmatory claim; the H10 gate stays date-gated to 2026-11-30.
- Wave A (7 assets, 644 files) is out of scope: its raw bytes are absent in this checkout.
- Does not alter any frozen DISP-001/002/003 artifact, config, ledger, panel, forward block or
  frontier, and does not unlock H1/H6/H7/H10.
- A green test suite proves only what the tests cover.

## Artifacts

- Script: `scripts/panel_wave_b_quality_audit.py`
- Audit: `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELQA-WAVEB-001/qa/panel_wave_b_quality_audit_<utc>.json`
- Test: `tests/test_panel_wave_b_quality_audit.py`
