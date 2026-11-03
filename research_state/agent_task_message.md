## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 H10 (2026-11-03T06:12:37Z)

## Session verification (2026-11-03T06:12:37Z)
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` verified byte-unchanged vs disk and `git show HEAD`.
- Full test suite green: `python3 -m unittest discover -s tests` -> Ran 210 tests OK (skipped=1).
- Re-probed November 2026: `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11` -> target_published=false, cutoff_gate=BLOCKED (record `research_state/cutoff_probe/cutoff_probe_20261103T061237Z.json`).
- October 2026 IS published (UNBLOCKED). Fresh H10 block in `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` remains IMMATURE/NULL_DIFF: n_formations=1, n_high=0, n_low=0, diff null; canonical `forward_block/` unchanged. No frozen artifacts modified.

## Situation
- October 2026 vintage is published but does NOT unblock H10 evaluation. Structural cause: Binance kline archive gap at 2026-10-28 shifts `last_allowed_formation` back (cutoff_loc-horizon) and trailing-decile classification needs >=30 prior in-block dispersions; block window cannot yield n_high>0 AND n_low>0 with current cutoff. November 2026 vintage (and likely December) required.
- Today is 2026-11-03; November 2026 monthly archive not yet published (month not over). Genuine data-maturity blocker.

## Your task
1. Wait for the November 2026 data vintage: re-probe with `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. When target_published=true, refresh data if needed via `python3 scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>` (free public only), re-run `python3 -m unittest discover -s tests`, verify H004V106 unchanged, then re-run the fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`):
   `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new cutoff> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/`
   Do not relax 30-day maturity, MIN_ASSETS_DECILES=20, or trailing-decile state rule.
2. If n_high>0 and n_low>0, report full results with overlap-aware/HAC uncertainty and apply predeclared decision rule (|diff|>economic significance after costs AND Holm across complete family) before confirmatory claim.
3. If still IMMATURE (n_high==0 or n_low==0), record exact blocker (unmet: n_high>0 AND n_low>0; reason: insufficient classifiable formations after trailing burn-in), update frontier/registry/manifest/handoff, wait for next vintage — do not relax rules, fabricate formations/outcomes, or open canonical sealed holdout.
4. Update frontier/registry/manifest/handoff with results/blocker.

## Hard constraints
- Free public data only; historical research only; no live/paper trading.
- Preserve DISPERSION-001/002. Never modify canonical `forward_block/` or other frozen artifacts.
- Do not relax 30-day maturity, MIN_ASSETS_DECILES=20, or state rule.
- Do not write "wait for a new experiment ID". If blocked by data maturity, wait for data vintage.
- Correct for complete declared multiple-testing family if promoting.

## Latest probe (2026-11-03T06:12:37Z)
- probe-month 2026-11: target_published=false, cutoff_gate=BLOCKED (record `research_state/cutoff_probe/cutoff_probe_20261103T061237Z.json`).
- Tests green (210 OK, 1 skipped). H004V106 unchanged. Fresh H10 still IMMATURE/NULL_DIFF. No frozen artifacts modified.
