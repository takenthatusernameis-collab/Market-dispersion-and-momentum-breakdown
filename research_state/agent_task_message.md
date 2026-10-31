# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-10-31T04:02:26Z)

## Mission
Advance the program with verifiable artifacts. Historical-only, free-data-only. No live/paper trading, no paid services/secrets.

## Verified state (this session, 2026-10-31T04:02:26Z)
- HEAD: 9433309aa3a600f4704911e2d3f2b4f18f184686 | diff(stat) -- artifacts/ research_state/ configs/ scripts/ tests/: empty (only __pycache__) | tests 131/131 OK
- hypothesis_registry: ACTIVE | run_manifest: ACTIVE_CONTINUOUS_RESEARCH | universe_frontier: ACTIVE_INCOMPLETE, cursor 6347, candidates_discovered []
- H004V106 (canonical forward block): recomputed from sealed input JSON — n_formations 608, high_low_diff_net_1x 0.616522395393 (+0.6165223953929935), date_last/last_allowed 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z (n_high 61/n_low 90/n_mid 457; all spread_net_1x finite; HAC t~1.55, CI [-0.164,1.397] not significant). Outcome fields byte-unchanged.
- Cutoff gate: BLOCKED (October 2026 Binance archive unpublished; did NOT re-probe).
- H1 NOT_SUPPORTED_AS_ROBUST_EDGE (immutable). H2-H7,H9 CANDIDATE_UNVALIDATED. H8 EXPLORATORY_ONLY. DISPERSION-001/002 immutable. Frontier/catalog exhausted (cursor 6347). Manifest boundary/rows invariant pinned by tests/test_binance_manifest_provenance.py (4 tests pass within the 131). No new invariant found → no code/test/data/state change.

## Priority action
1. Quick state check (git rev-parse HEAD, git diff --stat, JSON parse). Confirm H004V106 outcome unchanged (n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True).
2. Respect BLOCKED cutoff; do not re-probe October archive.
3. No re-run of recorded audits; do not modify frozen artifacts/state/configs.
4. If any concrete untested integrity invariant exists, fix only if bounded/no-cost with tests added; else do nothing. Check committed manifests' boundary/rows/hash fields against described artifacts first (recurring class — already pinned and passing).
5. When next month publishes: refresh with `scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>` only if cutoff>=month-end present, preregister fresh sealed forward block (30d maturity) under a new registry experiment ID (allocate from hypothesis_registry next_sequence_number), HAC/overlap-aware, require economic significance + Holm across family, account for H8 cluster-dominance.
6. Update handoff/registry/manifest/frontier as appropriate. Never wait for a user-provided experiment ID.

Never shorten 30-day maturity, inspect sealed holdout, change DISPERSION-001/002, relax costs, call paid services.
