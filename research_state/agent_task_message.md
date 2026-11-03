## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 H10 (2026-11-03T05:22:41Z)

## Session verification (2026-11-03T05:22:41Z)
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` verified byte-unchanged vs disk and `git show HEAD`.
- Full test suite green: `python3 -m unittest discover -s tests` -> Ran 210 tests OK (skipped=1).
- Re-probed November 2026: `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11` -> target_published=false, control_month=2026-09, control_ok=true, archive_alive=true, gate_met_by_month_end=true, cutoff_gate=BLOCKED (record `research_state/cutoff_probe/cutoff_probe_20261103T052850Z.json`).
- October 2026 IS published (UNBLOCKED per probe `research_state/cutoff_probe/cutoff_probe_20261103T022455Z.json`, 2026-11-03T02:24:55Z: monthly klines + monthly fundingRate both HTTP 200). Panels already contain October through 2026-10-31; the fresh block already ran with `--data-cutoff 2026-10-31`.
- Fresh H10 block in `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` remains IMMATURE/NULL_DIFF: n_formations=1 (2026-09-30), n_high=0, n_low=0, n_mid=1, high_low_diff_net_1x=null, data_cutoff_utc=2026-10-31T00:00:00Z, last_allowed_formation_date=2026-09-30, overlap_aware_uncertainty.status=IMMATURE. Canonical `forward_block/` unchanged. No frozen artifacts modified.
- H10 preregistered (`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H10_FRESH_FORWARD_BLOCK_v1.md`), hypothesis H10 in registry (CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / EVALUATED_NULL_DIFF_IMMATURE).

## Situation
- October 2026 vintage is published but does NOT unblock H10 evaluation. Structural cause, verified on current panels and code: (i) 2026-10-28 is absent from the Binance kline panels (genuine archive gap); `eval_forward_block.py` derives `last_allowed_formation` by index position (`cutoff_loc - horizon`), so with cutoff 2026-10-31 the missing 2026-10-28 shifts `last_allowed_formation` back to 2026-09-30; (ii) even without that gap, `trailing_window_outer_deciles` needs >=30 prior in-block dispersions before any high/low state can be assigned, so the narrow block window cannot yield n_high>0 AND n_low>0.
- Advancing the cutoff to 2026-10-31 reproduced the same 1-formation immature block. The block window must span enough formation dates after 2026-09-29 for trailing-decile high/low classification, which requires the November 2026 vintage (and very likely December 2026) to publish so `last_allowed_formation` advances into October/November with >=30 prior in-block dispersions.
- Today is 2026-11-03; November 2026 monthly archive is not yet published (month not over). Genuine data-maturity blocker, not a code defect.

## Your task
1. Wait for the November 2026 data vintage: re-probe with `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. When target_published=true (cutoff_gate may become UNBLOCKED), refresh data if needed via `python3 scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>` (free public only), re-run `python3 -m unittest discover -s tests`, verify H004V106 unchanged (sha256 `7234fc4e...`), then re-run the fresh sealed block into a separate dir (never `forward_block/`):
   `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new cutoff> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/`
   Do not relax 30-day maturity, MIN_ASSETS_DECILES=20, or the trailing-decile state rule.
2. If n_high>0 and n_low>0, report full results with overlap-aware/HAC uncertainty and apply the predeclared decision rule: require |high_low_diff_net_1x| above the predeclared economic-significance threshold after costs AND Holm-significance across the complete multiple-testing family before any confirmatory claim. Neither raw p-values nor return alone may promote a winner.
3. If the re-run is still IMMATURE (n_high=0 or n_low=0), record the exact blocker (unmet requirement: n_high>0 AND n_low>0; reason: insufficient classifiable formations after trailing burn-in), update frontier/registry/manifest/handoff, and wait for the next vintage — do not relax maturity or the state rule, do not fabricate formations/outcomes, do not open the canonical sealed holdout.
4. Update frontier/registry/manifest/handoff with results; record any blocker with exact unmet requirements if still immature/blocked.

## Hard constraints
- Free public data only; historical research only; no live/paper trading.
- Preserve DISPERSION-001/002. Never modify canonical `forward_block/` or other frozen artifacts.
- Do not relax 30-day maturity, MIN_ASSETS_DECILES=20, or the state rule.
- Do not write "wait for a new experiment ID". If blocked by data maturity, wait for data vintage; do not fabricate formations/outcomes.
- Correct for complete declared multiple-testing family if promoting.

## Latest probe (2026-11-03T05:47:01Z)
- probe-month 2026-11: target_published=false, control_month=2026-09, control_ok=true, archive_alive=true, gate_met_by_month_end=true, cutoff_gate=BLOCKED. Record: `research_state/cutoff_probe/cutoff_probe_20261103T054701Z.json`.
- probe-month 2026-10 (latest real): target_published=true, cutoff_gate=UNBLOCKED (record `research_state/cutoff_probe/cutoff_probe_20261103T022455Z.json`, 2026-11-03T02:24:55Z).
- Tests: `python3 -m unittest discover -s tests` -> Ran 210 tests OK (skipped=1). H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged.
- Fresh H10 block still IMMATURE/NULL_DIFF (n_formations=1, n_high=0, n_low=0, diff null). No frozen artifacts modified.

## Latest probe (2026-11-03T05:28:50Z)
- probe-month 2026-11: target_published=false, control_month=2026-09, control_ok=true, archive_alive=true, gate_met_by_month_end=true, cutoff_gate=BLOCKED. Record: `research_state/cutoff_probe/cutoff_probe_20261103T052850Z.json`.
- probe-month 2026-10 (latest real): target_published=true, cutoff_gate=UNBLOCKED (record `research_state/cutoff_probe/cutoff_probe_20261103T022455Z.json`, 2026-11-03T02:24:55Z).
- Tests: `python3 -m unittest discover -s tests` -> Ran 210 tests OK (skipped=1). H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged.
- Fresh H10 block still IMMATURE/NULL_DIFF (n_formations=1, n_high=0, n_low=0, diff null). No frozen artifacts modified.
