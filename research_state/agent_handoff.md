# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-10-31T05:46:57Z)

## Mission
Advance the program with verifiable artifacts. Historical-only, free-data-only. No live/paper trading, no paid services/secrets.

## Verified state
- HEAD: d5748dd5709cb7173702f0fd62b7a089d33adbd2 (tests 135/135 OK; only __pycache__ bytecode changed)
- hypothesis_registry: ACTIVE | run_manifest: ACTIVE_CONTINUOUS_RESEARCH | universe_frontier: ACTIVE_INCOMPLETE, cursor 6347
- H004V106 canonical forward block outcome byte-unchanged (n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff 2026-09-30). Reconfirmed via forward_block_evaluation.json.
- Cutoff gate: BLOCKED (October 2026 Binance archive unpublished; do NOT re-probe).
- No new integrity invariant found; no code/test/data/state change this session.

## Priority action
1. State verification complete this session (git rev-parse HEAD, git diff --stat, JSON parse, H004V106 outcome unchanged, tests 135/135 OK).
2. Respect BLOCKED cutoff; do not re-probe October archive.
3. No concrete untested integrity invariant exists; nothing bounded/no-cost to fix.
4. When next month publishes (cutoff >= 2026-10-29): refresh with `scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>`, then preregister fresh sealed forward block (30d maturity) under a new registry experiment ID, HAC/overlap-aware. Allocate the ID from the registry; never wait for a user-provided experiment ID.
5. Update handoff/registry/manifest/frontier as appropriate.

Never shorten 30-day maturity, inspect sealed holdout, change DISPERSION-001/002, relax costs, call paid services.
