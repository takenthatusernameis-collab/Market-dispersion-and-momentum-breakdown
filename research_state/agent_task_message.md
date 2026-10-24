# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Mandate
Continue quantitative research in this repository without waiting for a new manual experiment ID. Follow prompts/continuous_research_operating_contract_v1.md and docs/research_protocol.md. Historical-only, free-data-only, no live/paper orders.

## State on handoff
- Tests pass (21/21). DISPERSION-003 grid manifest verified: 216 configs, 216 unique IDs (H004V001..H004V216), 216 unique hashes, anchors H004V105/H004V106 present.
- DISPERSION-001/002 artifacts unchanged and closed/immutable.
- DISPERSION-003 grid evaluation complete: 54 OK / 162 BLOCKED / 0 FAILED / 1 Holm-rejected (H004V016).
- All 54 OK cells: expanding_point_in_time arm, trailing_window_median_split rule (needs 4+ assets, we have 6 max eligible).
- All 162 blocked: no_formations_passed_data_gate. Root cause: trailing_window_outer_deciles requires 10+ eligible assets per date; only 6 assets have both market cap data AND Binance perpetual funding data (btc, eth, 1inch, aave, ach, agld). Legacy arm has only 2 (btc, eth).
- Both anchors BLOCKED: H004V105 (legacy, outer_deciles, 2 assets) and H004V106 (expanding, outer_deciles, 6 max eligible).
- universe_frontier.json: 4 verified candidates (1inch, aave, ach, agld), 21 blocked, candidate_page_cursor=50, 822 total eligible candidates, rank_frontier_exhausted=false.
- marketcap_panel.csv: 46 assets (28 legacy + 18 candidates with cap data), 47414 rows, through 2026-10-23.
- Binance panels available for: btc, eth, 1inch, aave, ach, agld (6 assets total).

## First measurable deliverable
Discover and validate at least 4 additional candidate assets with both CoinMetrics CapMrktEstUSD market cap data AND Binance perpetual futures data, to reach 10+ total assets (minimum for decile-based dispersion). Then re-run the DISPERSION-003 grid so both anchors can be evaluated with the outer_deciles rule.

## Mandatory sequencing
1. Validate prior artifacts are intact. Never overwrite or edit DISPERSION-001 or DISPERSION-002 results.
2. Discover additional candidates from universe_frontier.json (cursor=50 onward). For each candidate: check CoinMetrics CapMrktEstUSD availability (historical point-in-time), check Binance perpetual symbol existence, record blockers per asset.
3. For newly verified candidates, add to refresh_free_data.py ASSETS/SYMBOL_MAP, fetch Binance klines+funding, regenerate marketcap_panel.csv.
4. Re-run scripts/run_dispersion003_grid.py with expanded universe. Target: both anchors H004V105/H004V106 unblocked (eligible_assets_per_date max >= 10).
5. If anchors unblocked, evaluate H004V106 on forward block beginning 2025-01-01 only; never sweep parameters on that block.
6. Freeze future data cutoff and hashes before outcomes are viewed.
7. Update hypothesis_registry.json, frontier, manifests, handoff and next task.

## Continue even when
- result is negative, null, inconclusive or rejected;
- an individual asset has missing data;
- a public endpoint is down or rate-limited;
- an implementation defect is found;
- no parameter configuration passes multiplicity or economic criteria.

Preserve evidence and continue with a justified different task. Never bypass a gate, invent data, select a winner by raw return, or mutate a frozen hypothesis. A blocked phase is not permission to stop unrelated research.

## Definition of done for this activation
Provide verified test output, candidate validation results (newly verified + blocked with reasons), updated marketcap_panel.csv with 10+ cap+Binance assets, re-run grid ledger showing both anchors unblocked (or documented blocker if infeasible), exact artifacts changed, and one next concrete task. Do not declare the program complete.