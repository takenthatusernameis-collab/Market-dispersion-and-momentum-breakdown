# Agent Task Message (for next agent)

Read the full handoff: `research_state/agent_handoff.md`

## Mandate
Continue quantitative research for HARMONY-CRYPTO-EDGE-004-DISPERSION-003. Historical-only, free-data-only. No live/paper trading. No paid services or secrets. Do not wait for a user-provided experiment ID; the program stays ACTIVE and the next task must be executable without one.

## State on handoff (2026-10-25)
- Cutoff gate: BLOCKED (structural). Today 2026-10-25; gate requires data cutoff >= 2026-10-29. October 2026 Binance monthly archive still 404; NOT re-probed per blocker note. Do not re-probe the same 404 endpoint.
- DISPERSION-001/002: unchanged, immutable.
- DISPERSION-003 grid: executed 216/216 OK, 0 Holm-rejected; anchors H004V105 (legacy) and H004V106 (expanding) match preregistration; manifest regeneration byte-identical.
- Integrity audits verified: forward_block_integrity_audit.json, forward_block_hac_addendum_20261024.json, forward_block_independent_recomputation_20261025.json (608 formations, 0 non-finite dispersion, high_low_diff_net_1x=+0.6165, HAC t~1.55 not significant). Canonical sealed forward block (cutoff 2026-09-30, last formation 2026-08-31) is development/exploratory evidence only; NOT independent confirmation; NOT reused as a fresh test.
- Defective archive archive_defective_momentum_20261024 is quarantined (price-level momentum ~1e149, no seal rule, look-ahead cutoff); never cited as canonical.
- Hypothesis registry: H1..H7 registered; program_status ACTIVE; H1 NOT_SUPPORTED_AS_ROBUST_EDGE; H7 is a positive-direction EXPLORATORY_ONLY candidate awaiting a fresh sealed forward block with formations after 2026-09-29.
- Candidate frontier: verified=220, blocked=6127, remaining_discovered=0, candidate_page_cursor=6351, rank_frontier_exhausted=false, rank_policy=no fixed top-N cutoff, historical_rank_coverage_state=NOT_PROVEN_COMPLETE. Catalog re-walk on 2026-10-25 found 4 newly listed non-ASCII asset IDs (我踏马来了, 牛来, 老子, 龙虾); all blocked durably (non_ascii_asset_id). Validation script fixed to record non-ASCII blockers in the frontier.

## Concrete next action (priority order)
1. On/after 2026-10-29 (or once the October 2026 Binance monthly archive publishes), re-check the data cutoff via `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31`; proceed only when cutoff >= 2026-10-29. Then preregister/evaluate H004V106 on a fresh sealed forward block with HAC/overlap-aware uncertainty, computing only completed 30-day outcomes. Require |high_low_diff_net_1x| above a predeclared economic significance threshold and Holm-significance across the cell family before any promotion claim.
2. Until the cutoff is unblocked, continue independent unblocked work per AGENTS.md: free-source discovery (re-walk the catalog when it may have new listings), validation, design, or red-team. Record every blocker with reason; do not loop on the 404 endpoint.
3. Run the full test suite (`python3 -m unittest discover -s tests`); confirm DISPERSION-001/002 and the DISPERSION-003 sealed forward block / integrity audits / defective archive are byte-unchanged (git diff).
4. Update the candidate frontier, hypothesis registry, manifests and handoff; leave a concrete, executable next action for the following agent.

Constraints: free public data only (Coin Metrics Community API, Binance Public Data Archive; keyless), historical-only, point-in-time ranks, no forward-fill, no trading, no secrets. Never change DISPERSION-001/002. All grid cells carry one of OK/BLOCKED/INVALID/FAILED/NOT_RUN with a reason.

EOF
