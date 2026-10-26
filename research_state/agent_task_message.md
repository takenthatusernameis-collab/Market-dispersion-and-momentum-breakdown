# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003
## Mandate
Continue quantitative research. Historical-only, free-data-only. No live/paper trading. No paid services or secrets.

## Current state (2026-10-26T14:32:00Z)
- Cutoff gate: BLOCKED (structural). Today 2026-10-26 < 2026-10-29; October 2026 Binance monthly archive 404; not re-probed per blocker note. Do not re-probe the same 404 endpoint. Preserve blocker and move to independent unblocked work per AGENTS.md.
- Tests: `python3 -m unittest discover -s tests` -> 50 OK (1 pre-existing RuntimeWarning from quarantined defective archive). git diff shows only universe_frontier.json timestamps + __pycache__; frozen artifacts byte-unchanged.
- DISPERSION-001/002 unchanged; artifacts immutable.
- DISPERSION-003: grid 216/216 OK, 0 Holm-rejected (grid_summary.json). Canonical sealed forward block (H004V106, cutoff 2026-09-30, last formation 2026-08-31): 608 formations, high_low_diff_net_1x=+0.6165223953929935, HAC t~1.55 not significant. Integrity audits present and byte-consistent. Defective archive quarantined. Byte-unchanged.
- H8 (EXPLORATORY_ONLY, DISP-003-STATEAUDIT-001): state-representativeness audit shows canonical H004V106 +0.617 is CLUSTER_DOMINATED by 2025-10 (dropping 2025-10 moves estimate to +0.093; high states in only 7 months). Exploratory only; cannot validate/refute H1/H6/H7 or unlock confirmatory track.
- Frontier: verified=220, blocked=6127, candidate_page_cursor=6347, newly_discovered=0, remaining_discovered=0; 4 non-ASCII asset IDs durably blocked (我踏马来了, 牛来, 老子, 龙虾). Historical rank coverage NOT_PROVEN_COMPLETE; rank policy no fixed top-N cutoff. No new candidates discovered/validated.

## Concrete next action (priority order)
1. On/after 2026-10-29 (or once the October 2026 Binance monthly archive publishes), re-check cutoff via `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31`. Only proceed when cutoff >= 2026-10-29. Preregister/evaluate H004V106 on a fresh sealed forward block with HAC/overlap-aware uncertainty, computing only completed 30-day outcomes. Require |high_low_diff_net_1x| above a predeclared economic significance threshold and Holm-significance across the cell family before any promotion claim.
2. Until unblocked, continue independent unblocked work per AGENTS.md: free-source discovery (re-walk catalog when it may gain new listings), validation, design, or red-team. Record every blocker with reason; do not loop on the 404 endpoint.
3. Run full test suite (`python3 -m unittest discover -s tests`); confirm DISPERSION-001/002 and DISPERSION-003 sealed forward block/integrity audits/defective archive byte-unchanged apart from recorded changes.
4. Update frontier/registry/manifests/handoff; leave a concrete executable next action. Never wait for user-provided experiment ID.

Constraints: free public data only, historical-only, point-in-time ranks, no forward-fill, no trading, no secrets. Never change DISPERSION-001/002. All cells must carry states with reasons. Do not relax fixed-30-day outcome maturity; do not open sealed holdout to rescue progress.
