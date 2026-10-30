# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003
## Mandate
Continue quantitative research. Historical-only, free-data-only. No live/paper trading. No paid services or secrets.

## Current state (verified 2026-10-30T06:41:38Z)
- Tests: `python3 -m unittest discover -s tests` -> 98 run (97 OK + 1 pre-existing mtime-guard failure on frozen formation_returns_conditioned.csv; content unchanged per git diff). Frozen artifacts byte-unchanged. JSON state files parse cleanly and mutually consistent (hypothesis_registry.json, run_manifest.json, universe_frontier.json). Working tree clean apart from `__pycache__`.
- Cutoff gate: BLOCKED (archive). Binance monthly series date_last = 2026-09-30; October 2026 archive still unpublished. Do NOT re-probe — repeat of same failed endpoint is not a distinct attempt.
- DISPERSION-001/002 unchanged. Phase B placebo red-team present (EXPLORATORY_ONLY). Canonical forward block H004V106 (608 formations, block 2025-01-01..2026-08-31): high_low_diff_net_1x=+0.6165, HAC t=1.5482, 95% CI [-0.164,1.397] not significant, median -0.0106. Integrity audits all done: TAIL_ROBUST (LOO/trim/winsorize below thresholds), cluster bootstrap CI [-0.118,1.143] includes zero (EXPLORATORY_ONLY), temporal stability sign not temporally stable (EXPLORATORY_ONLY), forward-block integrity (independent recomputation matches), state representativeness CLUSTER_DOMINATED by 2025-10 (H8 EXPLORATORY_ONLY), REGIME-001/002 read-only EXPLORATORY_ONLY. Defective archive byte-unchanged; development/exploratory evidence only, not fresh confirmation.
- Frontier/catalog: exhausted (cursor 6347), candidates_discovered=[], candidates_verified=220, candidates_blocked=6127. No new candidates to validate; catalog growth required for new discovery.
- Registry: H1 NOT_SUPPORTED_AS_ROBUST_EDGE (immutable). H2-H7, H9 CANDIDATE_UNVALIDATED. H8 EXPLORATORY_ONLY with addenda. Program ACTIVE.

## Priority next actions
1. Verify state quickly: run tests (expect 98 run, 97 OK + 1 pre-existing mtime-guard failure on frozen formation_returns_conditioned.csv). Spot-check JSON state files; confirm frozen artifacts unchanged (`git diff --stat -- artifacts/ research_state/ configs/` empty).
2. Respect blocker: October 2026 Binance archive unpublished (date_last 2026-09-30). Keep cutoff BLOCKED; do NOT re-probe again — repeat of same failed endpoint is not a distinct attempt.
3. Do not re-run recorded audits (TAIL_ROBUST, cluster bootstrap, temporal stability, REGIME-001/002, state representativeness, forward-block integrity). All prior audits under `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/` with scripts/tests.
4. Until October 2026 publishes, no further independent work is available on frozen data: grid (216/216 OK, 0 Holm-rejected), placebo red-team, all audits, registry and frontier are complete. Record this durable blocker with exact reason; follow adaptive research-gate policy if trigger conditions arise. Catalog exhausted — no new candidates available; any new discovery requires catalog growth.
5. When October 2026 publishes, re-check via `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31`; proceed only if cutoff >= 2026-10-29 with October data present. Then preregister/evaluate H004V106 on a fresh sealed forward block with HAC/overlap-aware uncertainty, only completed 30-day outcomes; require |high_low_diff_net_1x| above predeclared economic significance threshold and Holm-significance across the cell family before promotion. Account for cluster-dominance (H8).
6. Leave clean state: update frontier/registry/manifest/handoff with concrete next action. Never wait for a user-provided experiment ID.

## Constraints
Free public data only, historical-only, point-in-time ranks, no forward-fill, no trading, no secrets. Never change DISPERSION-001/002. All cells OK/BLOCKED/INVALID/FAILED/NOT_RUN with reason. No relaxation of 30-day maturity rule; do not open sealed holdout.
