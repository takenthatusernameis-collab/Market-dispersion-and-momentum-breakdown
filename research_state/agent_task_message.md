## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 H10 (2026-11-03T09:23:10Z)

## Session verification (2026-11-03T09:23:10Z)
- Ran `python3 -m unittest discover -s tests` -> **210 run, 210 OK, 1 skipped, EXIT=0** (state verified directly, not trusted from prose).
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` verified against the working-tree `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`.
- `research_state/run_manifest.json` carries the top-level `latest_archive_probe` key (the regression from checkpoint `2d6fcb3e` was already repaired by the prior session and is still present), quoting the real record `research_state/cutoff_probe/cutoff_probe_20261103T090931Z` (BLOCKED, target_published=false, probe_exit=1) with canonical H004V106 block fields.
- `universe_frontier.json`: status ACTIVE_INCOMPLETE, last_updated_utc 2026-11-03T09:11:16Z, candidate_page_cursor 6347, candidates_discovered [] (catalog exhausted; nothing new to validate).
- Fresh H10 block unchanged: IMMATURE/NULL_DIFF (n_formations=1, n_high=0, n_low=0, diff null) at `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json`. Canonical `forward_block/` unchanged. No frozen artifacts modified.

## Situation
- Today is 2026-11-03; November 2026 monthly archive not yet published (month not over). Genuine data-maturity blocker. H10 cannot be evaluated until the fresh block window spans enough formation dates for trailing-decile high/low classification.
- October 2026 vintage is published (UNBLOCKED) but does NOT unblock H10. Structural cause, verified on current panels: (i) 2026-10-28 absent from all Binance kline panels (genuine gap); eval_forward_block.py derives last_allowed_formation by index position (cutoff_loc - horizon), shifting last_allowed_formation to 2026-09-30 and excluding the 2026-10-01 formation; (ii) even without that gap, block window 2026-09-30..2026-10-01 holds <=2 formations while trailing-window outer-decile classification needs >=30 prior in-block dispersions to assign high/low state. >=20-asset gate necessary but not sufficient.
- Adaptive research-gate trigger NOT met (single timing route; repeated same-endpoint probes same-day are not distinct failed routes spanning two source families). Do NOT start exploratory track; do NOT relax 30-day maturity, MIN_ASSETS_DECILES=20, or trailing-decile state rule.

## Your task
1. Re-probe November 2026: `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11` — once per session only, and only after material passage of time / near month-end; repeating same failed endpoint same-day is looping. When target_published=true, refresh free public data if needed via `python3 scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>`, re-run tests, verify H004V106 unchanged, re-run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`):
   `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new cutoff> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/`
   Do not relax 30-day maturity, MIN_ASSETS_DECILES=20, or trailing-decile state rule.
2. If n_high>0 and n_low>0, report full results with overlap-aware/HAC uncertainty and apply predeclared decision rule (|high_low_diff_net_1x| above predeclared economic-significance threshold after costs AND Holm across complete cell family) before any confirmatory claim.
3. If still IMMATURE (n_high==0 or n_low==0), record exact blocker (unmet: n_high>0 AND n_low>0), update frontier/registry/manifest/handoff, wait for next vintage. Do not relax rules, fabricate formations/outcomes, or open canonical sealed holdout.
4. Update frontier/registry/manifest/handoff with results/blocker. Leave concrete next action. Never write "wait for a new experiment ID."

## Hard constraints
- Free public data only; historical research only; no live/paper trading.
- Preserve DISPERSION-001/002. Never modify canonical `forward_block/` or other frozen artifacts.
- Do not relax 30-day maturity, MIN_ASSETS_DECILES=20, or trailing-decile state rule.
- Do not write "wait for a new experiment ID." If blocked by data maturity, wait for data vintage.
- Correct for complete declared multiple-testing family if promoting.

## Latest probe (2026-11-03T09:23:10Z)
- probe-month 2026-11: target_published=false, cutoff_gate=BLOCKED (record `research_state/cutoff_probe/cutoff_probe_20261103T092310Z.json`). Archive alive (control 2026-09 monthly klines/fundingRate HTTP 200, daily 09-28/29/30 HTTP 200, 09-31 HTTP 404 invalid date); miss is genuine month-not-over absence. All six November endpoints (monthly klines, monthly fundingRate, daily 11-28/29/30/31) HTTP 404.
- Tests green (210 OK, 1 skipped). H004V106 unchanged. Fresh H10 still IMMATURE/NULL_DIFF. No frozen artifacts modified.

(End of file - total 30 lines)