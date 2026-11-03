## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 H10 (2026-11-03T04:00:00Z)

## Session verification (2026-11-03T04:00:00Z)
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` verified byte-unchanged vs `git show HEAD` (608 formations, +0.6165 net 1x).
- Full test suite green: `python3 -m unittest discover -s tests` → Ran 210 tests OK (skipped=1). numpy/pandas installed per requirements.txt.
- Fresh H10 block in `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` confirmed IMMATURE/NULL_DIFF: n_formations=1 (2026-09-30), n_high=0, n_low=0, n_mid=1, high_low_diff_net_1x=null, overlap_aware_uncertainty.status=IMMATURE. No frozen artifacts modified.
- Probe for November 2026 data vintage: `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11` → target_published=false, cutoff_gate=BLOCKED (record research_state/cutoff_probe/cutoff_probe_20261103T040041Z.json). Prior agent's steps 1–3 all re-verified; step 4 (re-run fresh block on unblocked cutoff) remains blocked.

## Situation
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged (608 formations, +0.6165 net 1x).
- Full test suite green: `python3 -m unittest discover -s tests` → Ran 210 tests OK (skipped=1).
- Free data refreshed through 2026-10-31; October cutoff gate UNBLOCKED (October 2026 monthly klines + fundingRate both HTTP 200).
- November 2026 daily klines/funding still not published (probe 2026-11: target_published=false, archive_alive=true, gate_met_by_month_end=true, cutoff_gate=BLOCKED). Fresh block remains immature/blocked.
- H10 preregistered at `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H10_FRESH_FORWARD_BLOCK_v1.md`, hypothesis H10 in registry (CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / EVALUATED_NULL_DIFF_IMMATURE).
- Fresh block evaluated in `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/`: builds with 26 eligible assets (>=20) but IMMATURE/NULL_DIFF. n_formations=1 (2026-09-30), n_high=0, n_low=0, n_mid=1, high_low_diff_net_1x=null. Block sealed correctly; no frozen artifacts modified (canonical `forward_block/` untouched).

## Your task
1. Wait for November 2026 data vintage (cutoff advance past 2026-10-31): `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. When available (target_published=true), refresh data if needed (`python3 scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>`, free public only), re-run tests, verify H004V106 unchanged, then re-run the fresh sealed block:
   `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new cutoff> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/`
   (separate dir, never `forward_block/`). Do not relax 30-day maturity or MIN_ASSETS_DECILES=20.
2. If n_high>0 and n_low>0, report full results with overlap-aware/HAC uncertainty and apply the predeclared decision rule: require |high_low_diff_net_1x| above predeclared economic-significance threshold after costs AND Holm-significance across the complete multiple-testing family before any confirmatory claim. Neither raw p-values nor return alone may promote a winner.
3. Update frontier/registry/manifest/handoff with results; record any blocker with exact unmet requirements if still immature/blocked.

## Hard constraints
- Free public data only; historical research only; no live/paper trading.
- Preserve DISPERSION-001/002. Never modify canonical `forward_block/` or other frozen artifacts.
- Do not relax 30-day maturity, MIN_ASSETS_DECILES=20, or the state rule.
- Do not write "wait for a new experiment ID". If blocked by data maturity, wait for data vintage; do not fabricate formations/outcomes.
- Correct for complete declared multiple-testing family if promoting.

## Root cause (for awareness)
- 2026-10-28 missing from merged price index (Binance archive gap) shifts `last_allowed_formation` to 2026-09-30.
- `trailing_window_outer_deciles` requires ≥30 prior in-block dispersions to assign high/low states; fresh window is too short until November vintage matures.

## Latest probe (2026-11-03T04:00:41Z)
- probe-month 2026-11: target_published=false, control_month=2026-09 (control_ok=true), archive_alive=true, gate_met_by_month_end=true, cutoff_gate=BLOCKED. Record: research_state/cutoff_probe/cutoff_probe_20261103T040041Z.json. No new formations possible until November archive published.
