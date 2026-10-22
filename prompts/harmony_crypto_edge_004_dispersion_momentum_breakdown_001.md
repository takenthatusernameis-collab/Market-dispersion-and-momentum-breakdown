# HARMONY CRYPTO-EDGE-004 — Market Dispersion and Momentum Breakdown
## Iteratively Improved Research-Agent Prompt v2.0 (Free Data, Point-in-Time Universe, Fail-Closed Validation)

**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-001  
**Research hypothesis:** CRYPTO-EDGE-004 — extreme cross-sectional dispersion weakens the subsequent cross-sectional cryptocurrency momentum spread  
**Execution repository:** takenthatusernameis-collab/Market-dispersion-and-momentum-breakdown
**Reference repository:** takenthatusernameis-collab/Expansion (read-only reference for prior protocols; do not modify it)  
**Scope:** reproducible historical research and backtesting only; no live trading, order placement, exchange-account access, or deployment  
**Data-cost boundary:** no paid services, subscriptions, trials, paid API tiers, paid compute, or purchases  
**Principle:** falsify the hypothesis fairly; do not optimize it into a result

---

## 1. Mission and decision

Determine whether high cross-sectional dispersion predicts a weaker next-month cross-sectional momentum spread than low dispersion, and whether the conditional difference is economically meaningful after realistic trading costs and perpetual funding.

Do not assume the hypothesis is profitable because it is plausible, has a high research score, or appears in a ranked shortlist. The current CRYPTO-EDGE-004 record says its registered prediction remains untested. Create the first reproducible empirical evidence, or provide a precise, auditable explanation of why the test is blocked.

The order of questions is mandatory:

1. Can a suitable historical, free-data, investable universe be constructed without future information or silently excluding failed/delisted contracts?
2. Does the unconditional momentum spread exist on that exact same universe, before conditioning on dispersion?
3. Does the preregistered high-versus-low dispersion comparison reduce that spread in the expected direction?
4. Does any difference survive realistic costs, funding, timing, capacity constraints, placebo tests, and chronological out-of-sample evaluation?
5. Is the evidence sufficient for independent confirmation, or must the candidate be rejected, left inconclusive, or blocked?

A state-dependent result is not proof of a tradable edge if the underlying unconditional momentum spread is absent or consumed by costs.

## 2. Iterative refinement history

These refinement passes are mandatory protections, not suggestions. Preserve them in future prompt revisions.

- **Pass 1 — translate the thesis:** turn “market dispersion and momentum breakdown” into a falsifiable comparison of forward momentum spreads under high versus low dispersion.
- **Pass 2 — separate prediction from profitability:** require the unconditional momentum baseline first, separating gross predictability from net investable returns.
- **Pass 3 — solve the universe problem:** use dated, point-in-time market-cap observations and contract eligibility; build a ranked universe from largest to smallest without an arbitrary top-N stop or a current-list backfill.
- **Pass 4 — research integrity:** preregister definitions, chronology, costs, benchmarks, placebos, uncertainty estimates, and data gates before calculating any outcome statistic.
- **Pass 5 — free data and reproducibility:** verify access at run time; preserve provenance, checksums, and an auditable data frontier.
- **Pass 6 — adversarial review:** audit look-ahead, survivorship, ticker mapping, revisions, overlapping observations, multiple testing, missing-data selection, and the distinction between an exact registered-screen replication and an expanded-universe extension.

Do not loosen an earlier control to obtain a more favorable result.

## 3. Repository and source-of-truth audit

Before implementing or running any strategy calculation:

1. Read the latest CRYPTO-EDGE-004 record in the public QUANTITATIVE-CRYPTOCURRENCY-INDICATORS-HYPOTHESIS-FACTORY repository, including its plan of record, registered statistic, source notes, shortlist, rejected/deferred history, and latest handoff.
2. Read this repository’s README, data-coverage and regime-coverage controls, relevant experiment protocols/prompts, and any candidate-specific data or cached artifacts.
3. Record the commit SHAs, file paths, versions, exact thesis, registered estimand, data window, and current state of any related candidate.
4. Identify every ambiguity in the original entry. Never silently choose whichever interpretation improves the result.
5. Keep this prompt's implementation, tests, data gates, experiment manifests, and results in Market-dispersion-and-momentum-breakdown. Treat Expansion as read-only reference material only; do not edit it as part of this task. Do not edit the hypothesis factory, Contraction, or unrelated repositories.
6. Do not mutate unrelated strategy rules, infrastructure, workflows, schedules, permissions, or secrets. If a new workflow is genuinely required, document why existing execution machinery is inadequate, keep the change narrowly scoped, and do not weaken repository protections.

The current factory record describes a free-data replication whose market-cap screen is not identical to its published reference screen. Preserve the original registered specification as the primary arm. Treat the user-requested continuously expanding market-cap-ranked universe as a distinct secondary arm unless the authoritative plan already defines it as primary. Never silently replace one with the other.

## 4. Free-data-only policy

### Candidate source families

Start with legally reusable public sources:

- **Historical crypto market capitalization:** the factory has documented a Coin Metrics Community API daily panel with fields named CapMrktEstUSD and CapMrktCurUSD, and a measured route that previously returned data without a credential. Coin Metrics documents a separate Community API at https://community-api.coinmetrics.io/v4 and a paid Pro API. Verify the exact endpoint/version, field availability, historical coverage, current access rules, rate limits, and license terms at execution time. Official references: https://docs.coinmetrics.io/api/v4/ and https://github.com/coinmetrics/product-docs/blob/master/docs/packages/coin-metrics-community-data.md.
- **Binance USDⓈ-M perpetual prices/volume:** use Binance’s official public archive and official market-data documentation where suitable. See https://github.com/binance/binance-public-data and https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data
- **Funding:** use historical public funding records from a free, documented source if they cover the same contracts and holding dates. Verify units, sign, event times, interval, and timestamp semantics.
- **Other sources:** consider only after checking access, reuse rights, historical coverage, identity mapping, and field semantics. A free current quote does not establish that a full historical panel is free.

Coin Metrics distinguishes its keyless Community API from its paid Pro API, and documents community metrics as available under a Creative Commons license with community rate limits. Keyless access does not by itself establish that a license permits every intended use: verify the terms, including whether they permit the intended research and future use, before collecting data. Do not silently switch to the paid api.coinmetrics.io endpoint. If license or access is incompatible with the intended use, find an adequate source whose terms permit it or classify the data gate as blocked. CoinGecko’s published API comparison, for example, describes a one-year historical-range limit on its free Demo tier, so do not treat it as a full-history replacement: https://www.coingecko.com/learn/coingecko-api-troubleshooting-guide-and-solutions

### Absolute prohibitions

- No subscriptions, paid API tiers, trials that roll into billing, paid datasets, data brokers, paid cloud compute, purchases, or requests for the user to buy data.
- Do not use paid/private/institutional data even if an endpoint offers a temporary trial.
- Never put API keys, tokens, cookies, signed URLs, personal account data, or private files in commits, prompts, logs, or public artifacts.
- Prefer keyless public sources. If a genuinely free key is indispensable, verify there is no payment requirement, use an approved secret mechanism, and never print the key. Otherwise classify the test as blocked.
- Respect rate limits with bounded exponential backoff and caching. A 401, 403, 404, 429, missing month, or unavailable endpoint is evidence to document—not permission to pay, scrape restricted services, or invent data.
- Do not claim “free-data validated” unless every indispensable data leg and the planned runner are accessible within the no-payment boundary.

## 5. Descending, continually expanding market-cap universe

This requirement is load-bearing. The objective is to exhaust the verifiable free-data universe, not repeatedly test a convenient small list.

### 5.1 Historical strategy universe

- Reconstruct eligibility at each historical formation timestamp from information observable as of that timestamp.
- Rank eligible underlying assets by point-in-time market capitalization in descending order on each formation date. Persist the date, value, source, rank, asset identity, contract identity, eligibility decision, and exclusion reason.
- Use historical rank for historical decisions, never today’s ranking projected backward.
- Construct effective-dated mappings between market-cap asset identities and Binance perpetual symbols. Handle ticker changes, collisions, migrations, wrapped/duplicated assets, symbol reuse, listings, and contract terminations explicitly.
- Include historically listed but now inactive/delisted contracts where free archives permit. Never drop a failure merely because it disappeared from the current active-symbol list.
- An instrument can enter only from its actual available/listing date and must stop earning contract returns after its valid trading life ends. Do not synthesize pre-listing returns or substitute spot returns for perpetual returns.
- Report per-date market-cap, price, funding, and common-panel coverage by rank band.
- Preserve the factory’s registered USD 60.3 million reference ceiling and CapMrktEstUSD / CapMrktCurUSD definitions exactly. The latest handoff describes the $60.3 million threshold as the reference used for the market-cap size label, with CapMrktCurUSD as the preregistered robustness check; do not turn it into an arbitrary top-N or market-cap eligibility cutoff. Reconfirm this against the latest authoritative plan at execution time. If the plan itself conflicts, record the issue and resolve it in an outcome-blind preregistration addendum. Keep the expanded all-rank arm separately labeled if it differs from the registered screen.

### 5.2 Operational expanding-rank acquisition queue

Maintain a persistent, append-only candidate and data-coverage ledger:

1. Obtain the broadest eligible dated asset list available from verified free sources.
2. Sort each date’s eligible market-cap universe in descending market-cap order.
3. Acquire, validate, and checkpoint the highest-ranked not-yet-complete cohort first. A batch size such as 100 assets is only a download/checkpoint size, never an investable-universe cutoff.
4. When a cohort is complete or explicitly marked incomplete, proceed to the next lower-ranked cohort. Continue until all identifiable eligible assets and obtainable dates have been processed or the verifiable source boundary is reached.
5. Reconcile each cohort against previous IDs to prevent duplicate assets/contracts and repeated experiments. Resume from checkpoints; do not reset to the top 20.
6. Add new listings only when they become historically eligible. Never backfill them into earlier dates.
7. Report the registered primary arm, prespecified rank-band diagnostics, and cumulative coverage checkpoints as the rank frontier expands. Do not use cumulative results to choose a profitable cutoff.
8. Record the last verified rank/date, next unprocessed rank, unique assets and contracts, duplicate/rejected IDs, missing assets, endpoint exhaustion, errors, and reasons for stopping.

**Do not confuse market-cap ranking with momentum ranking.** Market cap determines universe eligibility, rank bands, and the registered size label. Momentum determines portfolio ranks *inside* the eligible point-in-time universe. Download order must never determine strategy eligibility.

### 5.3 Fail-closed data gate

Before calculating any forward outcome or strategy-performance statistic, validate:

- Schema, units, UTC timestamps, completed bars, duplicates, row order, impossible values, symbol/asset mapping, and market-cap field meanings.
- Coverage across all sources and rank cohorts, exact shared dates, and usable asset counts on every formation date.
- Historical and inactive/delisted asset representation.
- Each asset’s first/last valid observation and each contract’s first/last eligible date, internal gaps, zero-volume bars, stale prices, cap gaps, and funding gaps.
- Source revisions/checksums; save SHA-256 for every raw archive and normalized panel.
- No future observations used for historical rank, screening, signals, liquidity measures, thresholds, or membership.
- An estimate of effective independent sample size and statistical power/minimum detectable effect.

Do not forward-fill missing returns, market caps, membership, funding, or lifetimes. Freeze missingness rules before outcomes are read. Exclude rows only under a preregistered rule and report counts/reasons. If reliable point-in-time cap ranks, survivorship treatment, identity mapping, or the necessary price/funding panel cannot be verified, emit **blocked_data_gate** and do not make confirmatory performance claims.

## 6. Freeze the hypothesis and estimand

### 6.1 Registered hypothesis

**H1:** Compared with a low-dispersion state, a high cross-sectional dispersion state is associated with a smaller subsequent one-month cross-sectional momentum spread on the registered eligible universe.

The primary statistic is the difference between the next-month momentum spread in high-dispersion and low-dispersion states. The predicted sign is negative. Test the statistic exactly as specified in the latest plan of record.

**H0:** High- and low-dispersion states do not differ in the registered forward momentum spread in the predicted direction. Report the preregistered directional test and a two-sided uncertainty interval; do not change inferential method after learning the sign.

### 6.2 Specification lock

Before inspecting forward-return outcomes:

1. Freeze the plan’s momentum definition, dispersion variable, state thresholds, formation times, evaluation horizon, portfolio breakpoints, size screen, eligible instruments, benchmark, and statistic.
2. Store the complete specification, decisions, sources, code version, and hashes in a versioned experiment file and manifest.
3. Add automated tests for signal timing and calculation of the primary statistic.
4. Persist the preregistration commit SHA and a timestamped copy before reading outcomes.

If the authoritative plan does not unambiguously specify an essential rule, do not invent it after results are visible. Record the gap and create an outcome-blind amendment first. Use the fallback defaults below only where the plan is genuinely silent. Label deviations as a free-data replication/extension, not an exact reproduction.

### 6.3 Frozen fallback only where the original specification is silent

- **Formation:** after a fully closed UTC daily bar; assume execution no earlier than the next tradable bar.
- **Momentum:** 30-day compounded return using only complete daily observations available at formation.
- **Forward measurement:** next 30 calendar days, with no overlap between formation inputs and subsequent outcome.
- **Cross-sectional momentum spread:** equal-weight return of the top momentum quintile minus the equal-weight return of the bottom momentum quintile, both formed from the same eligible point-in-time universe.
- **Dispersion:** cross-sectional standard deviation of those same eligible assets’ 30-day returns at formation.
- **State assignment:** a fixed historical threshold computed only from prior dispersion observations. Default to the past 365 calendar days and a past-only median threshold; state the minimum observations and freeze it before outcome calculation.
- **Trading expression:** long top momentum quintile / short bottom momentum quintile, rebalanced monthly and held for the next month. If the authoritative registration specifies a different schedule or weighting, the registration takes precedence in the primary arm.
- **Size screen and exclusions:** follow the authoritative plan. Register any fallback decisions before outcomes are calculated.

These defaults make an underspecified test executable; they do not establish exact replication. If instrument identity, return timing, or lawful free-data access still requires guessing, stop with **blocked_specification_gate**.

## 7. Mandatory test sequence

### Phase A — data construction and integrity

Complete the data gate first. Save diagnostics even if it fails. Never calculate performance metrics on an invalid or convenience-selected panel.

### Phase B — unconditional baseline first

Using the exact same eligible assets, dates, cap screen, signal definition, return accounting, and formation rules as the conditional test:

- Calculate the unconditional cross-sectional momentum spread before conditioning on dispersion.
- Report gross and net spreads, turnover, costs, funding PnL, coverage, and effective sample size.
- Use a matched equal-weight eligible-universe benchmark with identical dates/timing/accounting. Report BTC as context, not as an interchangeable benchmark.
- Run random-ranking and state/time-permutation placebos using identical dates, selection counts, costs, and accounting.
- If the baseline is zero/negative or does not survive base costs, state that before conditional results. The conditional interaction may be scientifically interesting but must not be marketed as a profitable strategy.

### Phase C — registered dispersion-conditioned test

Only after the baseline protocol and statistic are frozen:

- Estimate high-state spread, low-state spread, their difference, and preregistered uncertainty.
- Report coverage in each state, formation dates, unique contracts, overlapping forward windows, and effective sample size.
- Use an inference method suitable for serial dependence and overlapping horizons, such as a preregistered 30-day block bootstrap or HAC estimator. Freeze the method/lag rule beforehand.
- Report gross and net conditional differences; net is the economic decision quantity.
- Report state persistence, tail behavior, and dominance by any single event, date, or asset.
- Do not search alternate lookbacks, rebalance frequencies, state cutoffs, quantiles, cap thresholds, assets, venues, or holding windows to improve the primary result. Label exploratory variants separately, account for multiplicity, and never use them to rescue a failed registered test.

### Phase D — expanding universe and rank diagnostics

Report the registered primary arm and prespecified diagnostics by descending market-cap rank band, including lower-ranked cohorts absent from the initial data batch. Use consistent date-effective eligibility, pricing, costs, and formation times.

Rank-band results may reveal composition dependence, but cannot select an after-the-fact cutoff. Report the number of tests and address multiple comparisons. Preserve all negative and incomplete results. The expanded-universe result cannot replace a failed registered-screen result; label changed definitions as extensions.

### Phase E — realistic costs and portfolio accounting

- Verify the public official fee schedule for the exact instrument at run time. Record the source and assumptions before outcome analysis.
- Measure turnover from actual target-weight changes. Apply costs to each entry, rebalance, exit, and terminal liquidation.
- Include historical funding PnL with correct sign, event timestamps, and units for both long and short positions.
- Freeze a conservative slippage model from observable public liquidity. Report capacity and order notional versus trailing, past-only quote volume/ADV.
- Report a base cost case and 2x/3x total trading-cost stresses. Where useful, show fee and slippage components separately. Never lower the cost model after inspecting results.
- Benchmarks/placebos must use comparable net accounting. Never compare gross strategy returns with a net benchmark.
- Test accounting against hand-calculated toy panels: flat price, missing bar, zero trade, listing/termination, funding sign, turnover, terminal liquidation, and fold isolation.

If the public funding/cost data are missing for material parts of the primary sample, disclose the uncovered population and block or downgrade the net-tradability claim rather than assume missing costs are zero.

### Phase F — chronological OOS and robustness

- Use a chronological 60% discovery / 20% validation / 20% final-test split unless the authoritative registered protocol already sets another split. Fix boundaries by timestamp before inspecting outcomes.
- Freeze features, thresholds, universe rules, costs, benchmarks, and statistic before accessing final-test results.
- Report all periods chronologically, including equal chronological halves of the final test where sample size allows.
- Use paired, dependence-aware block-bootstrap intervals for forward spreads and their high-low difference. Save seed, block length, replication count, and design.
- Estimate effective sample size and power/minimum detectable effect. If the final test contains fewer than 24 effective independent forward-holding periods, classify a positive result as **exploratory_only** or **inconclusive**, not confirmatory.
- Repeat the registered result with CapMrktCurUSD replacing CapMrktEstUSD as the named capitalization robustness check, keeping all other rules fixed. This is a robustness arm, not another opportunity to select a winner.
- Test predefined cost stresses, regimes, coverage strata, and rank bands. A later-regime failure is evidence, not a tuning trigger.
- The expanding all-rank result cannot replace a failed primary registered screen.

## 8. Mandatory red-team checklist

The implementer and an independent reviewer must evaluate:

- Historical survivorship, delisted assets/contracts, termination/relisting, and identifier reuse.
- Market-cap timestamps, revisions, supply-estimation changes, stale observations, and coverage shifts.
- Look-ahead in availability, ranking, screening, returns, volume/ADV, funding, thresholds, and rebalance timing.
- Whether sparse cross-sections or missingness create artificial dispersion.
- Missing-not-at-random histories, exchange listing selection, assets without matching perpetuals, duplicate/bridged assets, ticker changes, and contract settlement semantics.
- Dependence on a single asset/date, market-wide crash, or bull/bear regime.
- Overlapping horizons, serial correlation, repeated state labels, low effective sample size, and low power.
- Multiple testing across all tried rank bands, signals, universes, screens, costs, and versions.
- Whether dispersion is a proxy for volatility, size composition, cross-sectional beta, liquidity, funding, momentum reversal, or another known factor.
- Identical eligibility, dates, weights, costs, and accounting in benchmarks and placebos.
- Current source terms, clean-checkout reproducibility, cache integrity, and access without paid or private data.
- Nonfinite statistics, zero-variance edge cases, annualization, timezone boundaries, incomplete bars, and portfolio leakage between folds.

An unexplained mismatch in frozen statistic, universe, timestamp, or accounting invalidates the affected result until reconciled. Narrative cannot override a failing machine gate.

## 9. Required tests and immutable artifacts

Add only the minimum code/tests needed for this experiment, following Expansion conventions. Run relevant tests before a full evaluation. Do not change unrelated candidates or workflows.

Save outputs under:

artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-001/

Required outputs:

- **run_manifest.json:** repository/commit SHAs, run timestamps, sources/access classifications, exact window, environment, code identity, seeds, configuration hash, output hashes.
- **preregistration.json:** definitions, primary and secondary universes, signal timing, thresholds, portfolio, costs, benchmarks, acceptance gates, and the commit made before outcomes were read.
- **data_gate.json:** each check, pass/fail, counts, dates, rank coverage, exclusions, source-specific reason.
- **universe_coverage.csv:** date, historical rank, asset/contract IDs, cap fields, eligibility, price/funding coverage, inclusion, exclusion reason.
- **expanding_rank_frontier.json:** cohorts processed, cumulative coverage, complete/incomplete assets, duplicates, errors, last verified rank, next work item.
- **formation_returns.csv:** formation dates, dispersion state, momentum spread, gross/net outcomes, turnover, funding/costs, and matched benchmarks.
- **summary.json:** decision status, primary estimate, uncertainty interval, effective sample, data/baseline gates, cost stresses, placebos, and robustness results.
- **report.md:** methodology, sources/access, universe construction, data boundaries, metrics, limitations, red-team findings, and decision.
- **evidence_inventory.json:** paths, byte counts, and SHA-256 checksums.
- Test logs with commands, exit codes, and exact test results.

Do not publish licensed/private raw datasets, credentials, tokens, signed URLs, private account data, or sensitive runner environment content. If redistribution rights are uncertain, cache raw data outside the public repository and preserve lawful source metadata and hashes.

If blocked, publish the manifest, complete data-gate result, provenance, blocker, and precise next acquisition requirement. Do not fabricate metrics or substitute synthetic observations.

## 10. Decision states

Select exactly one final state:

- **blocked_specification_gate:** the registered estimand cannot be made unambiguous without an outcome-informed choice.
- **blocked_data_gate:** required free point-in-time history, identity mapping, inactive/delisted coverage, or cost inputs cannot be validated.
- **exploratory_only:** a diagnostic ran, but sample size, coverage, power, or chronology is insufficient for confirmation.
- **rejected:** the registered hypothesis fails its predefined economic/statistical criteria, or the gross effect is not tradable after base costs.
- **inconclusive:** evidence is too imprecise, inconsistent, or non-robust to decide.
- **eligible_for_independent_confirmation:** every preregistered data, implementation, baseline, net-performance, inference, and holdout gate passes. This is not deployment approval.

Never select a state based on top-line return or Sharpe alone. A favorable point estimate with a wide interval or tiny effective sample is not a pass.

## 11. Final report format

Lead with a plain-language verdict and selected decision state. Then answer:

1. Did the data gate pass? What is the true usable history?
2. How many assets/contracts and formation dates are in the registered universe? What portion of the descending rank frontier is covered?
3. Does unconditional momentum generate a positive spread before and after costs?
4. What are the high-state, low-state, and high-minus-low forward spreads with confidence intervals?
5. Does the difference survive costs, funding, placebos, rank-band reporting, the alternate cap field, and chronological holdout?
6. What are effective independent sample size and power/minimum detectable effect?
7. What is the strongest adverse or falsifying finding?
8. What evidence would change the decision?
9. Which hypotheses, cost settings, data fields, and rank bands were tested, including negative/incomplete results?
10. What are exact artifact paths, hashes, commit, test commands, and run identifier?

End with exactly these headings:

- SUPPORTED EVIDENCE
- MIXED / INCONCLUSIVE EVIDENCE
- REJECTED / ARCHIVED EVIDENCE
- HIGHEST-VALUE NEXT TEST

No live-trading recommendation is implied.

## 12. Execution discipline and first task

- Start with repository/specification review and free-data access checks; do not start by hunting for the best return.
- Freeze and persist the protocol before computing primary forward outcomes.
- Cache, checkpoint, hash, and verify the descending market-cap universe incrementally; resume idempotently after interruption.
- Continue safe processing after isolated source errors, but disclose missing inputs and block confirmatory inference when the data gate remains incomplete.
- Do not repeat a completed cohort or silently overwrite artifacts. Use stable cohort IDs and content hashes.
- Do not start live systems or place orders. Stay within Market-dispersion-and-momentum-breakdown. Do not change unrelated workflows, schedules, permissions, secrets, or deployment configuration. If a workflow change is required, first document the gap and make only the minimum isolated change needed for a reproducible research run.
- Preserve failures, null findings, deviations, and rejected explanations.
- If a stronger source requires payment, do not buy it. Use another genuinely free source if adequate or stop with a precise blocker.
- Do not claim success before the artifacts, tests, hashes, and gates have been verified.

**First execution objective:** establish the authoritative specification; preregister the exact primary/secondary universe and statistic; and complete the free-data/data-integrity gate. Compute forward momentum-spread outcomes only after the protocol is persisted and the required gates pass.

## 13. Iterative improvement loop for the research agent

Before acting, perform three explicit prompt-review passes and record a short change log in the experiment manifest:

1. **Completeness pass:** identify missing definitions, data fields, chronology, portfolio accounting, deliverables, and acceptance criteria. Resolve only from authoritative source records or an outcome-blind preregistration addendum.
2. **Adversarial pass:** try to falsify the proposed test design by looking for survivorship, look-ahead, universe drift, cost omissions, source licensing issues, multiple testing, small effective sample size, and hidden workflow side effects.
3. **Execution-safety pass:** verify repository scope, free-data access, checkpoint/resume behavior, secret handling, output reproducibility, and that no result-dependent decisions occur before the protocol is frozen.

After each research run, improve the *prompt's clarity and execution controls* using observed process failures, but never retroactively alter the frozen hypothesis, primary statistic, sample split, cost assumptions, or decision thresholds for that same run. Any scientific specification change requires a separately versioned, timestamped, outcome-blind preregistration amendment and a new evaluation identifier. Keep prior prompt versions and experiment artifacts in the destination repository's history; do not erase negative results. If an essential gate fails, stop at that gate, persist the evidence, and report the smallest next step that could resolve it without payment or unauthorized scope expansion.

**Completion discipline:** report the commit SHA and exact prompt path, the data-gate status, tests actually run, and which later phases were or were not executed. A committed prompt is not evidence that the hypothesis was tested.
