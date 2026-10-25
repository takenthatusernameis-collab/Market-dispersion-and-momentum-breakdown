# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003
## Mandate
Continue quantitative research. Historical-only, free-data-only. No live/paper trading. No paid services or secrets.

## Current state (2026-10-25T11:27Z)
- Cutoff gate: BLOCKED (structural). Today 2026-10-25 < 2026-10-29; October 2026 Binance monthly archive 404; not re-probed per blocker note. Do not re-probe the same 404 endpoint.
- DISPERSION-001/002 unchanged; artifacts immutable.
- DISPERSION-003: grid 216/216 OK, 0 Holm-rejected (grid_summary.json). Canonical sealed forward block (H004V106, cutoff 2026-09-30, last formation 2026-08-31): 608 formations, high_low_diff_net_1x=+0.6165223953929935, HAC t~1.55 not significant. Integrity audits present and byte-consistent. Defective archive quarantined.
- Frontier: blocked=6127, candidate_page_cursor=6347, 4 non-ASCII asset IDs durably blocked (我踏马来了, 牛来, 老子, 龙虾). Historical rank coverage NOT_PROVEN_COMPLETE; rank policy no fixed top-N cutoff. Discovery re-walked at cursor 6347, no new candidates.
- Tests: `python3 -m unittest discover -s tests` -> 46 OK (1 pre-existing RuntimeWarning from quarantined defective archive). git diff only __pycache__ + universe_frontier.json timestamp (no source changes); all frozen artifacts byte-unchanged.

## Concrete next action (priority order)
1. On/after 2026-10-29 (or once the October 2026 Binance monthly archive publishes), re-check cutoff via `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31`. Only proceed when cutoff >= 2026-10-29. Preregister/evaluate H004V106 on a fresh sealed forward block with HAC/overlap-aware uncertainty, computing only completed 30-day outcomes. Require |high_low_diff_net_1x| above a predeclared economic significance threshold and Holm-significance across the cell family before any promotion claim.
2. Until unblocked, continue independent unblocked work per AGENTS.md: free-source discovery (re-walk catalog when it may gain new listings), validation, design, or red-team. Record every blocker with reason; do not loop on the 404 endpoint.
3. Run full test suite; confirm DISPERSION-001/002 and DISPERSION-003 sealed forward block/integrity audits/defective archive byte-unchanged apart from recorded changes.
4. Update frontier/registry/manifests/handoff; leave a concrete executable next action. Never wait for user-provided experiment ID.

Constraints: free public data only, historical-only, point-in-time ranks, no forward-fill, no trading, no secrets. Never change DISPERSION-001/002. All cells must carry states with reasons. Do not relax fixed 30-day outcome maturity; do not open sealed holdout to rescue progress.