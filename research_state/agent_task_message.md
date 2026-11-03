## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 H10 (2026-11-03T11:24:xxZ)

## Situation
- Today 2026-11-03; November 2026 not published (month not over). Genuine data-maturity blocker.
- H10 needs n_high>0 AND n_low>0 from trailing-decile classification; current fresh block has only 1 formation (2026-09-30), cannot classify high/low.
- October 2026 published but does not unblock (2026-10-28 kline gap shifts last_allowed_formation to 2026-09-30; trailing window needs >=30 prior in-block dispersions).
- Adaptive-gate trigger NOT met. Do NOT start exploratory track; do NOT relax 30-day maturity/MIN_ASSETS_DECILES=20/trailing-decile state rule.
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged.
- Note: test interpreter requires `python3 -m pip install -r requirements.txt` (numpy/pandas) before running suite.

## Your task
1. Re-probe November 2026: `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11` — once per session, only after material passage of time / near month-end (cutoff >= 2026-11-29 for complete 30-day outcome).
2. If target_published=true: refresh free public data if needed (`python3 scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>`), re-run tests, verify H004V106 unchanged, re-run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`):
   `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new cutoff> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/`
   Do not relax 30-day maturity, MIN_ASSETS_DECILES=20, or trailing-decile state rule.
3. If n_high>0 and n_low>0, report full results with overlap-aware/HAC uncertainty and apply predeclared decision rule (|high_low_diff_net_1x| above predeclared economic-significance threshold after costs AND Holm across complete cell family) before any confirmatory claim.
4. If still IMMATURE (n_high==0 or n_low==0), record exact blocker (unmet: n_high>0 AND n_low>0), update frontier/registry/manifest/handoff, wait for next vintage. Do not relax rules, fabricate formations/outcomes, or open canonical sealed holdout.
5. Update frontier/registry/manifest/handoff with results/blocker. Leave concrete next action. Never write "wait for a new experiment ID." If blocked by data maturity, wait for data vintage.

## Hard constraints
- Free public data only; historical research only; no live/paper trading.
- Preserve DISPERSION-001/002. Never modify canonical `forward_block/` or other frozen artifacts.
- Do not relax 30-day maturity, MIN_ASSETS_DECILES=20, or trailing-decile state rule.
- Correct for complete declared multiple-testing family if promoting.

## Latest probe (2026-11-03T11:16:09Z)
- probe-month 2026-11: target_published=false, cutoff_gate=BLOCKED (record `research_state/cutoff_probe/cutoff_probe_20261103T111609Z.json`). Archive alive (September 2026 control HTTP 200); miss genuine month-not-over. November 2026 monthly klines AND fundingRate HTTP 404, daily 11-28/29/30/31 HTTP 404. Fresh H10 still IMMATURE/NULL_DIFF.
