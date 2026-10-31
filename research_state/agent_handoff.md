# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-10-31T05:00:01Z)

## Mission
Advance the program with verifiable artifacts. Historical-only, free-data-only. No live/paper trading, no paid services/secrets.

## Verified state
- HEAD: 8c8b100094974807b73dfa2615a64b69331f7d23 | tests 135/135 OK
- hypothesis_registry: ACTIVE | run_manifest: ACTIVE_CONTINUOUS_RESEARCH | universe_frontier: ACTIVE_INCOMPLETE, cursor 6347
- H004V106 canonical forward block outcome byte-unchanged (n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff 2026-09-30).
- Cutoff gate: BLOCKED (October 2026 Binance archive unpublished; do NOT re-probe).

## Priority action
1. Quick state check (git rev-parse HEAD, git diff --stat, JSON parse). Confirm H004V106 outcome unchanged.
2. Respect BLOCKED cutoff; do not re-probe October archive.
3. If any concrete untested integrity invariant exists, fix only if bounded/no-cost with tests; else do nothing.
4. When next month publishes: refresh with `scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>` only if cutoff>=month-end present, preregister fresh sealed forward block (30d maturity) under new registry experiment ID, HAC/overlap-aware.
5. Update handoff/registry/manifest/frontier as appropriate. Never wait for a user-provided experiment ID.

Never shorten 30-day maturity, inspect sealed holdout, change DISPERSION-001/002, relax costs, call paid services.
" filePath">
research_state/agent_task_message.md