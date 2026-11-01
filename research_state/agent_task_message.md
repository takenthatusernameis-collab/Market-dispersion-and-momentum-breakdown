## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-11-01T08:30Z)

## Situation
Working tree clean of source changes (only __pycache__ bytecode plus append-only probe records). Full suite `python3 -m unittest discover -s tests` -> 161 run, 161 OK, 0 failures (verified 2026-11-01T08:30Z, EXIT=0). Canonical H004V106 sealed forward block verified byte-unchanged: n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z. `research_state/hypothesis_registry.json` next_sequence_number: 9 (H1..H9 present). Frontier exhausted at cursor 6347. All DISP-003 exploratory audits complete EXPLORATORY_ONLY; none unlock confirmatory track. Frozen artifacts untouched.

## Status: cutoff gate BLOCKED (re-verified)
Latest probe (`python3 scripts/probe_cutoff_gate.py --probe-month 2026-10`, record `research_state/cutoff_probe/cutoff_probe_20261101T083033Z.json`, EXIT=1): October 2026 monthly BTCUSDT klines AND monthly fundingRate endpoints both return HTTP 404; September 2026 control returns HTTP 200 (archive alive, miss is genuine). Daily partial endpoints return 200 but are NOT consumed by `refresh_free_data.py`. `target_published: false`, `cutoff_gate: BLOCKED`. Probe requires both monthly klines and monthly funding endpoints HTTP 200.

Note: test suite output may show mock `"cutoff_gate": "UNBLOCKED"` from `tests/test_cutoff_probe.py:138` — not a network result. Adaptive-gate trigger NOT met.

## Your task (gated; do not execute refresh while BLOCKED)
1. Preserve BLOCKED cutoff. Do NOT run `scripts/refresh_free_data.py` or preregister H10 while October 2026 monthly archives unpublished.
2. Monitor for October 2026 Binance archive publication (monthly klines + monthly fundingRate for BTCUSDT/ETHUSDT return HTTP 200; cutoff >= 2026-10-29). Re-confirm with `python3 scripts/probe_cutoff_gate.py --probe-month 2026-10` (expect EXIT=0 / UNBLOCKED only when monthly endpoints 200 and control 200).
3. Once UNBLOCKED: run `scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>` (free public data only).
4. Re-run `python3 -m unittest discover -s tests` and confirm all pass.
5. Verify integrity: H004V106 canonical forward block unchanged (n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z).
6. Preregister H10: allocate `next_sequence_number` 9->10 in `research_state/hypothesis_registry.json`, preregister fresh sealed forward block (strict 30-day maturity, formations after 2026-09-29), before computing outcomes, HAC/overlap-aware, evaluate only completed 30-day formations.
7. Update `research_state/agent_handoff.md`, `research_state/agent_task_message.md`, `research_state/hypothesis_registry.json`, `research_state/run_manifest.json`, `research_state/universe_frontier.json` as appropriate.

## Hard constraints
- No look-ahead, fabricated/forward-filled, invented fills, silent sample exclusions.
- Never shorten 30-day maturity; never inspect sealed holdout as fresh evidence; never change DISPERSION-001/002; never relax costs; never call paid services; no live/paper trading.
- H004V106 is development/exploratory only; cannot confirm hypothesis. Fresh sealed forward block (formations after 2026-09-29) required for any confirmatory claim.
- Historical research only.

## Concrete next action
While cutoff BLOCKED: preserve state. When Oct 2026 Binance monthly archives publish (both klines+funding HTTP 200, cutoff>=2026-10-29), confirm with probe (EXIT=0/UNBLOCKED) and execute steps 3-7.