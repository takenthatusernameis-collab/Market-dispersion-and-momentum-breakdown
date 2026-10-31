# NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-10-31T09:58:19Z)

## Situation
Program active and verified. HEAD `16d00cf` (local checkpoint commit; branch tracks origin/main); only `__pycache__` bytecode caches uncommitted. Tests `python3 -m unittest discover -s tests` -> 135 run, 135 OK, 0 failures (re-verified 2026-10-31T09:21:30Z). Canonical H004V106 sealed forward block verified from disk: n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z. hypothesis_registry.json `next_sequence_number`: 9 (H1..H9 present; tests pin it at 9). Universe frontier exhausted at cursor 6347 (catalog walked, 0 newly discovered).

## Blocker (respect it — do not re-probe)
October 2026 Binance public archive is unpublished; data-cutoff gate BLOCKED (requires cutoff >= 2026-10-29 on a published archive). Price/funding panels end 2026-09-30. Last direct probe 2026-10-31T08:08Z: BTCUSDT/ETHUSDT/BNBUSDT October 2026 klines and BTCUSDT October 2026 funding all HTTP 404; September 2026 BTCUSDT klines HTTP 200 (endpoint live, miss genuine). Do not re-probe while unpublished. No bounded no-cost untested task available; all DISP-003 exploratory audits complete and EXPLORATORY_ONLY. Preserve blocker.

## Your task (once the archive publishes / cutoff unblocks)
1. Confirm October 2026 Binance archive published (cutoff >= 2026-10-29). Do not re-probe before then.
2. Run `scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>` (free public data only; no paid services/secrets).
3. Re-run `python3 -m unittest discover -s tests` and confirm 135 run, 135 OK, 0 failures.
4. Confirm H004V106 canonical forward block unchanged: n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z.
5. Preregister fresh sealed forward block (strict 30-day maturity) under new experiment ID H10: allocate next_sequence_number 9->10 in `research_state/hypothesis_registry.json`, preregister before computing outcomes, HAC/overlap-aware, evaluate only completed 30-day formations.
6. Update `research_state/agent_handoff.md`, `research_state/agent_task_message.md`, `research_state/hypothesis_registry.json`, `research_state/run_manifest.json`, `research_state/universe_frontier.json` as appropriate.

## Hard constraints (never relax)
- No look-ahead, fabricated/forward-filled observations, invented fills, silent sample exclusions.
- Never shorten 30-day maturity; never inspect sealed holdout as fresh evidence; never change DISPERSION-001/002; never relax costs; never call paid services; no live/paper trading.
- H004V106 (+0.617) is development/exploratory evidence only (already inspected); cannot confirm hypothesis. Genuinely fresh sealed forward block (formations after 2026-09-29) required for confirmatory claim.
- Historical research only.

## Concrete next action for this session (none)
No unblocked action available: October 2026 archive unpublished (re-probing forbidden), frontier exhausted, all DISP-003 exploratory audits complete EXPLORATORY_ONLY. State re-verified; registry/manifest/frontier unchanged. When October 2026 Binance archive publishes (cutoff >= 2026-10-29), execute steps 1-6 with H10.
