# Preregistration — H004V106 Rank-Breadth Measurement Feasibility

**Program:** HARMONY-CRYPTO-EDGE-004
**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-FEAS-001
**Hypothesis ID:** H39 (next_sequence_number 38 → 39)
**Status:** EXPLORATORY_ONLY
**Created:** 2026-11-16T06:54:36Z
**Author:** automated research agent

## 1. Why this study exists

The candidate frontier is structurally exhausted: `universe_frontier.json`
records `candidate_page_cursor = 6347`, 6127 blocked candidates, 0 newly
discovered, and `historical_rank_coverage_state = NOT_PROVEN_COMPLETE`. The
committed DISP-003 expanding-universe panels cover only 32 assets
(`marketcap_panel.csv`), so the expanding arm actually run in the frozen grid is
a 32-asset universe. H3 (dispersion-momentum rank-breadth interaction) has
`next_test` = "Expand lower historical rank cohorts without a top-N cutoff and
report fixed rank bands with adequate sample sizes."

Before any outcome study of H3, a cheaper and prior question must be answered:
**does the committed free data even support a point-in-time rank universe wide
enough to estimate a rank-band interaction at all?** No committed artifact
measures this. H33 audited eligibility counts on the committed 32-asset panel;
H28 cross-tabulated Binance-vs-Coin-Metrics coverage. Neither measures the
*achievable* point-in-time market-cap rank breadth obtainable from the committed
free Coin Metrics candidate cap archive.

Per the adaptive research-gate policy (AGENTS.md + operating contract), the
least-damaging relaxation is a **descriptive/measurement feasibility study**
before estimating outcomes. This is that study.

## 2. Question and estimand

**Question:** Using only already-committed free public data (Coin Metrics
community `CapMrktEstUSD` candidate history + Binance USD-M perpetual
availability + the committed kline daily index), how large is the point-in-time
market-cap rankable universe on each date of the DISP-003 panel window, and how
many assets fall into fixed descending rank bands? Is a rank-band (H3)
interaction measurable, or is the achievable universe sample-limited?

**Estimand (descriptive only):** per-date rankable-universe size `N(d)` and its
fixed absolute rank-band composition `[1-20], [21-50], [51-100], [101-200],
[201+]`, aggregated over the study window, plus the ranks of the 32 committed
DISP-003 panel assets within that broader universe. **No returns, spreads,
dispersion states, p-values, costs or inference are computed.**

## 3. Method (frozen before computation)

1. **Universe `U` (explicit narrower population), the union of the two committed
   cap sources:**
   - **Legacy arm:** the 32 assets in `data/panels/marketcap_panel.csv`, each of
     which has a committed Binance kline panel. Cap = `CapMrktEstUSD` from the
     committed market-cap panel.
   - **Candidate arm:** every candidate `asset` with `binance.exists == true` in
     `data/panels/candidate_batch_validation.json` AND at least one
     `CapMrktEstUSD` observation in
     `data/raw/coinmetrics_candidates/<asset>_CapMrktEstUSD.json`. Cap = the raw
     candidate `CapMrktEstUSD` series.
   - `U` is the union of the two arms. The candidate arm is disjoint from the
     legacy arm (the candidate validation omits 30 of the 32 legacy assets), so
     `|U| = 32 + |candidate arm|`. This union is the broadest point-in-time
     rankable universe obtainable from the committed free data.

2. **Study window:** every date `d` in the committed `binance_klines_BTCUSDT.csv`
   daily index (UTC date from `open_time` ms), restricted to
   `2023-01-01 <= d <= 2026-10-31`.

3. **Per-date computation (point-in-time, no forward fill):**
   - `rankable(d) = { a in U : a has a CapMrktEstUSD observation exactly on d }`.
   - `N(d) = |rankable(d)|`.
   - Sort `rankable(d)` by `CapMrktEstUSD` descending, tie-break by asset id
     ascending; assign ranks `1..N(d)`.
   - Fixed absolute rank bands: `[1-20]`, `[21-50]`, `[51-100]`, `[101-200]`,
     `[201+]`; record per-date counts.

4. **Aggregate outputs:** `|U|`, number of assets with a non-empty series,
   number of study dates, `N(d)` distribution (min/p10/p50/mean/p90/max) and by
   calendar year, per-band count distribution and the fraction of dates each
   band has `>= 10` assets, the fraction of dates with `N(d) >= 100`, and the
   rank distribution of the 32 committed panel assets that lie in `U`.

5. **Frozen-hash check (read-only):** sha256 of the canonical forward block,
   the H10 fresh block, the grid result ledger, `universe_frontier.json` and the
   grid v3 config must equal their committed values before and after.

## 4. Decision rule (predeclared, outcome-blind)

Label the study **`RANK_BREADTH_MEASURABLE`** if and only if BOTH:

- (a) the median of `N(d)` over the study window is `>= 100`; AND
- (b) for each of bands `[1-20]`, `[21-50]`, `[51-100]`, the fraction of study
  dates whose band count is `>= 10` is `>= 0.90`.

Otherwise label it **`RANK_BREADTH_SAMPLE_LIMITED`**.

Either label is `EXPLORATORY_ONLY`. This study cannot validate, replace, unlock
or promote any confirmatory track (H1/H6/H7/H10) and is not independent
confirmation of anything.

## 5. Safeguards (never relaxed)

- No look-ahead: cap observations are matched on the exact date; no forward
  fill, no backfill, no today's-rank-as-history.
- No fabricated observations, invented fills, synthetic data, paid sources,
  credentials, or live/paper trading.
- The canonical forward block, H10 fresh block, grid ledger, grid summary, all
  frozen DISPERSION-001/002/003 artifacts/configs/inputs, the universe frontier
  and the sealed holdout are read-only and never modified.
- The inspected canonical forward block is NOT used as fresh evidence here; this
  is a measurement-feasibility study on committed input coverage, not a test of
  any economic hypothesis.

## 6. Expected output

- This preregistration record.
- Audit artifact under
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-FEAS-001/integrity_audit/H004V106_rank_breadth_feasibility_<timestamp>.json`.
- Registry entry H39 (EXPLORATORY_ONLY, feasibility_only).
- Regression test `tests/test_rank_breadth_feasibility_audit.py` and test update
  to `tests/test_continuous_research_contract.py` (next_sequence_number 39).
- Full suite green after changes.

## 7. No relaxation

This study relaxes no confirmatory gate: not the 30-day maturity rule, not
`MIN_ASSETS_DECILES=20`, not the trailing-decile state rule, not the Holm family,
not the alpha-spending rule. It is a standalone descriptive measurement on
committed free inputs.