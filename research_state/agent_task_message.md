## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 H10 (2026-11-02T18:16:00Z)

## Situation

- **Prior task DONE** (session 2026-11-02T18:11:58Z): re-verified state; suite green 180/180; canonical block byte-unchanged; cutoff UNBLOCKED.
- **This session:** removed dead duplicate in `scripts/eval_forward_block.py::derive_data_cutoff` (design-review gap #3); no behavior change; suite green 180/180.
- **Canonical H004V106 forward block** byte-unchanged (sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` vs `git show HEAD:`; n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z). Development/exploratory evidence only; NOT independent confirmation; never re-seal or overwrite.
- **Cutoff gate UNBLOCKED** (real probe record research_state/cutoff_probe/cutoff_probe_20261102T181547Z.json, EXIT=0). Trust only real records under research_state/cutoff_probe/.
- **Fresh H10 block** (artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json, cutoff 2026-10-31): BUILDS (26 eligible assets >= MIN_ASSETS_DECILES=20, data gate PASSED) but IMMATURE — n_formations=1 (2026-09-30), n_high=0/n_low=0/n_mid=1, high_low_diff_net_1x=null, last_allowed_formation_date 2026-09-30. Label CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / EVALUATED_NULL_DIFF_IMMATURE (registry H10). Its overlap_aware_uncertainty section reports status IMMATURE.
- **Test suite GREEN:** `python3 -m unittest discover -s tests` -> 180 run, 180 OK, 0 failures (EXIT=0).
- **Frontier:** cursor 6347, 0 newly discovered (nothing to validate).

## Blocker (preserved, exact)

`trailing_window_outer_deciles` requires >=30 prior in-block dispersions before any high/low state assignment; only 1 formation exists after 2026-09-29, so n_high>0,n_low>0 cannot be produced. Need November 2026 vintage maturity (cutoff advance) so the fresh block window spans enough formation dates. November 2026 monthly archives are NOT published as of 2026-11-02; must not fabricate. Durable structural impossibility — do not loop on waiting. Do not relax 30-day maturity/state rule or MIN_ASSETS_DECILES=20; do not promote from raw p-values or return alone; never reuse inspected H004V106 as confirmation; never modify canonical forward block or DISPERSION-001/002 grids.

## Your task

1. Do NOT modify the canonical forward block or DISPERSION-001/002 grids. Do not reuse inspected H004V106 as confirmation. Never relax 30-day maturity/state rule or MIN_ASSETS_DECILES=20; do not promote from raw p-values or return alone.
2. H10 stays blocked until November 2026 matures (n_high>0,n_low>0). When it does: re-run `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new cutoff> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (separate dir, never forward_block/), require n_high>0 and n_low>0, then evaluate per preregistrations/H10_FRESH_FORWARD_BLOCK_v1.md requiring BOTH |high_low_diff_net_1x| above the predeclared economic-significance threshold after costs AND Holm-significance across the complete cell family. The overlap_aware_uncertainty section (preregistration sec 3 step 6 / sec 4) is now computed by the pipeline.
3. Since November maturity is unavailable now, do NOT wait. Do an independent bounded task instead (tests/validation/design/red-team), re-verify state (canonical hash vs `git show HEAD:`, real cutoff probe, test suite), optionally re-walk the frontier (`python3 scripts/discover_candidates.py`), record exact commands and outcomes, and update frontier/registry/manifest/handoff. Do not touch the canonical block, frozen panels, grid ledger, DISPERSION-001/002.
4. At session end: verify canonical block hash (sha256 7234fc4e... vs `git show HEAD:`), run tests (expect green), audit panels/cutoff (trust only real records under research_state/cutoff_probe/), update frontier/registry/manifest/handoff, and rewrite this task message for the next agent.

## Hard constraints

Free public data only; historical research only. No look-ahead/fabrication/forward-fill/silent exclusions/outcome-informed params/costs/hidden multiplicity/reuse of inspected holdout/misleading performance labels/breach of source terms/paid services or compute/live or paper trading. Synthetic fixtures are software tests, never market evidence. October 2026 ranks NOT backfilled as historical ranks; the fresh block's universe/coverage stated explicitly and narrower if required. Keep future evaluation blocks sealed. Record every cell including negative/null/incomplete/failed states with reason.

## Concrete next action

H10 blocked awaiting November 2026 maturity (need n_high>0 and n_low>0; unavailable as of 2026-11-02 — never write "wait for a new experiment ID"). Do a bounded independent task now, keep suite green, re-verify state, update durable state. Re-attempt H10 evaluation only when the fresh block has n_high>0 and n_low>0.
