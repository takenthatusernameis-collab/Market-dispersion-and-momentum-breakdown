## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-11-01T10:09Z)

## Situation
Working tree clean of source changes (only __pycache__ bytecode plus append-only probe records in `research_state/cutoff_probe/`). Full suite `python3 -m unittest discover -s tests` -> 161 run, 161 OK, 0 failures (verified 2026-11-01T10:09Z). `numpy` 2.5.4 present. Canonical H004V106 sealed forward block verified byte-unchanged: n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z. `research_state/hypothesis_registry.json` next_sequence_number 9 (H1..H9 present). Universe frontier exhausted at cursor 6347. All DISP-003 exploratory audits complete EXPLORATORY_ONLY; none unlock confirmatory track. Frozen artifacts untouched.

## Status: cutoff gate BLOCKED (re-verified)
Latest probe (`python3 scripts/probe_cutoff_gate.py --probe-month 2026-10`, record `research_state/cutoff_probe/cutoff_probe_20261101T100911Z.json`, EXIT=1): October 2026 monthly BTCUSDT klines HTTP 404; monthly fundingRate HTTP 200. Probe requires BOTH monthly endpoints (consumed by `refresh_free_data.py`) -> `target_published: false`, `cutoff_gate: BLOCKED`. September 2026 control HTTP 200 (archive alive, miss genuine). Daily partials not consumed. Test suite mock `"cutoff_gate": "UNBLOCKED"` at `tests/test_cutoff_probe.py:138` is not a network result. Adaptive-gate not met.

## Your task (gated)
1. Preserve BLOCKED cutoff. Do NOT run `scripts/refresh_free_data.py` or preregister H10 while October 2026 monthly archives not published (need BOTH klines AND fundingRate HTTP 200).
2. Monitor for October 2026 Binance archive publication. Re-confirm with `python3 scripts/probe_cutoff_gate.py --probe-month 2026-10` (expect EXIT=0/UNBLOCKED only when both monthly endpoints 200).
3. Once UNBLOCKED: `scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>` (free public only).
4. Re-run `python3 -m unittest discover -s tests` (all pass).
5. Verify H004V106 unchanged (608 formations, high_low_diff_net_1x +0.6165223953929935, 2026-08-31, sealed).
6. Preregister H10: allocate next_sequence_number 9->10 in `research_state/hypothesis_registry.json`, fresh sealed forward block (strict 30-day maturity, formations after 2026-09-29), before outcomes, HAC/overlap-aware, only completed 30-day formations.
7. Update `research_state/agent_handoff.md`, `research_state/agent_task_message.md`, `research_state/hypothesis_registry.json`, `research_state/run_manifest.json`, `research_state/universe_frontier.json` as appropriate.

## Hard constraints
- No look-ahead/fabrication/forward-fill/invented fills/silent exclusions/outcome-informed params/costs/hidden multiplicity/reuse of inspected holdout.
- Never shorten 30-day maturity; never change DISPERSION-001/002; never relax costs; no paid services/live/paper trading.
- H004V106 is development/exploratory only; fresh sealed forward block (formations after 2026-09-29) required for confirmatory claim.

## Concrete next action
While BLOCKED: preserve state. When Oct 2026 Binance monthly archives publish (both klines AND fundingRate HTTP 200, cutoff>=2026-10-29), confirm with probe (EXIT=0/UNBLOCKED), execute steps 3-7.
