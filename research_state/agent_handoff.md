# Agent Handoff — HARMONY-CRYPTO-EDGE-004

## Program status
- **ACTIVE CONTINUOUS RESEARCH.** Do not pause the program or await a user-supplied experiment ID.
- The authorized scope is this repository, historical research, free data and no-cost tooling only. No paid sources, trading credentials, orders or live/paper deployment.
- Existing DISPERSION-001 and DISPERSION-002 evidence is closed and immutable.

## Verified baseline
- DISPERSION-001: primary result and 72-grid sensitivity results are committed. All 72 grid configurations completed; zero passed the recorded Holm-adjusted p-value threshold below 0.05.
- DISPERSION-002: corrected report says discovery high-minus-low difference +28.77 percentage points, validation +0.79 points, final −0.50 points; the effect did not replicate and state sample sizes were very small.
- A 108-configuration manifest exists for DISPERSION-002, but the committed files inspected for this handoff do not show a matching full grid result ledger. Verify and close this evidence gap; do not claim all 108 configurations were tested solely from the report text.
- Previously committed historical panels cover 28 mapped assets and end on 2024-12-31. The historical rank frontier is not proven exhausted.
- Current next config: configs/dispersion_momentum_grid_v3.json, 216 cells (108 parameter combinations × 2 universe arms); deterministic manifest generator and contract tests included. Manifest regenerated and verified: 216 configurations, 216 unique IDs (H004V001..H004V216), 216 unique hashes; anchors H004V105 (legacy28_comparator) and H004V106 (expanding_point_in_time) confirmed present.

## Completed tasks (this session)
1. **[DONE]** Refreshed free data (`scripts/refresh_free_data.py`): CoinMetrics Community API reachable; market-cap panels extend through 2026-10-23 (latest fully closed UTC daily candle); `universe_frontier.json` current_panel_date_end = 2026-10-23, latest_verified_data_refresh_utc = 2026-10-24T04:31:40Z.
2. **[DONE]** Verified test suite: `python -m unittest discover -s tests` → 40/40 OK.
3. **[DONE]** Verified git status: only `__pycache__` bytecode changed; no changes to DISPERSION-001/002 artifacts. Restored `forward_block_evaluation.json` `evaluated_utc` (reproducibility-test side effect) to the committed value.
4. **[DONE]** Reviewed DISPERSION-003 state: forward block H004V106 sealed per committed artifact (data_cutoff_utc 2026-09-30T00:00:00Z, last_allowed_formation_date 2026-08-31, date range 2025-01-01..2026-08-31, n_formations 608, high_low_diff_net_1x 0.6165, status OK). Committed artifact is the source of truth; handoff text previously recorded a different (-0.0097 / 637 formations / 2026-09-29) figure that does not match the committed file.
5. **[DONE]** Read prior handoff/task and updated handoff + next task message.
6. **[DONE]** Re-ran `scripts/refresh_free_data.py` this session: CoinMetrics Community API reachable; cutoff unchanged at 2026-10-23 (latest fully closed UTC daily candle); `universe_frontier.json` current_panel_date_end = 2026-10-23, latest_verified_data_refresh_utc = 2026-10-24T04:31:40Z. Forward block still BLOCKED (2026-10-23 < 2026-10-29).
7. **[DONE]** Verified test suite: `python -m unittest discover -s tests` → 40/40 OK. Git status: only __pycache__ bytecode; DISPERSION-001/002 artifacts unchanged.
## Blocker record (forward block) — UNRESOLVED
- Next sealed forward block for H004V106 requires formation dates >= 2026-09-30 with a 30-day horizon; need completed UTC observations through at least 2026-10-29.
- Verified data cutoff: 2026-10-23T00:00:00Z. 2026-10-23 < 2026-10-29 → **BLOCKED** (6 days short). Do not compute outcomes prematurely.
- When cutoff >= 2026-10-29 (free data only), evaluate only the preselected anchor H004V106 on the sealed block; no parameter/asset/threshold/cost search.

## Root cause resolution
- Previous blocker (only 6 cap+Binance assets, outer_deciles needs 10+) resolved: universe expanded to 32 assets. Both anchors now evaluable with outer_deciles rule.
- No new candidate discovery needed for the decile gate; 32 assets exceeds the 10-asset minimum.

## Immediate next task
1. **BLOCKER (forward block):** data cutoff 2026-10-23 < required 2026-10-29. Wait for free data to advance (do not force; do not compute prematurely). When cutoff >= 2026-10-29, evaluate only the preselected anchor H004V106 on the sealed forward block (formations >= 2026-09-30, 30-day horizon) without parameter/asset/threshold/cost search. Record the new cutoff in this handoff when evaluated.
2. Frontier expansion: `candidates_discovered` queue empty; frontier cursor=76, 822 eligible candidates, rank_frontier_exhausted=false. Populate `candidates_discovered` only if new verified cap+Binance candidates appear; validate in bounded batches via `scripts/validate_candidate_batch.py`. If none, proceed to integrity checks.
3. Red-team inference, cost/funding attribution, holdout integrity, and resume logic. All 40 tests pass; no failures found, so no new regression tests required this session. Re-run `python -m unittest discover -s tests` after any change.
4. If no candidate passes multiplicity or economic criteria, update hypothesis_registry.json and preregister a new theory-led experiment (H6 is a candidate; next_sequence_number=6).
5. Verify tests, evidence hashes, terminal cell counts and confirm no modifications to DISPERSION-001/002 artifacts; update this handoff and the next task with one concrete measurable action.

## Controls
- Point-in-time universe, no look-ahead, delisting/symbol-migration controls, historical funding/cost accounting, chronological evaluation and free-data-only.
- No fixed top-N universe cutoff; current ranks are discovery only.
- Negative, invalid, incomplete, failed and not-run cells remain in the ledger with explicit reasons.
- A green test or top-performing grid candidate is not evidence of profitability.
- Forward block is sealed: evaluated once for the preselected anchor only; no parameter/asset/threshold/cost search on that block.

## Continuation
The scheduled controller has finite hosted-runner activations and may be interrupted by provider, quota, network or platform failures. Continue through the scheduled recoverable loop and preserve checkpoints; never claim guaranteed uninterrupted uptime for a single process. If any source/phase is blocked, record the blocker and proceed with the next valid source, candidate, test, audit or hypothesis-planning task. Do not stop the research program because an experiment ended.

## Adaptive policy application — immediate next task (2026-10-24)

The adaptive-gate policy now permits bounded exploratory work while preserving confirmatory controls. The previously inspected H004V106 block is development/exploratory evidence, not a new holdout. The next future block still requires the full 30-day horizon and must not be computed before the declared cutoff reaches 2026-10-29.

**Immediate measurable task:** independently audit the canonical sealed artifact at `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json` against its formation ledger, hashes, grid/config manifest and state-classification code. Independently recalculate finite-value counts, high/low/mid state counts, mean/median spread, outlier influence and the reported high-minus-low difference; inspect whether each value is dimensionless return or percentage points; calculate uncertainty with overlapping-window dependence addressed. Compare to the archived defective artifact without modifying either source artifact. Persist a *new* integrity-audit artifact/report and update the hypothesis registry only after the discrepancy is resolved transparently.

After that audit, a reversed/positive-direction hypothesis requires a new ID and preregistration; historical outcomes already inspected may be used only for exploratory development. Use a fresh sealed future block for confirmation after the maturity date. Do not lower the 30-day outcome maturity rule or run a new parameter search on an inspected holdout. If further rank expansion is infeasible, use a separately versioned exploratory analysis over the already verified point-in-time eligible set and state the narrower population explicitly; never call current ranks historical truth. Preserve DISPERSION-001/002 and all current artifacts unchanged.

