# Agent Task Message (for next agent)

Read the full handoff: `research_state/agent_handoff.md`

## Mandate
Continue quantitative research for HARMONY-CRYPTO-EDGE-004-DISPERSION-003. Historical-only, free-data-only. No live/paper trading. No paid services or secrets. Do not wait for a user-provided experiment ID; the program stays ACTIVE and the next task must be executable without one.

## Verified state on handoff (2026-10-25)
- Cutoff gate: BLOCKED (structural). Today 2026-10-25; gate requires data cutoff >= 2026-10-29. October 2026 Binance monthly archive still 404; NOT re-probed per blocker note. Do not re-probe the same 404 endpoint.
- Grid manifest: deterministic, byte-identical regeneration; 216 cells H004V001-H004V216; anchors H004V105 (legacy) and H004V106 (expanding) correct; grid executed 216/216 OK, 0 Holm-rejected.
- Canonical sealed forward block (forward_block/forward_block_evaluation.json, H004V106, cutoff 2026-09-30, last formation 2026-08-31): 608 completed 30-day formations; state counts high=61/low=90/mid=457; high_low_diff_net_1x = +0.6165223953929935; spread_net_1x mean=+0.0996, median=-0.0106; Newey-West HAC lag 29: t~1.55, 95% CI [-0.164, 1.397], NOT significant. Development/exploratory evidence only — already inspected; NOT independent confirmation; NOT reused as a fresh test.
- Defective archive archive_defective_momentum_20261024 is quarantined; never cited as canonical.
- Funding-panel schema repaired (32/32 panels, 4 columns, 0 NaN funding rates). Regression test present.
- Integrity audits present and verified: forward_block_integrity_audit.json, forward_block_hac_addendum_20261024.json, forward_block_independent_recomputation_20261025.json (608 formations, 0 non-finite dispersion).
- Hypothesis registry: H1 NOT_SUPPORTED_AS_ROBUST_EDGE; H6 CANDIDATE_UNVALIDATED; H7 CANDIDATE_UNVALIDATED/EXPLORATORY_ONLY positive-direction; H2-H5 CANDIDATE_UNVALIDATED.
- Candidate frontier: candidates_blocked=6127, candidate_page_cursor=6347, 4 non-ASCII asset IDs durably blocked (我踏马来了, 牛来, 老子, 龙虾); rank_frontier_exhausted=false; historical_rank_coverage_state=NOT_PROVEN_COMPLETE. Free-source discovery re-walked the CoinMetrics community catalog this session: 6347 entries walked, 0 newly discovered (catalog not grown); candidates_discovered empty, nothing to validate. Verified count per last validation batch record = 220.
- Full test suite: 46 tests OK (1 pre-existing RuntimeWarning). DISPERSION-001/002 artifacts unchanged. DISPERSION-003 sealed forward block, integrity audits and defective archive byte-unchanged (git diff: only universe_frontier.json catalog-discovery timestamps and __pycache__).

## Concrete next action (priority order)
1. On/after 2026-10-29 (or once the October 2026 Binance monthly archive publishes), re-check the data cutoff via `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31`; proceed only when cutoff >= 2026-10-29. Then preregister/evaluate H004V106 on a fresh sealed forward block with HAC/overlap-aware uncertainty, computing only completed 30-day outcomes. Require |high_low_diff_net_1x| above a predeclared economic significance threshold and Holm-significance across the cell family before any promotion claim.
2. Until the cutoff is unblocked, continue independent unblocked work per AGENTS.md: free-source discovery (re-walk the catalog when it may gain new listings — just re-walked, 0 new), validation, design, or red-team. Record every blocker with reason; do not loop on the 404 endpoint.
3. Run the full test suite (`python3 -m unittest discover -s tests`); confirm DISPERSION-001/002 and the DISPERSION-003 sealed forward block / integrity audits / defective archive are byte-unchanged apart from the recorded funding-panel reseal.
4. Update the candidate frontier, hypothesis registry, manifests and handoff; leave a concrete, executable next action for the following agent. Never wait for a user-provided experiment ID; the program stays ACTIVE.

Constraints: free public data only (CoinMetrics Community API, Binance Public Data Archive; keyless), historical-only, point-in-time ranks, no forward-fill, no trading, no secrets. Never change DISPERSION-001/002. All grid cells carry one of OK/BLOCKED/INVALID/FAILED/NOT_RUN with a reason. Do not relax the fixed 30-day outcome maturity rule; do not open a sealed holdout to rescue progress; never reuse an inspected holdout as independent evidence.
EOF
