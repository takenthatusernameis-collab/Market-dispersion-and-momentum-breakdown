# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Mandate
Continue quantitative research in this repository without waiting for a new manual experiment ID. Follow prompts/continuous_research_operating_contract_v1.md and docs/research_protocol.md. Historical-only, free-data-only, no live/paper orders.

## State on handoff
- Tests pass (21/21). DISPERSION-003 grid manifest verified: 216 configs, 216 unique IDs (H004V001..H004V216), 216 unique hashes, anchors H004V105/H004V106 present.
- DISPERSION-001/002 artifacts unchanged and closed/immutable.
- DISPERSION-003 grid evaluation complete: 216 OK / 0 BLOCKED / 0 FAILED / 0 Holm-rejected.
- All 216 cells evaluated on expanded universe (32 cap+Binance assets in expanding arm; 28 in legacy arm).
- Anchor H004V106 (expanding, outer_deciles): n_formations=1339, high_low_diff_net_1x = -0.0600, not Holm-significant.
- Anchor H004V105 (legacy, outer_deciles): n_formations=1339, high_low_diff_net_1x = -0.0698, not Holm-significant.
- Sealed forward block evaluation of H004V106 complete: 2025-01-01 to 2026-09-29, 637 formations, high_low_diff_net_1x = -0.0097 (-0.97pp), same negative sign but small magnitude. Input hashes frozen in artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json.
- Universe expanded to 32 assets with both CoinMetrics CapMrktEstUSD and Binance perpetual data (exceeds 10-asset minimum for decile-based dispersion). Both anchors unblocked with outer_deciles rule.
- universe_frontier.json: candidate_page_cursor=76, 822 total eligible candidates, rank_frontier_exhausted=false, expanding_universe_assets_with_cap_and_binance=32.
- marketcap_panel.csv: 46 assets, 47414 rows, through 2026-10-23.
- hypothesis_registry.json: H1 evidence_note extended with DISPERSION-003 results; H6 candidate added (negative spread persists on forward data at small magnitude, not economically meaningful). next_sequence_number=6.

## First measurable deliverable
Evaluate H004V106 anchor on the next sealed forward block beginning after 2026-09-29 (the current forward block end date). Freeze exact boundaries and input file hashes before computing outcomes. Never search parameters, assets, thresholds, or costs on the forward block.

## Mandatory sequencing
1. Validate prior artifacts are intact. Never overwrite or edit DISPERSION-001 or DISPERSION-002 results.
2. Define the next sealed forward block: start date = day after 2026-09-29 (the last formation date in the current forward block), end date = latest fully closed UTC daily candle. Record exact boundaries and input hashes before computing outcomes.
3. Evaluate only H004V106 (momentum_lookback=30, forward_horizon=30, estimator=cross_sectional_population_stddev, window=365, rule=trailing_window_outer_deciles, arm=expanding_point_in_time) on that block. No parameter/asset/threshold/cost search.
4. Record the result with exact formation date range, n_formations, high/low/mid counts, high_low_diff_gross, high_low_diff_net_1x, eligible_assets_per_date, and all input file SHA-256 hashes.
5. If the forward block end extends beyond 2026-09-29, new data may need to be refreshed (refresh_free_data.py) — only free public sources, record cutoff and provenance.
6. Update hypothesis_registry.json (H6 status, evidence), universe_frontier.json, forward_block artifacts, and this handoff.
7. Verify tests pass (21/21), confirm DISPERSION-001/002 artifacts unchanged, update handoff and next task message.

## Continue even when
- result is negative, null, inconclusive or rejected;
- an individual asset has missing data;
- a public endpoint is down or rate-limited;
- an implementation defect is found;
- no parameter configuration passes multiplicity or economic criteria.

## Definition of done for this activation
Provide verified test output, forward block evaluation result (newly evaluated block with exact boundaries and frozen hashes), updated hypothesis_registry.json and universe_frontier.json, exact artifacts changed, confirmation DISPERSION-001/002 artifacts unchanged, and one next concrete task. Do not declare the program complete.
