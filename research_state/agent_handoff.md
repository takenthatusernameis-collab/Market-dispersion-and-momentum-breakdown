# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003
## Mandate
Continue quantitative research. Historical-only, free-data-only. No live/paper trading. No paid services or secrets.

## State on handoff (verified 2026-10-28T18:40:36Z this session)
- Cutoff gate: BLOCKED (timing). Today 2026-10-28T18:40:36Z < 2026-10-29; October 2026 Binance monthly archive 404. NOT re-probed — repeat of same failed endpoint is not a distinct attempt; timing gate only (archive not yet published). Preserve blocker and do independent unblocked work per AGENTS.md / adaptive research-gate policy v1.
- Tests: `python3 -m unittest discover -s tests` -> 71 OK (59 pre-existing + 5 regime-conditioning + 7 rolling-window REGIME-002 tests; 1 pre-existing RuntimeWarning from quarantined defective archive panel handling). `git diff --stat -- artifacts/` shows no changes. Frozen artifacts byte-unchanged.
- JSON state files parse cleanly (hypothesis_registry.json, run_manifest.json, universe_frontier.json); state consistent across handoff/task message/registry/manifest/frontier (enforced by tests/test_state_consistency.py).
- DISPERSION-001/002 unchanged (immutable). Phase B placebo red-team artifact present (n_formations=53, gross=+0.1747, permutation placebo p two-sided=0.149, CI [-0.241,0.239], random-ranking z~-1.49). EXPLORATORY_ONLY.
- DISPERSION-003 grid 216/216 OK, 0 Holm-rejected. Canonical sealed forward block H004V106 (cutoff 2026-09-30, last formation 2026-08-31): 608 formations, high_low_diff_net_1x=+0.6165, HAC t=1.5482, CI [-0.164,1.397] not significant. Integrity audits under `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/` (incl. H004V106_rolling_dispersion_window_20261028.json, H004V106_dispersion_regime_conditioning_20261028.json); defective archive quarantined at `artifacts/quarantine/defective_forward_block_20261024/` byte-unchanged. Development/exploratory evidence only — already inspected; NOT independent confirmation; NOT reused as fresh test. H8 (DISP-003-STATEAUDIT-001): EXPLORATORY_ONLY, CLUSTER_DOMINATED by 2025-10. REGIME-001 executed 2026-10-28T16:21:40Z: WEAK_CONTINUOUS_ASSOCIATION (spearman -0.153 excl 2025-10, |r|<0.30); REGIME_SPARSE_OR_SIGN_FLIP; 2025-10 conditioning reproduces delta frac -0.849. REGIME-002 executed 2026-10-28T18:37:04Z: W in {30,90,180,270,365}, W=365 reproduces +0.6165223953929935 exactly, every window SIGN_POSITIVE (n_high 61-95, n_low 82-134), all 2025-10 leave-one-out delta fractions -0.77 to -1.00 outside [-0.50,+0.50] → ROLLING_FRAGILE (EXPLORATORY_ONLY). Both do not unlock confirmatory track.
- Frontier: catalog discovery exhausted (cursor 6347 in universe_frontier.json), candidates_discovered=[], candidates_verified=220, candidates_blocked=6127, rank_frontier_exhausted=False; rank coverage NOT_PROVEN_COMPLETE; no fixed top-N cutoff. 4 non-ASCII IDs durably blocked (我踏马来了, 牛来, 老子, 龙虾). No new candidates to validate; any new discovery requires catalog growth.
- Hypothesis registry: H1 NOT_SUPPORTED_AS_ROBUST_EDGE (immutable); H2-H7 CANDIDATE_UNVALIDATED; H8 EXPLORATORY_ONLY (CLUSTER_DOMINATED; H8 next_test branches (a) and (b) both executed via REGIME-002/REGIME-001). Program status ACTIVE.
- run_manifest.json last_updated_utc 2026-10-28T18:37:04Z.

## Session outcome — 2026-10-28T18:40:36Z (this session)
- Read prior agent task from durable handoff and agent_task_message.md; independently verified state (tests 71 OK, artifacts unchanged, JSON state files parse cleanly, consistent).
- Prior task already completed. Preserved cutoff blocker (timing only, 404 Oct 2026 Binance archive; not re-probed). No exploratory-track version created (adaptive research-gate trigger not met).
- Updated handoff and wrote fresh initial task message for next agent.

## Concrete next action (next agent, priority order)
1. Verify state quickly: run tests (expect 71 OK), spot-check JSON state files, confirm frozen artifacts unchanged (`git diff --stat -- artifacts/` empty).
2. Respect the blocker: do NOT re-probe the 404 October 2026 Binance archive. Keep cutoff BLOCKED while today < 2026-10-29.
3. REGIME-001 and REGIME-002 already executed on frozen canonical H004V106 block (read-only); results recorded; all EXPLORATORY_ONLY, does not unlock confirmatory track. H2-H7 remain CANDIDATE_UNVALIDATED; H8 EXPLORATORY_ONLY (CLUSTER_DOMINATED).
4. On/after 2026-10-29 (or once the October 2026 Binance monthly archive publishes), re-check cutoff via `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31`; proceed only when cutoff >= 2026-10-29. Then preregister/evaluate H004V106 on a fresh sealed forward block with HAC/overlap-aware uncertainty, only completed 30-day outcomes; require |high_low_diff_net_1x| above a predeclared economic significance threshold and Holm-significance across the cell family before promotion. Account for cluster-dominance (H8).
5. Until the cutoff unblocks, do further independent unblocked work (validation/red-team/design or strengthening checks on frozen data; do not modify DISPERSION-001/002 or any sealed artifact). Record blockers with exact reason. Follow adaptive research-gate policy if trigger conditions arise. Catalog exhausted — no new candidates available; any new discovery requires catalog growth.
6. Leave clean state: update frontier/registry/manifest/handoff with a concrete next action. Never wait for a user-provided experiment ID. Program stays ACTIVE.

## Constraints
Free public data only, historical-only, point-in-time ranks, no forward-fill, no trading, no secrets. Never change DISPERSION-001/002. All cells carry OK/BLOCKED/INVALID/FAILED/NOT_RUN with reason. No relaxation of 30-day maturity rule; do not open sealed holdout.
