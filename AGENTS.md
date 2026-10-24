# Agent operating rules

## Mission
Advance the Market Dispersion and Momentum Breakdown research program continuously. Each session must deliver a verifiable artifact, test, source-coverage improvement, evidence audit, candidate evaluation or explicit blocker-resolution attempt.

## Required reading
Read this file, prompts/continuous_research_operating_contract_v1.md, research_state/agent_handoff.md, research_state/agent_task_message.md, docs/research_protocol.md, the active grid config and latest report for any experiment touched.

## Non-negotiable controls
- Free public data only. No paid services/trials/compute, secrets, exchange credentials or non-public endpoints.
- Historical research only. Never place orders or deploy live/paper trading.
- Use point-in-time membership/ranks, contract mapping and listing/delisting status. Today's rank is never historical truth.
- Preserve DISPERSION-001/002 configs, inputs, artifacts and findings. Changed hypotheses, grids or data use new IDs and artifact paths.
- Use completed UTC observations, causal timing, realistic costs/funding and chronological evaluation.
- Record every cell, including negative, null, incomplete, invalid, failed and not-run states with reason.
- Correct for the complete declared multiple-testing family. Do not promote a winner from raw p-values or return alone.
- Keep future evaluation blocks sealed. Never reuse an inspected holdout as independent evidence.
- Never fabricate metrics, silently drop candidates or change grids after seeing outcomes.
- Never wait for a manually supplied experiment ID within this authorized scope. Allocate unique IDs from the registry and preregister first.
- When one cell is blocked, preserve its blocker and continue with other candidates, free-source discovery, tests, validation, design or red-team tasks.
- Keep credentials and sensitive runner output out of files and logs.

## Per-session definition of done
1. Read handoff; pick the highest-priority unblocked action.
2. Make a narrow change with tests or measurable progress.
3. Run applicable checks and record exact commands/outcomes.
4. Inspect the diff; confirm old experiment artifacts are unchanged.
5. Update frontier, registry, manifest and handoff as appropriate.
6. Leave a concrete next action. Never write “wait for a new experiment ID.”

Workflow success is not evidence of an economic edge. One completed experiment does not end the program.


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


### Repository-specific default: market dispersion × momentum
- Do not use the unusual `H004V106` forward-block estimate as a winner until it has been independently recomputed from the exact sealed input hashes and formation ledger. Current canonical artifact: `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`. Preserve it and the defective archive unchanged; create a new audit artifact with reconciliation, finite-value checks, state counts, mean/median, tail influence, cost treatment, overlap-aware uncertainty and independent metric recomputation.
- The current forward block has already been inspected, so it is development/exploratory evidence for any newly formulated hypothesis, never untouched confirmation. Do not repeat its result as a fresh test.
- Once the artifact integrity audit is recorded, preregister any positive-direction or otherwise revised mechanism under a new hypothesis/experiment ID. Use the smallest useful diagnostic first; then use only a genuinely fresh, mature forward block for confirmation. Do not relax the fixed 30-day outcome maturity rule or compute truncated outcomes.
- If historical rank completeness is what prevents additional candidate progress, a new exploratory analysis may use the verified point-in-time eligible assets and state its narrower universe/coverage explicitly; today's ranks must not be backfilled as historical ranks. Preserve the expanding-universe confirmatory arm unchanged.

