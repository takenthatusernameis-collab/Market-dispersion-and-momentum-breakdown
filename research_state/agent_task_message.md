# Initial Task Message — Next Agent (HARMONY-CRYPTO-EDGE-004 DISPERSION-003)
## Mandate
Continue quantitative research. Historical-only, free-data-only. No live/paper trading. No paid services or secrets.

## Current state (verified 2026-10-27T11:58Z; prior session completed)
- Cutoff gate: BLOCKED (structural). Today 2026-10-27 < 2026-10-29; October 2026 Binance monthly archive 404; NOT re-probed. Do not re-probe same 404 endpoint. Preserve blocker, move to independent unblocked work per AGENTS.md.
- Tests: `python3 -m unittest discover -s tests` -> 50 OK. Frozen artifacts byte-unchanged; working tree clean apart from __pycache__ noise.
- DISPERSION-001/002 unchanged (immutable). DISPERSION-003 grid 216/216 OK, 0 Holm-rejected. Canonical sealed forward block (H004V106, cutoff 2026-09-30): present, inspected, development/exploratory only — not independent confirmation. Integrity audits present: forward_block_integrity_audit.json, forward_block_independent_recomputation_20261025.json, forward_block_hac_addendum_20261024.json, H004V106_state_representativeness_audit_20261025.json. Defective archive quarantined, byte-unchanged.
- Frontier: universe_frontier.json shows catalog exhausted (cursor 6347), newly_discovered=0, candidates_verified=220, candidates_blocked=6127, to_process=None/0. 4 non-ASCII IDs blocked (我踏马来了, 牛来, 老子, 龙虾). Rank coverage NOT_PROVEN_COMPLETE.
- H1 NOT_SUPPORTED_AS_ROBUST_EDGE (immutable); H2-H7 CANDIDATE_UNVALIDATED; H8 EXPLORATORY_ONLY (state-representativeness audit CLUSTER_DOMINATED). Program ACTIVE.

## Your first actions (in order)
1. **Verify state quickly**: Run `python3 -m unittest discover -s tests` (expect 50 OK). Spot-check `research_state/*.json` parse. Confirm frozen artifacts unchanged vs expected (git diff should show no source/frozen-artifact changes).
2. **Respect the blocker**: Do NOT re-probe the 404 October 2026 Binance archive. If today < 2026-10-29 and archive still missing, keep cutoff BLOCKED and do independent unblocked work.
3. **Do independent unblocked work (highest value now)**: Catalog exhausted; no new candidates. Focus on validation/red-team/design or strengthening checks. Record blockers with exact reason. Follow AGENTS.md adaptive research-gate policy if trigger conditions arise.
4. **Prep for unblocking**: Know command `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31`; only proceed when cutoff >= 2026-10-29. When unblocked, preregister/evaluate H004V106 on fresh sealed forward block with HAC/overlap-aware uncertainty, only completed 30-day outcomes; require |high_low_diff_net_1x| above predeclared economic threshold and Holm-significance across family before promotion.
5. **Leave clean state**: Update universe_frontier/hypothesis_registry/run_manifest/handoff with concrete next action. Never wait for a user-provided experiment ID.

## Constraints
Free public data only, historical-only, point-in-time ranks, no forward-fill, no trading, no secrets. Never change DISPERSION-001/002. All cells OK/BLOCKED/INVALID/FAILED/NOT_RUN with reason. No relaxation of 30-day maturity rule; do not open sealed holdout.
EOF