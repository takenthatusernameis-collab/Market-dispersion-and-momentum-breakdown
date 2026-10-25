# Agent Task Message (for next agent)

Read the full handoff: `research_state/agent_handoff.md`

## Mandate
Continue quantitative research for HARMONY-CRYPTO-EDGE-004-DISPERSION-003. Historical-only, free-data-only. No live/paper trading. No paid services or secrets. Do not wait for a user-provided experiment ID; the program stays ACTIVE and the next task must be executable without one.

## Verified state on handoff (2026-10-25)
- Cutoff gate: BLOCKED (structural). Today 2026-10-25; gate requires data cutoff >= 2026-10-29. October 2026 Binance monthly archive still 404; NOT re-probed per blocker note. Do not re-probe the same 404 endpoint.
- Grid manifest: deterministic, byte-identical regeneration; 216 cells H004V001-H004V216; anchors H004V105 (legacy) and H004V106 (expanding) correct; grid executed 216/216 OK, 0 Holm-rejected.
- Canonical sealed forward block (forward_block/forward_block_evaluation.json, H004V106, cutoff 2026-09-30, last formation 2026-08-31): 608 completed 30-day formations; state counts high=61, low=90, mid=457; high_low_diff_net_1x = +0.6165223953929935 (positive sign, opposite to H1's registered negative prediction); spread_net_1x mean = +0.0996, median = -0.0106; Newey-West HAC lag 29: t~1.55, 95% CI [-0.164, 1.397], NOT significant. Development/exploratory evidence only — already inspected; NOT independent confirmation; NOT reused as a fresh test.
- Defective archive archive_defective_momentum_20261024 is quarantined (price-level momentum, dispersion ~1e149, no sealing rule, look-ahead cutoff through 2026-09-29); never cited as canonical.
- Funding-panel schema defect REPAIRED. All 32 committed `binance_funding_*.csv` panels rebuilt from raw zips via `scripts/repair_funding_panels.py`; production fixed in `scripts/refresh_free_data.py` and `scripts/normalize_binance_panels.py`. Panels now 4 columns, single symbol, 0 NaN funding rates, 2023-01..2026-09. Regression test `tests/test_forward_block_integrity.py::test_funding_panels_have_aligned_header_and_data`.
- Integrity audits present and verified: forward_block_integrity_audit.json, forward_block_hac_addendum_20261024.json, forward_block_independent_recomputation_20261025.json (608 formations, 0 non-finite dispersion).
- Hypothesis registry: H1 NOT_SUPPORTED_AS_ROBUST_EDGE; H6 CANDIDATE_UNVALIDATED (requires fresh sealed block after 2026-09-29 with predeclared economic threshold + Holm significance); H7 CANDIDATE_UNVALIDATED/EXPLORATORY_ONLY positive-direction candidate awaiting fresh block. H2-H5 CANDIDATE_UNVALIDATED.
- Candidate frontier: verified=220, blocked=6127, remaining_discovered=0, candidate_page_cursor=6351, rank_frontier_exhausted=false, rank_policy=no fixed top-N cutoff, historical_rank_coverage_state=NOT_PROVEN_COMPLETE. 4 non-ASCII asset IDs blocked durably (我踏马来了, 牛来, 老子, 龙虾).
- Full test suite: 46 tests OK (1 pre-existing RuntimeWarning). DISPERSION-001/002 artifacts unchanged. DISPERSION-003 sealed forward block, integrity audits and defective archive byte-unchanged (git diff: only __pycache__).

## Concrete next action (priority order)
1. On/after 2026-10-29 (or once the October 2026 Binance monthly archive publishes), re-check the data cutoff via `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31`; proceed only when cutoff >= 2026-10-29. Then preregister/evaluate H004V106 on a fresh sealed forward block with HAC/overlap-aware uncertainty, computing only completed 30-day outcomes. Require |high_low_diff_net_1x| above a predeclared economic significance threshold and Holm-significance across the cell family before any promotion claim.
2. Until the cutoff is unblocked, continue independent unblocked work per AGENTS.md: free-source discovery (re-walk the catalog when it may have new listings), validation, design, or red-team. Record every blocker with reason; do not loop on the 404 endpoint.
3. Run the full test suite (`python3 -m unittest discover -s tests`); confirm DISPERSION-001/002 and the DISPERSION-003 sealed forward block / integrity audits / defective archive are byte-unchanged apart from the funding-panel reseal already recorded.
4. Update the candidate frontier, hypothesis registry, manifests and handoff; leave a concrete, executable next action for the following agent.

Constraints: free public data only (Coin Metrics Community API, Binance Public Data Archive; keyless), historical-only, point-in-time ranks, no forward-fill, no trading, no secrets. Never change DISPERSION-001/002. All grid cells carry one of OK/BLOCKED/INVALID/FAILED/NOT_RUN with a reason.
EOF
echo done