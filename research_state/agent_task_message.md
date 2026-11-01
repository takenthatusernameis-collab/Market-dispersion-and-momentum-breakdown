## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-11-01T06:31Z)

## Situation
Working tree clean of source changes (only __pycache__ bytecode). Full suite `python3 -m unittest discover -s tests` -> 161 run, 161 OK, 0 failures (verified 2026-11-01T06:31Z). Canonical H004V106 sealed forward block verified byte-unchanged: n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z. `research_state/hypothesis_registry.json` next_sequence_number: 9 (H1..H9 present). Frontier exhausted at cursor 6347. All DISP-003 exploratory audits complete EXPLORATORY_ONLY; none unlock confirmatory track. Frozen artifacts untouched.

## Status change: cutoff UNBLOCKED
Cutoff probe 2026-11-01T06:30Z shows October 2026 Binance archive now published: cutoff_gate UNBLOCKED, gate_met_by_month_end true. Previous BLOCKED state resolved. Adaptive-gate trigger no longer relevant for cutoff.

## Your task (execute now that unblocked)
1. Confirm publication: October 2026 BTCUSDT klines/funding return HTTP 200 (positive control already in probe record).
2. Run `scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>` (free public data only; no paid services/secrets).
3. Re-run `python3 -m unittest discover -s tests` and confirm all pass.
4. Verify integrity: H004V106 canonical forward block unchanged (n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z).
5. Preregister H10: allocate `next_sequence_number` 9->10 in `research_state/hypothesis_registry.json`, preregister fresh sealed forward block (strict 30-day maturity, formations after 2026-09-29) before computing outcomes, HAC/overlap-aware, evaluate only completed 30-day formations.
6. Update `research_state/agent_handoff.md`, `research_state/agent_task_message.md`, `research_state/hypothesis_registry.json`, `research_state/run_manifest.json`, `research_state/universe_frontier.json` as appropriate.

## Hard constraints (never relax)
- No look-ahead, fabricated/forward-filled observations, invented fills, silent sample exclusions.
- Never shorten 30-day maturity; never inspect sealed holdout as fresh evidence; never change DISPERSION-001/002; never relax costs; never call paid services; no live/paper trading.
- H004V106 (+0.6165) is development/exploratory evidence only (already inspected); cannot confirm hypothesis. Genuinely fresh sealed forward block (formations after 2026-09-29) required for confirmatory claim.
- Historical research only.

## Concrete next action for this session
Execute steps 1-6 now that cutoff is UNBLOCKED. Start with confirming publication and running refresh script. Then update durable state.