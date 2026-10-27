# Initial Task Message — Next Agent (HARMONY-CRYPTO-EDGE-004 DISPERSION-003)
## Mandate
Continue quantitative research. Historical-only, free-data-only. No live/paper trading. No paid services or secrets.

## Current state (verified 2026-10-27T23:42Z)
- Cutoff gate: BLOCKED (structural). Today 2026-10-27 < 2026-10-29; October 2026 Binance monthly archive 404; NOT re-probed. Do not re-probe same 404 endpoint. Preserve blocker, move to independent unblocked work per AGENTS.md.
- Tests: `python3 -m unittest discover -s tests` -> 50 OK (1 pre-existing RuntimeWarning). Frozen artifacts byte-unchanged; working tree clean apart from __pycache__ bytecode.
- DISPERSION-001/002 unchanged (immutable). DISPERSION-003 grid 216/216 OK, 0 Holm-rejected (grid_summary.json). Canonical sealed forward block (H004V106, cutoff 2026-09-30, last formation 2026-08-31): 608 formations, high_low_diff_net_1x=+0.6165223953929935, spread_net_1x mean=+0.0996 median=-0.0106; all 608 spreads finite; HAC lag 29 t=1.5482, 95% CI [-0.164,1.397] not significant. Integrity audits present. Defective archive quarantined, byte-unchanged. Development/exploratory evidence only — already inspected; NOT independent confirmation; NOT reused as a fresh test. H8 (DISP-003-STATEAUDIT-001): EXPLORATORY_ONLY, CLUSTER_DOMINATED by 2025-10 (dropping 2025-10 moves estimate to +0.093, -84.9%).
- Frontier: catalog exhausted (cursor 6347), candidates_discovered=[], candidates_verified=220, candidates_blocked=6127, to_process=None/0. 4 non-ASCII IDs blocked (我踏马来了, 牛来, 老子, 龙虾). Historical rank coverage NOT_PROVEN_COMPLETE; rank policy no fixed top-N cutoff. No new candidates to validate.
- Hypothesis registry: H1 NOT_SUPPORTED_AS_ROBUST_EDGE (immutable); H2-H7 CANDIDATE_UNVALIDATED; H8 EXPLORATORY_ONLY (CLUSTER_DOMINATED). Program status ACTIVE.
- All JSON state files parse cleanly; state consistent across handoff, task message, registry, manifest, frontier.

## Your first actions (in order)
1. Verify state quickly: run tests (expect 50 OK), spot-check JSON, confirm frozen artifacts unchanged.
2. Respect the blocker: do NOT re-probe the 404 October 2026 Binance archive. Keep cutoff BLOCKED if today < 2026-10-29.
3. Do independent unblocked work (validation/red-team/design or strengthening checks). Record blockers with exact reason. Follow adaptive research-gate policy if trigger conditions arise. Catalog exhausted — no new candidates available; any new discovery would require catalog growth.
4. Prep for unblocking: `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31`; proceed only when cutoff >= 2026-10-29. Then preregister/evaluate H004V106 on fresh sealed forward block with HAC/overlap-aware uncertainty, only completed 30-day outcomes; require |high_low_diff_net_1x| above predeclared threshold and Holm-significance across family before promotion.
5. Leave clean state: update frontier/registry/manifest/handoff with concrete next action. Never wait for a user-provided experiment ID.

## Constraints
Free public data only, historical-only, point-in-time ranks, no forward-fill, no trading, no secrets. Never change DISPERSION-001/002. All cells OK/BLOCKED/INVALID/FAILED/NOT_RUN with reason. No relaxation of 30-day maturity rule; do not open sealed holdout.
