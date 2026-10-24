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

## Completed tasks
1. **[DONE]** Run unit-test suite and generate_grid_v3_manifest.py; verify 216 unique IDs/hashes and anchors H004V105/H004V106. All tests pass (21/21).
2. **[DONE]** Extended free public price, cap and funding data to latest fully closed UTC daily candle (2026-10-23); provenance recorded in data/panels/data_refresh_provenance.json; 21/21 tests pass.
3. **[DONE]** Validated first candidate batch of 25 non-legacy assets: 4 verified (1inch, aave, ach, agld with CapMrktEstUSD + Binance perpetual), 21 blocked (no cap data and/or no Binance perpetual). Persisted in universe_frontier.json (candidate_page_cursor=76; 822 total eligible candidates). Added 4 verified candidates to refresh_free_data.py ASSETS/SYMBOL_MAP. Regenerated marketcap_panel.csv (46 assets, 47414 rows).
4. **[DONE]** DISPERSION-003 grid evaluation complete: 216 cells evaluated — 216 OK, 0 BLOCKED, 0 FAILED, 0 Holm-rejected. All cells evaluated on expanding universe with 32 cap+Binance assets (legacy arm: 28, expanding arm: 32). Anchor H004V106: 1339 formations, high_low_diff_net_1x = -0.0599, not Holm-significant. Grid results in artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/grid_result_ledger.json and grid_summary.json.
5. **[DONE]** Forward block evaluation of H004V106: sealed block 2025-01-01 to 2026-09-29 (latest fully closed UTC candle frozen at 2026-10-23T00:00:00Z). 637 formations (113 high, 163 low, 361 mid). high_low_diff_gross = -0.0097, high_low_diff_net_1x = -0.0097. Same negative sign as H1 but small magnitude; not an economically meaningful edge. Input file hashes frozen in forward_block_evaluation.json before outcomes were computed. Output at artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json.
6. **[DONE]** Expanded universe to 32 assets with both CoinMetrics CapMrktEstUSD and Binance perpetual data (well past the 10-asset minimum for decile-based dispersion). Both anchors H004V105 and H004V106 now unblocked with outer_deciles rule.
7. **[DONE]** hypothesis_registry.json updated: H1 evidence_note extended with DISPERSION-003 grid and forward block results; new H6 candidate added (negative spread persists on forward data at small magnitude, not economically meaningful). last_updated_utc set.
8. **[DONE]** All 21 tests pass. DISPERSION-001/002 artifacts verified unchanged (git status confirms only DISPERSION-003 artifacts and research state modified).

## Grid results summary
- Status: 216 OK / 0 BLOCKED / 0 FAILED / 0 Holm-rejected
- All cells evaluated on expanded universe (32 cap+Binance assets in expanding arm)
- Anchor H004V106 (expanding, outer_deciles): n_formations=1339, high=516, low=110, high_low_diff_gross=-0.0600, high_low_diff_net_1x=-0.0600, eligible_assets_per_date mean=29.0 max=32
- Anchor H004V105 (legacy, outer_deciles): n_formations=1339, high=516, low=110, high_low_diff_gross=-0.0698, high_low_diff_net_1x=-0.0698, eligible_assets_per_date mean=27.1 max=28
- Neither anchor Holm-rejected. Forward block H004V106: high_low_diff_net_1x = -0.0097.

## Root cause resolution
- Previous blocker (only 6 cap+Binance assets, outer_deciles needs 10+) resolved: universe expanded to 32 assets. Both anchors now evaluable with outer_deciles rule.
- No new candidate discovery needed for the decile gate; 32 assets exceeds the 10-asset minimum.

## Immediate next task
1. Next sealed forward block for H004V106 is blocked until data reaches 2026-10-29 (formation 2026-09-30 needs +30d horizon). Current cutoff 2026-10-23. Record blocker; do not compute outcomes prematurely.
2. Continue candidate frontier expansion beyond the current 32 assets if more cap+Binance assets are discovered; universe_frontier.json cursor=76, 822 total eligible candidates, rank_frontier_exhausted=false.
3. Red-team inference, cost/funding attribution, holdout integrity, and resume logic. Add regression tests for any failures found.
4. If no candidate passes multiplicity or economic criteria, update hypothesis_registry.json and preregister a new theory-led experiment (H6 is a candidate; next_sequence_number=6).
5. Verify tests, evidence hashes, terminal cell counts and no modifications to DISPERSION-001/002 artifacts; update this handoff and the next task with a measurable action.

## Controls
- Point-in-time universe, no look-ahead, delisting/symbol-migration controls, historical funding/cost accounting, chronological evaluation and free-data-only.
- No fixed top-N universe cutoff; current ranks are discovery only.
- Negative, invalid, incomplete, failed and not-run cells remain in the ledger with explicit reasons.
- A green test or top-performing grid candidate is not evidence of profitability.
- Forward block is sealed: evaluated once for the preselected anchor only; no parameter/asset/threshold/cost search on that block.

## Continuation
The scheduled controller has finite hosted-runner activations and may be interrupted by provider, quota, network or platform failures. Continue through the scheduled recoverable loop and preserve checkpoints; never claim guaranteed uninterrupted uptime for a single process. If any source/phase is blocked, record the blocker and proceed with the next valid source, candidate, test, audit or hypothesis-planning task. Do not stop the research program because an experiment ended.
