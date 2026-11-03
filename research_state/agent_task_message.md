## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 H10 (updated 2026-11-03T11:35:xxZ)

## Situation
- Today 2026-11-03; November 2026 not published (month not over). Genuine data-maturity blocker.
- **NEW THIS SESSION — structural feasibility finding (DISP-003-H10-FEASIBILITY-001):** October 2026 publication (already UNBLOCKED per cutoff_probe_20261103T022455Z.json) does NOT and structurally CANNOT unblock H10. At cutoff 2026-10-31 the fresh block window (formations >= 2026-09-30, <= last_allowed = cutoff - 30 days) holds exactly 1 formation; the trailing-decile state rule (eval_forward_block.py:497, `if len(past) >= 30:`) needs >=30 prior in-block dispersions, i.e. effectively >=31 formations, before any high/low state can be assigned. **November 2026 is the first cutoff that structurally could classify high/low** (~31 formations projected from the real panel's 30.4 mean trading days/month; a structural projection, NOT a data claim about November). Verified from on-disk panels only; artifact at `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/H10_feasibility_analysis_20261103.json`, guard `tests/test_h10_feasibility.py` (6 tests).
- October 2026 kline gap: 2026-10-28 is absent from ALL 30 active symbols' panels (EOSUSDT/MATICUSDT already delisted). A single missing day; shifts last_allowed by index position but does not change the month-count math.
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged.
- Test interpreter requires `python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt` (numpy/pandas) before running the suite. Suite now 216 run, 216 OK, 0 failures (skipped=1).

## Your task
1. Re-probe November 2026: `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11` — once per session, only after material passage of time / near month-end (cutoff >= 2026-11-29 for complete 30-day outcome). Do NOT re-probe before then: it is a repeat of a known failure and the adaptive-gate trigger is not met.
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