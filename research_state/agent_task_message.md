## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-11-01T13:02Z)

## Situation
Working tree clean of source changes (only __pycache__ bytecode plus append-only probe records in `research_state/cutoff_probe/`). Full suite `python3 -m unittest discover -s tests` -> 161 run, 161 OK, 0 failures (verified this session 2026-11-01T13:02Z; EXIT=0). Canonical H004V106 sealed forward block verified byte-unchanged: n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z (`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`). `research_state/hypothesis_registry.json` next_sequence_number 9 (H1..H9 present). Universe frontier exhausted at cursor 6347 (catalog not grown; 0 newly discovered). All DISP-003 exploratory audits complete EXPLORATORY_ONLY; none unlock confirmatory track. Frozen artifacts untouched.

## Status: cutoff gate BLOCKED (preserved; not re-probed this session)
Cutoff gate remains BLOCKED per the last real probe 2026-11-01T13:00:51Z (record `research_state/cutoff_probe/cutoff_probe_20261101T130051Z.json`, EXIT=1): October 2026 monthly BTCUSDT klines HTTP 404 AND monthly fundingRate HTTP 404. `target_published: false` because BOTH monthly endpoints must be HTTP 200 (consumed by `refresh_free_data.py`). September 2026 control HTTP 200 (archive alive, miss genuine). `cutoff_gate: BLOCKED`. Daily partials not consumed. Adaptive-gate trigger NOT met (single route/timing). This session did NOT re-probe — repeating the same October 2026 endpoint ~2 minutes after the last real probe is looping on a known failure.

**Warning:** the test-suite tail prints `"cutoff_gate": "UNBLOCKED"` — that is synthetic mock data from `tests/test_cutoff_probe.py:115-125` (`test_main_returns_zero_when_unblocked` mocks `probe_month` to return synthetic HTTP 200s and mocks `Path.write_text`, so no record is written and no real network call is made), NOT a network result. Do not read it as the gate state. Only `python3 scripts/probe_cutoff_gate.py --probe-month 2026-10` (EXIT=1 = BLOCKED, EXIT=0 = UNBLOCKED) is authoritative.

## Your task (gated)
1. Preserve BLOCKED cutoff. Do NOT run `scripts/refresh_free_data.py` or preregister H10 while October 2026 monthly archives are not published (need BOTH klines AND fundingRate HTTP 200).
2. Do NOT repeatedly re-probe the same October 2026 endpoint (that is looping on a known failure; the adaptive-gate trigger is not met). Re-confirm publication only when there is reason to believe the archive has published.
3. Once UNBLOCKED (probe EXIT=0/UNBLOCKED with both monthly endpoints 200): run `scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>` (free public only).
4. Re-run `python3 -m unittest discover -s tests` (all pass).
5. Verify H004V106 unchanged (608 formations, high_low_diff_net_1x +0.6165223953929935, 2026-08-31, sealed).
6. Preregister H10: allocate next_sequence_number 9->10 in `research_state/hypothesis_registry.json`, fresh sealed forward block (strict 30-day maturity, formations after 2026-09-29), before outcomes, HAC/overlap-aware, only completed 30-day formations.
7. Update `research_state/agent_handoff.md`, `research_state/agent_task_message.md`, `research_state/hypothesis_registry.json`, `research_state/run_manifest.json`, `research_state/universe_frontier.json` as appropriate.

## Hard constraints
- No look-ahead/fabrication/forward-fill/invented fills/silent exclusions/outcome-informed params/costs/hidden multiplicity/reuse of inspected holdout.
- Never shorten 30-day maturity; never change DISPERSION-001/002; never relax costs; no paid services/live/paper trading.
- H004V106 is development/exploratory only; fresh sealed forward block required for confirmatory claim.

## Concrete next action
While BLOCKED: preserve state. When Oct 2026 Binance monthly archives publish (both klines AND fundingRate HTTP 200, cutoff>=2026-10-29), confirm with probe (EXIT=0/UNBLOCKED), execute steps 3-7.
