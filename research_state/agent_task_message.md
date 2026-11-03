## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 H10 (2026-11-03T18:31Z)

## Situation
- Today 2026-11-03. November 2026 not published (month not over). Genuine data-maturity blocker; cutoff gate BLOCKED.
- Latest REAL probe: research_state/cutoff_probe/cutoff_probe_20261103T154136Z.json (2026-11-03T15:41:36Z): November 2026 monthly klines AND monthly fundingRate HTTP 404; daily 11-28/29/30/31 HTTP 404; September 2026 control HTTP 200 (archive alive, miss genuine month-not-over). target_published=false, cutoff_gate=BLOCKED, probe_exit=1.
- Do NOT treat suite output as a gate decision: tests/test_cutoff_probe.py mocks probe.main() and prints a synthetic "cutoff_gate": "UNBLOCKED" line while writing NOTHING to disk (tests/test_cutoff_probe.py:147-160). Trust only real records under research_state/cutoff_probe/; every real November 2026 record on disk reports BLOCKED.
- Structural feasibility (DISP-003-H10-FEASIBILITY-001): October 2026 cannot unblock H10. Fresh block window gives n_formations=1 (2026-09-30), high/low unassignable (need >=31 formations/trailing-decile states). November 2026 is structurally the first cutoff that could classify high/low (~31 formations projected at cutoff 2026-11-30). Artifact: integrity_audit/H10_feasibility_analysis_20261103.json; tests tests/test_h10_feasibility.py.
- Canonical H004V106 sha256 `7234fc4e...` unchanged; sealed forward block (608 formations, data_cutoff 2026-09-30, last formation 2026-08-31, high_low_diff_net_1x +0.6165) is development/exploratory evidence only -- already inspected, not independent confirmation.
- Environment: this session installed numpy/pandas from requirements.txt; suite green (218 run, OK, skipped=1). Future sessions: run `python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt` before the suite if ModuleNotFoundError appears.
- Frontier exhausted (cursor 6347); grid ledger 216/216 OK; no bounded unblocked work remains besides the November 2026 maturity gate.

## Your task
1. Do NOT re-probe November 2026 before cutoff >= 2026-11-29. A same-day repeat of the 15:41:36Z probe is a repeat of a known failure, not a distinct failed route; the adaptive-gate trigger is NOT met (single timing route). Do not start an exploratory track.
2. When target_published=true: refresh free public data if needed, re-run `python3 -m unittest discover -s tests`, verify H004V106 unchanged vs `git show HEAD:`, run fresh sealed block `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new cutoff> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`).
3. If n_high>0 and n_low>0, report full results with overlap-aware/HAC uncertainty and apply the predeclared decision rule before any confirmatory claim.
4. If still IMMATURE, record exact blocker (probe results + formation counts/states), update frontier/registry/manifest/handoff, wait for next vintage.
5. Update frontier/registry/manifest/handoff with results/blocker. Leave a concrete next action. Never write "wait for a new experiment ID." If blocked by data maturity, wait for data vintage.

## Hard constraints
- Free public data only; historical research only; no live/paper trading.
- Preserve DISPERSION-001/002. Never modify canonical `forward_block/` or other frozen artifacts.
- Do not relax 30-day maturity, MIN_ASSETS_DECILES=20, or trailing-decile state rule.
- Correct for complete declared multiple-testing family if promoting.
