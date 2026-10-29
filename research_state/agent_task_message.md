# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Mandate
Continue quantitative research. Historical-only, free-data-only. No live/paper trading. No paid services or secrets.

## Current state (verified 2026-10-29T20:46:46Z)
- Tests: `python3 -m unittest discover -s tests` -> 98 run (97 OK + 1 pre-existing mtime-guard failure on frozen formation_returns_conditioned.csv; content unchanged per git diff). Frozen artifacts unchanged.
- JSON state files parse cleanly and consistent (hypothesis_registry.json, run_manifest.json, universe_frontier.json). Hypothesis statuses: H1 NOT_SUPPORTED_AS_ROBUST_EDGE (immutable); H2-H7 CANDIDATE_UNVALIDATED; H8 EXPLORATORY_ONLY (CLUSTER_DOMINATED by 2025-10); H9 CANDIDATE_UNVALIDATED; program status ACTIVE. Frontier cursor 6347, candidates_discovered=[], candidates_verified=220, candidates_blocked=6127, rank_frontier_exhausted=False; rank coverage NOT_PROVEN_COMPLETE.
- Cutoff gate: BLOCKED (archive). October 2026 Binance monthly archive still unpublished (series date_last = 2026-09-30). Do NOT re-probe — repeat of same failed endpoint is not a distinct attempt.
- DISPERSION-001/002 unchanged (immutable). Prior audits recorded (TAIL_ROBUST, cluster bootstrap EXPLORATORY_ONLY, REGIME-001/002 EXPLORATORY_ONLY, H004V106_FORWARD_BLOCK_TEMPORAL_STABILITY_20261029 EXPLORATORY_ONLY). None unlock confirmatory track.
- H004V106 canonical forward block remains development/exploratory evidence only (already inspected), not independent confirmation. Do not reuse as fresh test.
- Catalog exhausted (cursor 6347). No new candidates without catalog growth.

## Concrete next action (priority order)
1. Verify state quickly: run tests (expect 98 run, 97 OK + 1 pre-existing mtime-guard failure). Spot-check JSON state files, confirm frozen artifacts unchanged (`git diff --stat -- artifacts/ research_state/ configs/` empty).
2. Respect blocker: keep cutoff BLOCKED until October 2026 Binance monthly archive publishes (date_last=2026-09-30). No re-probe.
3. Do independent unblocked work (validation/red-team/design or strengthening checks on frozen data). Do not modify DISPERSION-001/002 or sealed artifacts. Record blockers with exact reasons.
4. Follow adaptive research-gate policy if trigger conditions arise. Catalog exhausted — no new candidates without catalog growth.
5. When October 2026 publishes, re-check via `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31`; only proceed when cutoff >= 2026-10-29 with October data present. Preregister/evaluate on a fresh sealed forward block with HAC/overlap-aware uncertainty, only completed 30-day outcomes; require |high_low_diff_net_1x| above predeclared economic threshold and Holm-significance across the cell family before promotion. Account for cluster-dominance (H8).
6. Leave clean state: update frontier/registry/manifest/handoff with concrete next action. Never wait for a user-provided experiment ID.

## Constraints
Free public data only, historical-only, point-in-time ranks, no forward-fill, no trading, no secrets. Never change DISPERSION-001/002. All cells OK/BLOCKED/INVALID/FAILED/NOT_RUN with reason. No relaxation of 30-day maturity rule; do not open sealed holdout.
