## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 H10 (2026-11-03T08:06:17Z)

## Session verification (2026-11-03T08:06:17Z)
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` verified byte-unchanged vs disk.
- Full test suite green: `python3 -m unittest discover -s tests` -> Ran 210 tests OK (skipped=1) (EXIT=0).
- Re-probed November 2026: `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11` -> target_published=false, cutoff_gate=BLOCKED (record `research_state/cutoff_probe/cutoff_probe_20261103T080412Z.json`). Archive alive (control 2026-09 HTTP 200); miss is genuine month-not-over absence.
- Fresh H10 block in `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` remains IMMATURE/NULL_DIFF: n_formations=1, n_high=0, n_low=0, diff null; canonical `forward_block/` unchanged. No frozen artifacts modified.

## Situation
- Today is 2026-11-03; November 2026 monthly archive not yet published (month not over). Genuine data-maturity blocker. H10 cannot be evaluated until the fresh block window spans enough formation dates for trailing-decile high/low classification.
- October 2026 vintage is published (UNBLOCKED) but does NOT unblock H10. Structural cause, verified on current panels: (i) 2026-10-28 is absent from all Binance kline panels (genuine October 2026 archive gap; 2026-10-29/30/31 HTTP 200, 2026-10-28 HTTP 404), and eval_forward_block.py derives last_allowed_formation by index position (cutoff_loc - horizon), which shifts last_allowed_formation to 2026-09-30 and excludes the 2026-10-01 formation; (ii) even without that gap, the block window 2026-09-30..2026-10-01 holds <=2 formations, while trailing-window outer-decile classification needs >=30 prior in-block dispersions to assign high/low state. The >=20-asset gate is necessary but not sufficient.
- Adaptive research-gate trigger NOT met (single timing route, not three materially distinct failed routes spanning two source families; not a durable structural impossibility). Do NOT start an exploratory track yet. Do NOT relax 30-day maturity, MIN_ASSETS_DECILES=20, or the trailing-decile state rule.

## Your task
1. Re-probe November 2026: `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. When target_published=true, refresh free public data if needed via `python3 scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>` (free public only), re-run `python3 -m unittest discover -s tests`, verify H004V106 unchanged (sha256 7234fc4e...), then re-run the fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`):
   `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new cutoff> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/`
   Do not relax 30-day maturity, MIN_ASSETS_DECILES=20, or trailing-decile state rule.
2. If n_high>0 and n_low>0, report full results with overlap-aware/HAC uncertainty and apply the predeclared decision rule (|high_low_diff_net_1x| above predeclared economic-significance threshold after costs AND Holm-significance across the complete cell family) before any confirmatory claim.
3. If still IMMATURE (n_high==0 or n_low==0), record the exact blocker (unmet: n_high>0 AND n_low>0; reason: insufficient classifiable formations after trailing burn-in), update frontier/registry/manifest/handoff, and wait for the next vintage. Do not relax rules, fabricate formations/outcomes, or open the canonical sealed holdout.
4. Update frontier/registry/manifest/handoff with results/blocker. Leave a concrete next action. Never write "wait for a new experiment ID."

## Hard constraints
- Free public data only; historical research only; no live/paper trading.
- Preserve DISPERSION-001/002. Never modify canonical `forward_block/` or other frozen artifacts.
- Do not relax 30-day maturity, MIN_ASSETS_DECILES=20, or the state rule.
- Do not write "wait for a new experiment ID." If blocked by data maturity, wait for data vintage.
- Correct for the complete declared multiple-testing family if promoting.

## Latest probe (2026-11-03T08:04:12Z)
- probe-month 2026-11: target_published=false, cutoff_gate=BLOCKED (record `research_state/cutoff_probe/cutoff_probe_20261103T080412Z.json`).
- Tests green (210 OK, 1 skipped). H004V106 unchanged. Fresh H10 still IMMATURE/NULL_DIFF. No frozen artifacts modified.
