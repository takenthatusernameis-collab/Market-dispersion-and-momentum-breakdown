## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 H10 (2026-11-02T19:00:00Z)

## Situation

- **Prior task DONE** (session 2026-11-02T18:20:00Z): re-verified state; suite green 180/180; canonical block byte-unchanged.
- **This session:** bounded re-verification + frontier re-walk; suite green 180/180/0; canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` matches `git show HEAD:`; frontier re-walk 6347 entries, 0 newly discovered; durable state refreshed.
- **Canonical H004V106 forward block** byte-unchanged (sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` vs `git show HEAD:`; n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z). Development/exploratory only; not independent confirmation.
- **Cutoff gate:** trust real records under `research_state/cutoff_probe/` (latest re-probe returned BLOCKED in this pass; prior UNBLOCKED record `cutoff_probe_20261102T180156Z.json` remains durable reference).
- **Fresh H10 block** (artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json, cutoff 2026-10-31): BUILDS but IMMATURE — n_formations=1 (2026-09-30), n_high=0/n_low=0/n_mid=1, high_low_diff_net_1x=null. Overlap-aware uncertainty reports IMMATURE.
- **Test suite GREEN:** `python3 -m unittest discover -s tests` -> 180 run, 180 OK, 0 failures.

## Blocker (preserved, exact)

`trailing_window_outer_deciles` requires >=30 prior in-block dispersions before any high/low state assignment; only 1 formation exists after 2026-09-29, so n_high>0,n_low>0 cannot be produced. Need November 2026 vintage maturity. November 2026 monthly archives not published as of 2026-11-02 — do not fabricate. Do not relax 30-day maturity/state rule or MIN_ASSETS_DECILES=20; do not promote from raw p-values or return alone; never reuse inspected H004V106 as confirmation; never modify canonical forward block or DISPERSION-001/002 grids.

## Your task

1. Do NOT modify canonical forward block or DISPERSION-001/002 grids.
2. H10 blocked until November 2026 matures (n_high>0,n_low>0). When matured: re-run `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new cutoff> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never forward_block/), require n_high>0,n_low>0, evaluate per preregistrations/H10_FRESH_FORWARD_BLOCK_v1.md requiring BOTH |high_low_diff_net_1x| above economic threshold after costs AND Holm-significance across complete cell family.
3. Since maturity unavailable now, do NOT wait. Do a bounded independent task (tests/validation/design/red-team), re-verify state (canonical hash vs `git show HEAD:`, real cutoff probe, tests), optionally re-walk frontier, record exact commands/outcomes, update frontier/registry/manifest/handoff.
4. At end: verify canonical hash, run tests (green), audit cutoff via real records, update durable state, rewrite this message.

## Hard constraints

Free public data only; historical research only. No look-ahead/fabrication/forward-fill/silent exclusions/outcome-informed params/costs/hidden multiplicity/reuse of inspected holdout/misleading performance labels/breach of source terms/paid services or compute/live or paper trading. Synthetic fixtures are software tests only. Keep future evaluation blocks sealed. Record every cell including negative/null/incomplete/failed states with reason.

## Concrete next action

H10 blocked awaiting November 2026 maturity (n_high>0,n_low>0; unavailable as of 2026-11-02). Do bounded independent work now; re-attempt H10 only when n_high>0,n_low>0.
