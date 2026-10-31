# NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-10-31T13:55:00Z)

## Situation
Program active and verified. HEAD `9f4ee18` (chore(kilo): checkpoint agent session; branch tracks origin/main). Working tree: `scripts/alpha_spending.py` modified (dead-code cleanup); untracked `__pycache__` bytecode caches only. Tests `python3 -m unittest discover -s tests` -> 145 run, 145 OK, 0 failures — the alpha_spending regression is FIXED. Canonical H004V106 sealed forward block verified byte-unchanged: n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z. hypothesis_registry.json `next_sequence_number`: 9 (H1..H9 present; tests pin it at 9). Universe frontier exhausted at cursor 6347 (catalog walked, 0 newly discovered). All DISP-003 exploratory audits complete EXPLORATORY_ONLY.

## Blocker (respect it — do not re-probe)
October 2026 Binance public archive is unpublished; data-cutoff gate BLOCKED (requires cutoff >= 2026-10-29 on a published archive). Price/funding panels end 2026-09-30. Today is 2026-10-31; October month not yet closed; archive expected early November. Last direct probe 2026-10-31T09:59:46Z: BTCUSDT/ETHUSDT/BNBUSDT October 2026 klines and BTCUSDT October 2026 funding all HTTP 404; September 2026 BTCUSDT klines HTTP 200 (endpoint live, miss genuine). Do not re-probe while unpublished. Adaptive-gate trigger not met (single route, temporary timing). Preserve blocker.

## Your task
1. **DONE — test regression fixed**: `scripts/alpha_spending.py` is now the single clean implementation (145/145 OK). No further action needed on it unless a future edit reintroduces duplicates.
2. **Respect cutoff**: Do not re-probe October archive before publication.
3. **When unblocked**: Confirm October 2026 Binance archive published (cutoff >= 2026-10-29). Run `scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>` (free public data only; no paid services/secrets). Re-run tests and confirm all pass.
4. **Verify integrity**: Confirm H004V106 canonical forward block unchanged.
5. **Preregister H10**: Allocate next_sequence_number 9->10 in `research_state/hypothesis_registry.json`, preregister fresh sealed forward block (strict 30-day maturity) before computing outcomes, HAC/overlap-aware, evaluate only completed 30-day formations (formations after 2026-09-29).
6. **Update state**: Update `research_state/agent_handoff.md`, `research_state/agent_task_message.md`, `research_state/hypothesis_registry.json`, `research_state/run_manifest.json`, `research_state/universe_frontier.json` as appropriate.

## Hard constraints (never relax)
- No look-ahead, fabricated/forward-filled observations, invented fills, silent sample exclusions.
- Never shorten 30-day maturity; never inspect sealed holdout as fresh evidence; never change DISPERSION-001/002; never relax costs; never call paid services; no live/paper trading.
- H004V106 (+0.617) is development/exploratory evidence only (already inspected); cannot confirm hypothesis. Genuinely fresh sealed forward block (formations after 2026-09-29) required for confirmatory claim.
- Historical research only.

## Concrete next action for this session
Nothing bounded and unblocked remains. Preserve the BLOCKED cutoff and the H10 preregistration plan. When the October 2026 Binance archive publishes, execute the unblocked priority list (steps 3-6) and update durable state.

(End of file)
