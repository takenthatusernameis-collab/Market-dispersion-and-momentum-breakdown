## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 H10 (updated 2026-11-03T15:38Z)

## Situation
- Today 2026-11-03. November 2026 not published (month not over). Genuine data-maturity blocker.
- Structural feasibility (DISP-003-H10-FEASIBILITY-001): October 2026 cannot unblock H10. At cutoff 2026-10-31 fresh block window gives exactly 1 formation; trailing-decile rule needs >=30 prior in-block dispersions. November 2026 is structurally the first cutoff that could classify high/low (~31 formations projected). Artifact: `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/H10_feasibility_analysis_20261103.json`; tests `tests/test_h10_feasibility.py`.
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged. Fresh H10 block IMMATURE (n_formations=1, n_high=0, n_low=0, n_mid=1, date 2026-09-30).
- Suite: 216 run, 216 OK, 0 failures (skipped=1).
- Latest probe 2026-11-03T15:38:02Z: Nov 2026 klines AND fundingRate HTTP 404; daily endpoints also 404; Sept 200 OK (control). target_published=false, cutoff_gate=BLOCKED.

## Your task
1. Do NOT re-probe November 2026 before cutoff >= 2026-11-29.
2. When target_published=true: refresh free public data if needed, re-run tests, verify H004V106 unchanged, run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`).
3. If n_high>0 and n_low>0, report full results with overlap-aware/HAC uncertainty and apply predeclared decision rule before any confirmatory claim.
4. If still IMMATURE, record exact blocker, update frontier/registry/manifest/handoff, wait for next vintage.
5. Update frontier/registry/manifest/handoff with results/blocker. Leave concrete next action. Never write "wait for a new experiment ID." If blocked by data maturity, wait for data vintage.

## Hard constraints
- Free public data only; historical research only; no live/paper trading.
- Preserve DISPERSION-001/002. Never modify canonical `forward_block/` or other frozen artifacts.
- Do not relax 30-day maturity, MIN_ASSETS_DECILES=20, or trailing-decile state rule.
- Correct for complete declared multiple-testing family if promoting.
"