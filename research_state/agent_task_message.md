# DELAY-ELIMINATION OVERRIDE — 2026-10-31

Before executing the task below, perform a cheap state-fingerprint check (HEAD + changed paths + existing archive cutoff metadata).

- If code/tests changed since the last verified test run, run affected tests first and the full suite at the milestone.
- If no code/test/data/state changed, skip the full test suite, skip repeated archive probes, do not append another session outcome, and do not update the manifest/frontier/handoffs just to refresh timestamps.
- Resume substantive work only on a new archive publication, a genuinely new free-data source, a state change, or a concrete untested integrity invariant.
- Keep a single event-triggered review; no minute-level polling and no duplicate wakeups.
- The 30-day maturity and sealed-forward-block rules remain mandatory. This override changes only the engineering cadence, not the research protocol.

---

# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Mandate
Continue quantitative research. Historical-only, free-data-only. No live/paper trading. No paid services or secrets.

## Current state (verified 2026-10-31T03:00:30Z)
- Tests: `python3 -m unittest discover -s tests` -> **131 run, 131 OK, 0 failures** (last verified 2026-10-31T01:05Z; skipped this session per override — no code/test/data/state changed). HEAD `8f347e9001d0c9740d100c7283641b853112740a`; `git diff --stat -- artifacts/ research_state/ configs/` empty; working-tree deltas only `__pycache__` bytecode caches. JSON state files parse cleanly and mutually consistent (registry program_status=ACTIVE, manifest program_status=ACTIVE_CONTINUOUS_RESEARCH, frontier status=ACTIVE_INCOMPLETE, candidate_page_cursor=6347; candidates_verified=220, candidates_blocked=6127, candidates_discovered=[]).
- Forward block H004V106 **outcome** byte-unchanged: n_formations 608, high_low_diff_net_1x=+0.6165223953929935, date_first 2025-01-01, date_last 2026-08-31, last_allowed_formation_date 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z, status OK (n_high=61/n_low=90/n_mid=457; HAC t=1.5482, CI [-0.164,1.397] not significant, median -0.0106).
- Binance monthly/daily archives: October 2026 unpublished (404). September 2026 available.
- Cutoff gate: BLOCKED. Canonical forward block H004V106 data_cutoff_utc 2026-09-30T00:00:00Z, last_allowed_formation_date 2026-08-31, n_formations 608, block_sealed=True.
- Manifest boundary/rows/hash check completed against artifacts — no concrete integrity invariant found, nothing to repair.
- DISPERSION-001/002 unchanged (immutable). Phase B placebo red-team present (EXPLORATORY_ONLY). Integrity audits done; defective archive byte-unchanged (development/exploratory evidence only).
- Frontier/catalog exhausted (cursor 6347). Registry: H1 NOT_SUPPORTED_AS_ROBUST_EDGE (immutable). H2-H7, H9 CANDIDATE_UNVALIDATED. H8 EXPLORATORY_ONLY with addenda. Program ACTIVE.

## Priority next actions
1. Verify state quickly per override: `git rev-parse HEAD`, `git diff --stat -- artifacts/ research_state/ configs/`, spot-check JSON files. Confirm forward-block *outcome* fields unchanged (H004V106: n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True).
2. Respect blocker: October 2026 Binance archive unpublished. Keep cutoff BLOCKED; do NOT re-probe. Do not re-run recorded audits. Do not modify frozen artifacts/state/configs.
3. Until next month publishes, no further independent work on frozen data (grid complete, audits complete, catalog exhausted). Complete any bounded, no-cost local task only if a concrete untested integrity invariant is found — first check committed manifests' boundary/rows/hash fields against described artifacts (recurring defect class). No code/test/data/state change → skip full suite per override.
4. When next month publishes: `scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>` only if cutoff >= month-end with that month present. Preregister/evaluate a fresh sealed forward block with HAC/overlap-aware uncertainty, only completed 30-day outcomes; require economic significance + Holm across the 216-cell family before promotion; account for H8 cluster-dominance.
5. Leave clean state; update handoff/registry/manifest/frontier as appropriate. Never wait for a user-provided experiment ID. Program ACTIVE.

## Constraints
Free public data only, historical-only, point-in-time ranks, no forward-fill, no trading, no secrets. Never change DISPERSION-001/002. All cells recorded with reason. No relaxation of 30-day maturity rule; do not open sealed holdout.
" filePath">
research_state/agent_task_message.md