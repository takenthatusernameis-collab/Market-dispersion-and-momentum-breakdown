## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 H10 (updated 2026-11-03T14:17Z)

## Situation
- Today 2026-11-03. November 2026 not published (month not over). Genuine data-maturity blocker.
- **Structural feasibility (DISP-003-H10-FEASIBILITY-001):** October 2026 cannot unblock H10. At cutoff 2026-10-31 fresh block window gives exactly 1 formation; trailing-decile rule needs >=30 prior in-block dispersions. **November 2026 is structurally the first cutoff that could classify high/low** (~31 formations projected). Artifact: `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/H10_feasibility_analysis_20261103.json`; tests `tests/test_h10_feasibility.py`.
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged (verified vs disk and vs `git show HEAD:`). Fresh H10 block IMMATURE (n_formations=1, n_high=0, n_low=0, n_mid=1, date 2026-09-30, high_low_diff_net_1x=null, overlap_aware_uncertainty status IMMATURE). Fresh block sha256 `4106f42105d224ab0880710e8e1847c012025e5d50fdd47a3e66feb20e03435a`.
- Suite: 216 run, 216 OK, 0 failures (skipped=1). Requires numpy/pandas installed.
- Latest probe 2026-11-03T13:41:20Z (record `research_state/cutoff_probe/cutoff_probe_20261103T134120Z.json`): Nov 2026 klines AND fundingRate HTTP 404; daily endpoints also 404; Sept 200 OK (control). target_published=false, cutoff_gate=BLOCKED.

## Your task
1. Do NOT re-probe November 2026 before cutoff >= 2026-11-29. Today 2026-11-03; re-probing repeats known failure, adaptive-gate trigger not met.
2. When target_published=true (`python3 scripts/probe_cutoff_gate.py --probe-month 2026-11` returns UNBLOCKED): refresh free public data if needed (`python3 scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>`), re-run tests, verify H004V106 unchanged vs `git show HEAD:`, run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`):
   `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new cutoff> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/`
   Do not relax 30-day maturity, MIN_ASSETS_DECILES=20, or trailing-decile state rule.
3. If n_high>0 and n_low>0, report full results with overlap-aware/HAC uncertainty and apply predeclared decision rule (|high_low_diff_net_1x| above predeclared economic-significance threshold after costs AND Holm across complete cell family) before any confirmatory claim.
4. If still IMMATURE, record exact blocker, update frontier/registry/manifest/handoff, wait for next vintage. Do not relax rules/fabricate/open canonical sealed holdout.
5. Update frontier/registry/manifest/handoff with results/blocker. Leave concrete next action. Never write "wait for a new experiment ID." If blocked by data maturity, wait for data vintage.

## Hard constraints
- Free public data only; historical research only; no live/paper trading.
- Preserve DISPERSION-001/002. Never modify canonical `forward_block/` or other frozen artifacts.
- Do not relax 30-day maturity, MIN_ASSETS_DECILES=20, or trailing-decile state rule.
- Correct for complete declared multiple-testing family if promoting.
