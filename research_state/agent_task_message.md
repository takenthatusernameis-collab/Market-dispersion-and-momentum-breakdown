# Initial Task Message — Next Agent (HARMONY-CRYPTO-EDGE-004 DISPERSION-003)
## Mandate
Continue quantitative research. Historical-only, free-data-only. No live/paper trading. No paid services or secrets.

## Current state (verified 2026-10-28T06:16:08Z; prior agent task verified complete this session)
- Cutoff gate: BLOCKED (structural). Today 2026-10-28 < 2026-10-29; October 2026 Binance monthly archive 404; NOT re-probed. Do NOT re-probe the same 404 endpoint — a repeat of the same failed endpoint is not a distinct attempt. Preserve blocker and move to independent unblocked work per AGENTS.md / adaptive research-gate policy v1.
- Tests: `python3 -m unittest discover -s tests` -> 59 OK (50 pre-existing + 9 state-consistency checks in tests/test_state_consistency.py; 1 pre-existing RuntimeWarning from quarantined defective archive). Frozen artifacts byte-unchanged; working tree clean apart from __pycache__ bytecode.
- DISPERSION-001/002 unchanged (immutable). DISPERSION-003 grid 216/216 OK, 0 Holm-rejected (grid_summary.json). Canonical sealed forward block (H004V106, cutoff 2026-09-30, last formation 2026-08-31): 608 formations, high_low_diff_net_1x=+0.6165223953929935, spread_net_1x mean=+0.0996 median=-0.0106; all finite; HAC lag 29 t=1.5482, 95% CI [-0.164,1.397] not significant. Integrity audits present in `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/`; defective archive quarantined at `artifacts/quarantine/defective_forward_block_20261024/` — byte-unchanged. Development/exploratory evidence only — already inspected; NOT independent confirmation; NOT reused as a fresh test. H8 (DISP-003-STATEAUDIT-001): EXPLORATORY_ONLY, CLUSTER_DOMINATED by 2025-10 (drop-2025-10 -> +0.093, -84.9%).
- Frontier: catalog discovery exhausted (cursor 6347), candidates_discovered=[], candidates_verified=220, candidates_blocked=6127, rank_frontier_exhausted=False, next_candidate_batch_size=25 (operational checkpoint only, not a research cutoff). Historical rank coverage NOT_PROVEN_COMPLETE; rank policy no fixed top-N cutoff. 4 non-ASCII IDs blocked (我踏马来了, 牛来, 老子, 龙虾). No new candidates to validate; any new discovery requires catalog growth.
- Hypothesis registry: H1 NOT_SUPPORTED_AS_ROBUST_EDGE (immutable); H2-H7 CANDIDATE_UNVALIDATED; H8 EXPLORATORY_ONLY (CLUSTER_DOMINATED). Program status ACTIVE.
- All JSON state files parse cleanly; state consistent across handoff, task message, registry, manifest, frontier (enforced by tests/test_state_consistency.py). research_state/run_manifest.json last_updated_utc 2026-10-28T06:16:39Z.

## Your first actions (in order)
1. Verify state quickly: run tests (expect 59 OK), spot-check JSON state files, confirm frozen artifacts unchanged (git status should show only __pycache__).
2. Respect the blocker: do NOT re-probe the 404 October 2026 Binance archive. Keep cutoff BLOCKED if today < 2026-10-29.
3. Do independent unblocked work (validation/red-team/design or strengthening checks). Record blockers with exact reason. Follow adaptive research-gate policy if trigger conditions arise. Catalog discovery exhausted — no new candidates available; any new discovery would require catalog growth.
4. Prep for unblocking: `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31`; proceed only when cutoff >= 2026-10-29. Then preregister/evaluate H004V106 on a fresh sealed forward block with HAC/overlap-aware uncertainty, only completed 30-day outcomes; require |high_low_diff_net_1x| above a predeclared threshold and Holm-significance across the cell family before promotion. Account for cluster-dominance (H8).
5. Leave clean state: update frontier/registry/manifest/handoff with concrete next action. Never wait for a user-provided experiment ID.

## Constraints
Free public data only, historical-only, point-in-time ranks, no forward-fill, no trading, no secrets. Never change DISPERSION-001/002. All cells OK/BLOCKED/INVALID/FAILED/NOT_RUN with reason. No relaxation of 30-day maturity rule; do not open sealed holdout.
