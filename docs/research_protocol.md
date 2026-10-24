# Research protocol

**Program status:** active continuous research. **Economic status:** no robust trading edge established. **Scope:** historical research only, free sources and no-cost tooling.

## 1. Evidence ledger and versioning
DISPERSION-001 and DISPERSION-002 are closed records. Do not change their hypotheses, grids, input panels, results, hashes, reports or conclusions. The initial 72-cell grid completed with zero configurations passing the recorded Holm-adjusted threshold. DISPERSION-002's discovery effect shrank to +0.79 percentage points in validation and −0.50 points in the final split. Keep complete, planned and incomplete artifacts clearly distinguished.

Any changed candidate, universe, signal, cost model, parameter axis, threshold or hypothesis gets a new experiment ID and preregistration before computing its forward outcomes. The next planned ID is HARMONY-CRYPTO-EDGE-004-DISPERSION-003.

## 2. Hypothesis registry
H1: extreme cross-sectional return dispersion weakens the next cross-sectional momentum spread; predicted high-minus-low sign is negative. Current evidence does not support H1 as a robust edge and does not establish its opposite. Keep these separately registered future candidates:
- H2: high dispersion strengthens momentum continuation.
- H3: the effect interacts with historical market-cap rank breadth or asset cohort.
- H4: continuous dispersion is more informative than sparse high/low state buckets.
- H5: effects are driven by outliers, portfolio-tail construction or volatility exposure and weaken under robust/risk-normalized diagnostics.

These are unvalidated hypotheses, not known edges. Specify a mechanism and direction before outcomes; require new future-block confirmation.

## 3. Point-in-time expanding universe
At each historical formation time, identify eligible assets using information then available, rank by historical cap descending with deterministic canonical-ID tie-breaking, and process candidates in operational cohorts. Preserve every candidate, rank, cap source, as-of/availability time, contract identity, eligibility, exclusion, missing-data reason and hash. Add candidates only from evidenced listing/eligibility dates. Never backfill pre-listing observations or substitute current rank for historical rank.

The legacy 28-asset universe is a comparator only. The expanding arm has no fixed top-N limit. Reports disclose counts by historical rank band, age/listing cohort, coverage and exclusion.

## 4. DISPERSION-003 grid
configs/dispersion_momentum_grid_v3.json declares 108 parameter combinations crossed with two universe arms, for 216 cells:
- momentum lookback: 14, 30, 60 days;
- forward horizon: 14, 30, 60 days;
- dispersion estimator: standard deviation or scaled median absolute deviation;
- dispersion reference window: 30, 90, 365 days;
- dispersion classification: outer deciles or median split;
- universe arm: legacy 28 assets or expanding point-in-time universe.

Portfolio tails are fixed at equal-weighted top/bottom deciles. The anchor uses a 30-day lookback, 30-day forward horizon, standard deviation, 365-day window and outer-decile state. Grid IDs are H004V001–H004V216; the legacy and expanding anchor cells are H004V105 and H004V106 respectively. Generate and validate the full deterministic manifest before outcome calculation.

All 216 cells are one family for exploratory sensitivity correction. Run the full grid on development/validation data only; apply Holm step-down correction at alpha 0.05 across the complete family for the registered net 1x endpoint. Report all cells and both signs. The registered H1 direction remains negative; a positive result is a candidate for a new hypothesis, not a retroactive rewrite.

## 5. Causal timing and portfolio accounting
Use completed UTC daily bars and data available by formation. Fix the monthly formation phase before outcomes. Calculate cumulative momentum over the configured lookback, sort deterministically, long the top decile and short the bottom decile, equal-weighted and non-overlapping. The forward outcome must use post-signal prices with explicit entry/exit timing. Never forward-fill missing prices, returns, funding or dispersion.

Model the baseline cost and predeclared 2x/3x stress cases. Include historical perpetual funding with correct sign and settlement timing. Report gross price return, funding PnL, fees, slippage, turnover, exposure, net return and benchmark fields separately.

## 6. Sample splits and forward confirmation
Use chronological discovery/validation data for the complete grid. Prior final splits that have already been read are development data for all future research, not untouched confirmation.

For the next genuinely forward test, use dates beginning 2025-01-01 and end at the latest fully closed UTC daily candle frozen in the preregistration. Record exact boundaries and input hashes before revealing outcomes. The forward block is evaluated only for the preselected anchor; do not use it to search parameters, assets, thresholds or costs.

For future ongoing blocks, freeze each new block and evaluate it once. Number sequential looks and apply a predeclared alpha-spending rule such as alpha_k = 0.05 / (k * (k + 1)). If any state has fewer than five independent formations or uncertainty is not estimable, label the result exploratory/inconclusive and continue accumulating future data or test another preregistered question on eligible development data.

## 7. Inference and parameter replacement
- Publish the anchor first, regardless of sign.
- Apply Holm correction across the complete 216-cell family; never adjust only the universe arm that looks best.
- Use a justified dependence-aware block bootstrap or an alternative autocorrelation-aware method. Never report a point estimate as a confidence interval. If valid inference is unavailable, say null/unavailable and why.
- Disclose effective sample size, high/low counts, statistical power where estimable, and overlapping-window limitations.
- Every expected cell must have status OK, BLOCKED, INVALID, FAILED or NOT_RUN and a reason. Resume idempotently without duplicate/missing keys.
- Shortlist replacement configs only using development data and predeclared net-of-cost, uncertainty, multiplicity and stability criteria. Shortlisting is not confirmation.
- Do not force a winner if none pass. Record the result, generate a mechanistic new hypothesis and use a fresh future block for confirmation. The best member of a losing family is not a validated strategy.

## 8. Data gates and source constraints
Gate on historical cap availability/as-of time, contract identity, lifecycle, prices, funding, UTC timing, duplicates, missingness, source terms and hashes. The historical panel previously inspected ended in 2024; refresh is mandatory. See docs/sources.md.

A blocked candidate remains in the frontier. Continue other candidates and independent research tasks. A missing source is not permission to bypass the gate or stop everything.

## 9. Required artifacts
Each run retains a preregistration, prompt-review changelog, run manifest, frozen config, grid manifest, data gate, source inventory/hashes, universe frontier, universe-coverage panel, one terminal result per expected cell, portfolio/accounting ledgers, summaries, tests, validation logs and report. Do not redistribute raw data unless its terms permit it.

## 10. Continuous feedback loop
Each worker session chooses one unblocked measurable action in this order: recover a checkpoint; expand/refresh candidate frontier; repair a source gate; complete/resume grid cells; red-team method/accounting/inference; update hypothesis status; preregister the next falsifiable candidate; update tests/docs/manifests/handoff.

Do not stop because an experiment ended, results were unfavorable, the hypothesis was rejected, a candidate's data was missing or a manual experiment ID has not been supplied. Preserve blockers and move to the next valid action. The overall program remains ACTIVE unless the user explicitly stops it.

## 11. Decision states
Use one status per experiment: NOT_RUN, BLOCKED_SPECIFICATION_GATE, BLOCKED_DATA_GATE, IMPLEMENTATION_FAILED, EXPLORATORY_ONLY, INCONCLUSIVE, REJECTED or SUPPORTED_FOR_FURTHER_RESEARCH. This does not authorize deployment/trading.

## 12. Required report sections
Include the decision and strongest adverse finding; sources and data gates; universe and rank coverage; all grid results; cost/funding attribution; uncertainty and adjusted inference; holdout integrity; sample size; hashes; tests; limitations; and highest-value next test.

End the report with:
- SUPPORTED EVIDENCE
- MIXED / INCONCLUSIVE EVIDENCE
- REJECTED / ARCHIVED EVIDENCE
- HIGHEST-VALUE NEXT TEST
