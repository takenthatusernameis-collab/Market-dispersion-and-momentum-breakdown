# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-10-31T10:40:54Z)

## Mission
Advance the program with verifiable artifacts. Historical-only, free-data-only. No live/paper trading, no paid services/secrets.

## Verified state (2026-10-31T10:39:09Z)
- HEAD: 5c3f3af (chore(kilo): checkpoint agent session; branch tracks origin/main; only `__pycache__` bytecode caches uncommitted).
- Tests: `python3 -m unittest discover -s tests` -> 135 run, 135 OK, 0 failures (verified this session; deps installed).
- H004V106 canonical forward block verified from disk (artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json): n_formations 608, high_low_diff_net_1x 0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z. Byte-unchanged vs committed artifact; no frozen artifact touched.
- Cutoff gate: BLOCKED (October 2026 Binance archive unpublished). Last direct probe 2026-10-31T09:59:46Z to data.binance.vision for BTCUSDT/ETHUSDT/BNBUSDT October 2026 klines and BTCUSDT October 2026 funding all returned HTTP 404; September 2026 BTCUSDT klines returned HTTP 200 in prior probe. Endpoint live; miss is genuine absence (October month not yet closed). Do not re-probe again while unpublished.
- hypothesis_registry.json next_sequence_number: 9 (H1..H9 present; tests pin next_sequence_number == 9). No new hypothesis allocated this session; H10 pending archive publication.
- No bounded no-cost untested task available. Blocker preserved. Frontier exhausted at cursor 6347 (catalog walked, 0 newly discovered). All DISP-003 exploratory audits complete and EXPLORATORY_ONLY; none unlocks the confirmatory track.
- research_state/hypothesis_registry.json, run_manifest.json, universe_frontier.json unchanged this session.

## Priority action
1. Respect BLOCKED cutoff; do not re-probe October archive while unpublished.
2. When October 2026 Binance archive publishes (cutoff >= 2026-10-29 on a published archive): refresh with `scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>`, then preregister a fresh sealed forward block (30d maturity) under a new registry experiment ID H10 (allocate next_sequence_number 9 -> 10), HAC/overlap-aware, evaluate only completed 30-day formations.
3. Update handoff/registry/manifest/frontier as appropriate.

Never shorten 30-day maturity, inspect sealed holdout, change DISPERSION-001/002, relax costs, call paid services.
