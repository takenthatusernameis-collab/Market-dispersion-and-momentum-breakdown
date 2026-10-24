# Agent Handoff — HARMONY-CRYPTO-EDGE-004

## Program status
- **ACTIVE CONTINUOUS RESEARCH.** Do not pause the program or await a user-supplied experiment ID.
- The authorized scope is this repository, historical research, free data and no-cost tooling only. No paid sources, trading credentials, orders or live/paper deployment.
- Existing DISPERSION-001 and DISPERSION-002 evidence is closed and immutable.

## Verified baseline
- DISPERSION-001: primary result and 72-grid sensitivity results are committed. All 72 grid configurations completed; zero passed the recorded Holm-adjusted p-value threshold below 0.05.
- DISPERSION-002: corrected report says discovery high-minus-low difference +28.77 percentage points, validation +0.79 points, final −0.50 points; the effect did not replicate and state sample sizes were very small.
- A 108-configuration manifest exists for DISPERSION-002, but the committed files inspected for this handoff do not show a matching full grid result ledger. Verify and close this evidence gap; do not claim all 108 configurations were tested solely from the report text.
- Previously committed historical panels cover 28 mapped assets and end on 2024-12-31. The historical rank frontier is not proven exhausted.
- Current next config: configs/dispersion_momentum_grid_v3.json, 216 cells (108 parameter combinations × 2 universe arms); deterministic manifest generator and contract tests included. Manifest regenerated and verified: 216 configurations, 216 unique IDs (H004V001..H004V216), 216 unique hashes; anchors H004V105 (legacy28_comparator) and H004V106 (expanding_point_in_time) confirmed present.

## Immediate next task
1. **[DONE]** Run the unit-test suite and scripts/generate_grid_v3_manifest.py; verify 216 unique IDs/hashes and anchors H004V105/H004V106. All tests pass (21/21).
2. [DONE] Extended free public price, cap and funding data to latest fully closed UTC daily candle (2026-10-23); provenance recorded in data/panels/data_refresh_provenance.json; 21/21 tests pass.
3. Discover candidates below the existing 28-asset set using descending historical point-in-time market-cap rank; process batches of 25 as operational checkpoints only, not a fixed universe cutoff. Record missing-history/mapping/data blockers and continue to other candidates/tasks.
4. Implement a resumable, idempotent DISPERSION-003 data gate and evaluation runner for the full 216-cell grid. Compare legacy28 and expanding point-in-time arms. The complete grid is development/validation only; report every cell and the full Holm correction family.
5. Freeze the exact future data cutoff and hashes before outcomes are viewed. Evaluate only the single primary anchor on the forward block beginning 2025-01-01; never search parameters on that block.
6. Update hypothesis_registry.json and preregister a new, theory-led experiment if no candidate passes. Keep the program active regardless of negative or null results.
7. Verify tests, evidence hashes, terminal cell counts and no modifications to DISPERSION-001/002 artifacts; update this handoff and the next task with a measurable action.

## Controls
- Point-in-time universe, no look-ahead, delisting/symbol-migration controls, historical funding/cost accounting, chronological evaluation and free-data-only.
- No fixed top-N universe cutoff; current ranks are discovery only.
- Negative, invalid, incomplete, failed and not-run cells remain in the ledger with explicit reasons.
- A green test or top-performing grid candidate is not evidence of profitability.

## Continuation
The scheduled controller has finite hosted-runner activations and may be interrupted by provider, quota, network or platform failures. Continue through the scheduled recoverable loop and preserve checkpoints; never claim guaranteed uninterrupted uptime for a single process. If any source/phase is blocked, record the blocker and proceed with the next valid source, candidate, test, audit or hypothesis-planning task. Do not stop the research program because an experiment ended.
