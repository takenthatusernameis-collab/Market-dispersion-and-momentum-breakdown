# Agent Task Message (for next agent)

Read the full handoff: `research_state/agent_handoff.md`

## Mandate
Continue quantitative research for HARMONY-CRYPTO-EDGE-004-DISPERSION-003. Historical-only, free-data-only. No live/paper trading. No paid services or secrets. Do not wait for a user-provided experiment ID; the program stays ACTIVE and the next task must be executable without one.

## State on handoff (2026-10-25)
- Cutoff gate: BLOCKED (structural). Today 2026-10-25; gate requires data cutoff >= 2026-10-29. October 2026 Binance monthly archive still 404; NOT re-probed per blocker note. Do not re-probe the same 404 endpoint.
- DISPERSION-001/002: unchanged, immutable.
- DISPERSION-003 grid: executed 216/216 OK, 0 Holm-rejected; anchors H004V105 (legacy) and H004V106 (expanding) match preregistration; manifest regeneration byte-identical.
- Canonical sealed forward block (forward_block/forward_block_evaluation.json, H004V106, cutoff 2026-09-30, last formation 2026-08-31): 608 formations; state counts high=61, low=90, mid=457; high_low_diff_net_1x = +0.6165 (POSITIVE sign, opposite to H1's registered negative prediction); Newey-West HAC lag 29: t=1.5482, 95% CI [-0.164, 1.397], NOT significant; spread_net_1x mean=+0.0996, median=-0.0106. Verified against integrity_audit + forward_block_independent_recomputation_20261025.json (608 formations, 0 non-finite dispersion). Development/exploratory evidence only — already inspected; NOT independent confirmation; NOT reused as a fresh test.
- Defective archive archive_defective_momentum_20261024 is quarantined (price-level momentum, dispersion ~1e149, no sealing rule, look-ahead cutoff through 2026-09-29); never cited as canonical.
- Hypothesis registry: H1 NOT_SUPPORTED_AS_ROBUST_EDGE; H6 CANDIDATE_UNVALIDATED (requires fresh sealed block after 2026-09-29 with predeclared economic threshold + Holm significance); H7 CANDIDATE_UNVALIDATED/EXPLORATORY_ONLY positive-direction candidate awaiting fresh block. H2–H5 CANDIDATE_UNVALIDATED.
- Candidate frontier: verified=220, blocked=6127, remaining_discovered=0, candidate_page_cursor=6351, rank_frontier_exhausted=false, rank_policy=no fixed top-N cutoff, historical_rank_coverage_state=NOT_PROVEN_COMPLETE. 4 non-ASCII asset IDs blocked durably (non_ascii_asset_id); validation script records blockers additively.
- Full test suite: 45 tests OK (1 pre-existing RuntimeWarning). DISPERSION-001/002 and DISPERSION-003 sealed forward block / integrity audits / defective archive byte-unchanged (git diff: only __pycache__).

## Concrete next action (priority order)
1. On/after 2026-10-29 (or once the October 2026 Binance monthly archive publishes), re-check the data cutoff via `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31`; proceed only when cutoff >= 2026-10-29. Then preregister/evaluate H004V106 on a fresh sealed forward block with HAC/overlap-aware uncertainty, computing only completed 30-day outcomes. Require |high_low_diff_net_1x| above a predeclared economic significance threshold and Holm-significance across the cell family before any promotion claim.
2. Until the cutoff is unblocked, continue independent unblocked work per AGENTS.md: free-source discovery (re-walk the catalog when it may have new listings), validation, design, or red-team. Record every blocker with reason; do not loop on the 404 endpoint.
3. Run the full test suite (`python3 -m unittest discover -s tests`); confirm DISPERSION-001/002 and the DISPERSION-003 sealed forward block / integrity audits / defective archive are byte-unchanged (git diff).
4. Update the candidate frontier, hypothesis registry, manifests and handoff; leave a concrete, executable next action for the following agent.

Constraints: free public data only (Coin Metrics Community API, Binance Public Data Archive; keyless), historical-only, point-in-time ranks, no forward-fill, no trading, no secrets. Never change DISPERSION-001/002. All grid cells carry one of OK/BLOCKED/INVALID/FAILED/NOT_RUN with a reason.

EOF
