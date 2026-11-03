## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 H10 (2026-11-03T19:51Z)

## Situation
- Today 2026-11-03. November 2026 not published. Genuine data-maturity blocker; cutoff gate BLOCKED until >= 2026-11-29.
- Latest REAL probe: research_state/cutoff_probe/cutoff_probe_20261103T154136Z.json (2026-11-03T15:41:36Z): November 2026 monthly klines AND monthly fundingRate HTTP 404; daily 11-28/29/30/31 HTTP 404; September 2026 control HTTP 200. target_published=false, cutoff_gate=BLOCKED, probe_exit=1, archive_alive=true.
- Do NOT re-probe November 2026 before cutoff >= 2026-11-29. Today is before the gate date; re-probing is a same-day repeat of a known failure and is prohibited.
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged vs disk and `git show HEAD:`; sealed forward block is development/exploratory evidence only.
- Fresh H10 block unchanged: n_formations=1, n_high=0, n_low=0, n_mid=1, date 2026-09-30, high_low_diff_net_1x null, overlap_aware_uncertainty status IMMATURE, data_cutoff 2026-10-31.
- Environment: numpy/pandas installed; suite green (218 run, OK, skipped=1, EXIT=0).
- Frontier exhausted (cursor 6347); grid ledger 218/218 OK.
- All H004V106 audit artifacts present and passing: final integrity audit PASS (608 formations, high=61/low=90/mid=457, all recompute matches within 1e-9, cost treatment consistent, tail influence within thresholds, overlap-aware CI computed), overlap-aware audit, tail influence audit, cluster bootstrap, temporal stability, placebo red team, dispersion regime conditioning, state representativeness, rolling dispersion window.
- H10 feasibility analysis (DISP-003-H10-FEASIBILITY-001) confirms November 2026 is the first vintage that could structurally classify high/low (~31 formations projected at cutoff 2026-11-30; cutoff 2026-10-31 holds exactly 1 formation). October 2026 publication did NOT and could NOT unblock H10.
- No bounded, no-cost, unblocked productive action remains; all remaining work requires November 2026 data vintage.

## Your task
1. Do NOT re-probe November 2026 before cutoff >= 2026-11-29.
2. On/after 2026-11-29, re-probe: `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If target_published=true: refresh free public data if needed (`python3 scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>`), re-run `python3 -m unittest discover -s tests`, verify H004V106 unchanged vs `git show HEAD:`, run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` via `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new cutoff> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never write to `forward_block/`).
3. If n_high>0 and n_low>0, report full results with overlap-aware/HAC uncertainty and apply predeclared decision rule before any confirmatory claim.
4. If still IMMATURE, record exact blocker, update frontier/registry/manifest/handoff, wait for next vintage. Do not relax maturity/decile rules.
5. Update frontier/registry/manifest/handoff with results/blocker. Leave a concrete next action. Never write "wait for a new experiment ID."

## Hard constraints
- Free public data only; historical research only; no live/paper trading.
- Preserve DISPERSION-001/002. Never modify canonical `forward_block/`.
- Do not relax 30-day maturity, MIN_ASSETS_DECILES=20, or trailing-decile state rule.
- Correct for complete declared multiple-testing family if promoting.
- Trust only real probe records under research_state/cutoff_probe/.
"