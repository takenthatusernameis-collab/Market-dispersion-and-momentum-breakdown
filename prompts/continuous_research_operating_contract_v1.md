# Continuous Research Operating Contract v1

**Program:** HARMONY-CRYPTO-EDGE-004 — Market Dispersion and Momentum Breakdown  
**Status:** Active continuous research  
**Next planned experiment:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003

## Refined mission

Run an indefinite, resumable cycle of candidate-universe expansion, preregistration, empirical testing, independent validation, falsification and evidence-based next-test selection. The objective is reliable knowledge about whether any dispersion-conditioned cross-sectional momentum rule has a repeatable cost-adjusted effect—not to manufacture a positive backtest.

Within this repository and historical-research boundary, do not wait for a user-provided experiment ID. Allocate unique IDs from the registry, preregister a new config, complete the highest-value unblocked task, and update the durable handoff before ending each session.

## Three prompt-improvement passes before execution

1. **Completeness:** identify missing hypotheses, ranks, data fields, signal timing, accounting, grid axes, inference, gates, artifacts and continuation state.
2. **Adversarial:** search for look-ahead, survivorship, mapping errors, revisions, small-sample inference, silent exclusions, cost/funding omissions, multiplicity leakage and false replication.
3. **Execution and recovery:** verify repository scope, free-source rules, checkpointing, deterministic IDs/hashes, terminal cell coverage, credential hygiene, tests and an executable next task.

Record a short change log in each new preregistration. Improve clarity and implementation controls, but never change a frozen experiment after outcomes are visible.

## Evidence that drives the next actions

- DISPERSION-001's primary estimate was positive for high-minus-low spread, contrary to the registered negative prediction. Its 72-cell sensitivity grid completed but no configuration passed the recorded Holm-adjusted threshold.
- DISPERSION-002's discovery difference was about +28.77 percentage points, but contracted to +0.79 points in validation and −0.50 points in the final split. High/low state samples were too small for strong inference.
- The inspected historical panel covers 28 mapped assets and ends on 2024-12-31. The candidate frontier is not proven exhausted.
- A 108-configuration manifest exists for the follow-up, but no matching complete result ledger was present in the inspected committed artifacts. Verify and close this gap; never assume a grid ran because a report mentions it.

## Immediate sequence

1. Verify branch HEAD, active workflow state, latest tests, candidate frontier and all outstanding gates.
2. Refresh free public historical cap, price and funding data through the latest fully closed UTC daily candle. Record cutoffs, coverage and hashes.
3. Discover candidates beyond the existing 28 mapped assets using historical point-in-time market-cap rank in descending order. Process bounded cohorts for checkpointing only; there is no fixed top-N cutoff.
4. Validate timestamped cap history, asset identity, perpetual contract mapping, price/funding history and listing/delisting lifecycle for every candidate.
5. Freeze DISPERSION-003 preregistration and generate the complete 216-cell manifest in configs/dispersion_momentum_grid_v3.json before calculating forward outcomes.
6. Run the full grid on eligible discovery/validation data, report every result, and apply Holm correction across all 216 cells. Continue even if all results are unfavorable.
7. Seal the forward block beginning 2025-01-01 at an exact fully closed UTC cutoff and evaluate only the frozen anchor on that block. Never tune against that block.
8. Update hypothesis status and form a new mechanistic experiment when useful. No candidate passing is a valid result, not a reason to force a winner.
9. Red-team source coverage, timing, accounting, inference, grid identities, holdout integrity and resume logic. Add regression tests for failures found.
10. Update the candidate frontier, hypothesis registry, run manifest, artifacts and handoff. The next task must be explicit and executable without asking for another experiment ID.

## Universe and data rules

Use only genuinely free public sources with documented access. The current documented source families are Coin Metrics Community API for historical market-cap metrics and Binance Public Data Archive for daily klines and historical funding archives; verify live access and per-field coverage each run.

At each historical formation time, ranks must use a market-cap metric available then. Preserve discovery rank separately from historical rank. Include delisted assets and contract migrations, but never backfill prior to eligibility. Store source, as-of and availability timestamps, units, coverage, mapping, exclusions, checksums and error reasons.

If a candidate is blocked, persist the blocker, apply bounded retry/backoff and continue to other candidates or independent tasks. Do not substitute current rank, synthetic observations, paid data or unverified interpolation.

## Grid rules

DISPERSION-003 contains 216 cells:
- momentum lookback: 14, 30, 60 days;
- forward horizon: 14, 30, 60 days;
- dispersion estimator: population standard deviation or scaled median absolute deviation;
- dispersion reference window: 30, 90, 365 days;
- dispersion state: outer deciles or median split;
- universe arm: legacy28 comparator or expanding point-in-time universe.

Portfolio tails are fixed to top/bottom deciles. IDs are H004V001–H004V216. The primary anchor in the expanding universe is H004V106; the legacy comparator is H004V105. Verify by deterministic generation. The 216 cells form one exploratory multiplicity family. Holm-correct the net 1x endpoint across the whole family; report both directions without choosing a one-sided sign after the fact.

The registered H1 prediction remains negative. A positive result is a separately registered candidate hypothesis, not a retroactive rewrite. The grid can never rescue a failed or inconclusive primary test.

## Recursive evidence feedback

After every completed or blocked phase, explicitly answer:
- What did evidence support, contradict or leave uncertain?
- What alternative explanation is strongest?
- Which data limitation most limits inference?
- Which next test offers the greatest information gain per unit of free compute?
- What outcome would falsify the next candidate?

Track the reverse-sign continuation hypothesis, rank-breadth interaction, continuous dispersion effect, and robust/outlier/risk-neutralized explanations as unvalidated candidates until tested.

## Continuous execution and recovery

- Never write “await a new experiment ID” as the next task.
- Never declare the research program complete because a test, grid, candidate cohort or scheduled activation ended.
- Continue data discovery, source coverage, auditing, tests and fresh preregistration when results are negative or data are blocked.
- Use idempotent checkpoints and exact expected-versus-observed cell counts; preserve interrupted work and resume without duplicate rows.
- Respect hosted job limits and use the scheduled controller to resume. A single hosted process cannot guarantee literal uninterrupted uptime; aim for persistent queued work and recoverable progress.
- The program remains ACTIVE until explicitly stopped by the user.
- No paid services, credentials, live or paper trading, under any circumstances.

## Required artifacts

Each experiment preserves a preregistration and review log, run manifest, frozen config, grid manifest, data gate, evidence/source inventory, universe frontier, one terminal result per expected cell, portfolio accounting ledgers, inference summaries, tests, validation logs and a report.

A completed test must end with verified state and a concrete next action. If a required artifact cannot be produced, record why and proceed with another valid task. Never claim unperformed empirical work is complete.


## Adaptive research-gate policy v1 — default for future work

**Purpose:** prevent repeated feasibility deadlocks without turning weaker evidence into a stronger claim. This policy changes the default way the agent makes progress; it does not rewrite frozen experiments.

### 1. Keep two tracks separate
- **Confirmatory track:** preserve the currently registered hypothesis, sample minimums, history minimums, universe definition, parameter grid, costs, holdout boundaries and acceptance criteria. Never change them in place or retroactively reclassify old evidence.
- **Exploratory track:** when the trigger below is met, automatically create a new uniquely identified version with the smallest feasible change. It may answer a narrower or lower-powered question, but its status must be `EXPLORATORY_ONLY` or `INCONCLUSIVE`; it cannot validate, replace or unlock the frozen confirmatory track.

### 2. Trigger for adaptive relaxation
Start the exploratory track after either (a) three materially distinct, documented attempts spanning at least two independent source families or methodological routes fail to advance the same feasibility gate, or (b) a durable structural impossibility is evidenced by source coverage, terms, schema or sample counts. A repeat of the same failed endpoint is not a distinct attempt. Record route, date, observed response/coverage, exact unmet requirement and why retries are unlikely to help. Do not keep looping on a known failure.

### 3. Relax the least damaging feasibility constraint first
Consider, one at a time: use a smaller *explicitly defined* eligible population; use the verified historical overlap rather than demanding a market-cap rank that is not essential to the mechanism; shorten history for a clearly labeled pilot; reduce grid breadth by testing a frozen anchor first; or run a descriptive/measurement feasibility study before estimating outcomes. Choose based on the estimand and data-generating process, not on which choice improves returns. If more than one dimension changes, state and justify each change in a new version before calculating its outcomes.

### 4. Hard safeguards are never relaxed
No look-ahead, fabricated or forward-filled observations, invented fills, silent sample exclusions, outcome-informed parameters/costs, hidden multiple-testing, reuse of an inspected holdout as fresh confirmation, misleading performance labels, breach of source terms, paid services or compute where prohibited, or live/paper trading. Synthetic fixtures are software tests, never market evidence. A current market-cap snapshot must never be labeled historical point-in-time truth. Do not open an originally sealed holdout to rescue progress; any relaxed study needs a new ID, explicit estimand and correctly labeled data vintage.

### 5. Reporting and promotion
Report all attempted routes and failures, coverage/missingness, sample and independent-cluster counts, changed assumptions, uncertainty, all tried variants, costs and reasons for exclusions. Report effect sizes descriptively if calculable, but do not describe underpowered inference as confirmation. A green workflow or passing tests proves only what the tests cover. Promotion requires the original confirmatory gates on admissible data, a sealed evaluation, complete multiple-testing correction and independent recomputation. If the alternative remains infeasible, say so and move to another independent task.

**Default execution rule:** once the trigger is met, do not merely write another blocker memo. Within the repository's existing authorization, complete the next bounded, no-cost exploratory task and preserve the original blocked status. Do not obtain new permissions, spend money, trigger prohibited workflows, or alter frozen result artifacts to make this possible.

