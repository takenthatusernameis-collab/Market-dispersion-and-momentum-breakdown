## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 H10 (2026-11-03T18:44Z)

## Situation
- Today 2026-11-03. November 2026 not published (month not over). Genuine data-maturity blocker; cutoff gate BLOCKED until >= 2026-11-29.
- Latest REAL probe: research_state/cutoff_probe/cutoff_probe_20261103T154136Z.json (2026-11-03T15:41:36Z): November 2026 monthly klines AND monthly fundingRate HTTP 404; daily 11-28/29/30/31 HTTP 404; September 2026 control HTTP 200 (archive alive, miss genuine month-not-over). target_published=false, cutoff_gate=BLOCKED, probe_exit=1.
- Do NOT re-probe November 2026 before cutoff >= 2026-11-29. A same-day repeat of the 15:41:36Z probe is a repeat of a known failure, not a distinct failed route; the adaptive-gate trigger is NOT met (single timing route). Do not start an exploratory track.
- Do NOT treat suite output as a gate decision: tests/test_cutoff_probe.py mocks probe.main() and prints a synthetic "cutoff_gate": "UNBLOCKED" line while writing NOTHING to disk. Trust only real records under research_state/cutoff_probe/; every real November 2026 record on disk reports BLOCKED.
- Structural feasibility (DISP-003-H10-FEASIBILITY-001): October 2026 cannot unblock H10. Fresh block window gives n_formations=1 (2026-09-30), high/low unassignable (need >=31 formations/trailing-decile states). November 2026 is structurally the first cutoff that could classify high/low (~31 formations projected at cutoff 2026-11-30). Artifact: integrity_audit/H10_feasibility_analysis_20261103.json; tests tests/test_h10_feasibility.py.
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged; sealed forward block (608 formations, data_cutoff 2026-09-30, last formation 2026-08-31, high_low_diff_net_1x +0.6165) is development/exploratory evidence only -- already inspected, not independent confirmation.
- Fresh H10 block (artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json) unchanged: n_formations=1, n_high=0, n_low=0, n_mid=1, IMMATURE.
- Environment: numpy/pandas installed from requirements.txt; suite green (218 run, OK, skipped=1). If ModuleNotFoundError appears, run `python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt` before suite.
- Frontier exhausted (cursor 6347); grid ledger 218/218 OK; no bounded unblocked work remains besides the November 2026 maturity gate.

## Your task
1. Do NOT re-probe November 2026 before cutoff >= 2026-11-29. A same-day repeat of the 15:41:36Z probe is a repeat of a known failure, not a distinct failed route; the adaptive-gate trigger is NOT met. Do not start an exploratory track.
2. On/after 2026-11-29, re-probe: `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If target_published=true: refresh free public data if needed (`python3 scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>`), re-run `python3 -m unittest discover -s tests`, verify H004V106 unchanged vs `git show HEAD:`, run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`) via `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new cutoff> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/`.
3. If n_high>0 and n_low>0, report full results with overlap-aware/HAC uncertainty and apply the predeclared decision rule before any confirmatory claim.
4. If still IMMATURE (n_high==0 or n_low==0), record exact blocker (probe results + formation counts/states by decile/trailing window), update frontier/registry/manifest/handoff, and wait for next vintage. Do not relax maturity/decile rules.
5. Update frontier/registry/manifest/handoff with results/blocker. Leave a concrete next action. Never write "wait for a new experiment ID." If blocked by data maturity, wait for data vintage.

## Hard constraints
- Free public data only; historical research only; no live/paper trading.
- Preserve DISPERSION-001/002. Never modify canonical `forward_block/` or other frozen artifacts.
- Do not relax 30-day maturity, MIN_ASSETS_DECILES=20, or trailing-decile state rule.
- Correct for complete declared multiple-testing family if promoting.
- Trust only real probe records under research_state/cutoff_probe/ (ignore mocked test output).
