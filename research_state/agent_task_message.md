# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003
## Mandate
Continue quantitative research. Historical-only, free-data-only. No live/paper trading. No paid services or secrets.

## Current state (verified 2026-10-30T12:28:12Z)
- Tests: `python3 -m unittest discover -s tests` -> **100 run, 100 OK, 0 failures** (numpy/pandas installed per requirements.txt).
- Frozen artifacts byte-unchanged: `git diff --stat -- artifacts/ research_state/ configs/` empty (only `tests/__pycache__` bytecode caches in working tree).
- JSON state files parse cleanly and are mutually consistent (hypothesis_registry.json ACTIVE, run_manifest.json ACTIVE_CONTINUOUS_RESEARCH, universe_frontier.json ACTIVE_INCOMPLETE, cursor 6347).
- Cutoff gate: BLOCKED (archive). Today is 2026-10-30; October 2026 Binance monthly archive still unpublished (Binance series date_last = 2026-09-30; canonical forward block data_cutoff_utc = 2026-09-30T00:00:00Z, last_allowed_formation_date = 2026-08-31). Do NOT re-probe — repeat of same failed endpoint is not a distinct attempt.
- DISPERSION-001/002 unchanged (immutable). Phase B placebo red-team present (EXPLORATORY_ONLY). Canonical sealed forward block H004V106 (608 formations, block 2025-01-01..2026-08-31): high_low_diff_net_1x=+0.6165, HAC t=1.5482, CI [-0.164,1.397] not significant, median -0.0106. Integrity audits all done: TAIL_ROBUST, cluster bootstrap CI includes zero (EXPLORATORY_ONLY), temporal stability sign not stable (EXPLORATORY_ONLY), state representativeness CLUSTER_DOMINATED (H8 EXPLORATORY_ONLY), REGIME-001/002 read-only (EXPLORATORY_ONLY). Defective archive byte-unchanged; development/exploratory evidence only.
- Frontier/catalog: exhausted (cursor 6347), candidates_discovered=[], candidates_verified=220, candidates_blocked=6127. Catalog growth required for new discovery. CoinMetrics community catalog fully walked (6347 entries); no new asset ids remain outside legacy28 ∪ verified ∪ blocked.
- Registry: H1 NOT_SUPPORTED_AS_ROBUST_EDGE (immutable). H2-H7, H9 CANDIDATE_UNVALIDATED. H8 EXPLORATORY_ONLY with addenda. Program ACTIVE.

## Priority next actions
1. Verify state quickly each session: `python3 -m unittest discover -s tests` (expect 100 run, 100 OK). Spot-check JSON files; confirm `git diff --stat -- artifacts/ research_state/ configs/` empty except bytecode caches.
2. Respect blocker: October 2026 Binance archive unpublished (date_last 2026-09-30). Keep BLOCKED; do NOT re-probe.
3. Do not re-run recorded audits (TAIL_ROBUST, cluster bootstrap, temporal stability, REGIME-001/002, state representativeness, forward-block integrity, phase B placebo). Do not modify frozen artifacts/state/configs.
4. Until October publishes: no independent work available on frozen data (grid/audits/placebo/registry/frontier complete). Catalog exhausted. Follow adaptive research-gate policy if triggers arise; do not merely write another blocker memo — complete any bounded, no-cost local task that advances state (tests, consistency checks, documentation).
5. When October publishes: `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31` only if cutoff >= 2026-10-29 with October present. Preregister/evaluate fresh sealed forward block with HAC/overlap-aware uncertainty, only completed 30-day outcomes; require economic significance + Holm across family before promotion; account for H8 cluster-dominance.
6. Leave clean state; update handoff/registry/manifest/frontier as appropriate. Never wait for user-provided experiment ID.

## Constraints
Free public data only, historical-only, point-in-time ranks, no forward-fill, no trading, no secrets. Never change DISPERSION-001/002. All cells recorded with reason. No relaxation of 30-day maturity rule; do not open sealed holdout.
