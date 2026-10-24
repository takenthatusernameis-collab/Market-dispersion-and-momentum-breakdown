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
3. **[DONE]** Validated first candidate batch of 25 non-legacy assets: 4 verified (1inch, aave, ach, agld with CapMrktEstUSD + Binance perpetual), 21 blocked (no cap data and/or no Binance perpetual). Persisted in universe_frontier.json (candidate_page_cursor=50; 822 total eligible candidates). Added 4 verified candidates to refresh_free_data.py ASSETS/SYMBOL_MAP. Regenerated marketcap_panel.csv (46 assets, 47414 rows).
4. **[DONE]** DISPERSION-003 grid evaluation complete: 216 cells evaluated — 54 OK, 162 BLOCKED, 0 FAILED, 1 Holm-rejected (H004V016). All 54 OK cells are expanding_point_in_time arm with trailing_window_median_split rule. All 162 blocked cells reason="no_formations_passed_data_gate" (all 108 legacy28_comparator cells + 54 expanding cells with trailing_window_outer_deciles rule). Both anchors BLOCKED: H004V105 (legacy, outer_deciles, only 2 assets) and H004V106 (expanding, outer_deciles, only 6 max eligible assets). Grid results in artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/grid_result_ledger.json and grid_summary.json.

## Grid results summary
- Status: 54 OK / 162 BLOCKED / 0 FAILED / 1 Holm-rejected
- All OK cells: expanding_point_in_time arm, trailing_window_median_split rule, n_formations 671-717, high_low_diff_gross range approx -0.146 to +0.096
- All blocked cells: no_formations_passed_data_gate
- Root cause for blockers: trailing_window_outer_deciles requires 10+ eligible assets per date; only 6 assets have both market cap data AND Binance perpetual funding data (btc, eth, 1inch, aave, ach, agld). Legacy arm has only 2 (btc, eth). Median split (needs 4+) works; deciles (needs 10+) does not.
- Anchor blocking means pre-2025 forward-block anchor evaluation cannot proceed until universe breadth reaches 10+ cap+Binance assets.

## Immediate next task
1. Discover and validate more candidate assets with both CoinMetrics CapMrktEstUSD data AND Binance perpetual futures, targeting 4+ additional assets to reach 10+ total (minimum for decile-based dispersion). Use universe_frontier.json (cursor=50, 21 blocked candidates, 822 total eligible) as the discovery source.
2. Re-run the DISPERSION-003 grid with the expanded universe so both anchors (H004V105, H004V106) can be evaluated with outer_deciles rule.
3. Evaluate the single primary anchor (H004V106) on the forward block beginning 2025-01-01 only; never search parameters on that block.
4. Freeze the exact future data cutoff and hashes before outcomes are viewed.
5. Update hypothesis_registry.json and preregister a new theory-led experiment if no candidate passes.
6. Verify tests, evidence hashes, terminal cell counts and no modifications to DISPERSION-001/002 artifacts; update this handoff and the next task with a measurable action.

## Controls
- Point-in-time universe, no look-ahead, delisting/symbol-migration controls, historical funding/cost accounting, chronological evaluation and free-data-only.
- No fixed top-N universe cutoff; current ranks are discovery only.
- Negative, invalid, incomplete, failed and not-run cells remain in the ledger with explicit reasons.
- A green test or top-performing grid candidate is not evidence of profitability.

## Continuation
The scheduled controller has finite hosted-runner activations and may be interrupted by provider, quota, network or platform failures. Continue through the scheduled recoverable loop and preserve checkpoints; never claim guaranteed uninterrupted uptime for a single process. If any source/phase is blocked, record the blocker and proceed with the next valid source, candidate, test, audit or hypothesis-planning task. Do not stop the research program because an experiment ended.