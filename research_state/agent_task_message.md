## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-11-02T10:07:17Z)

## Situation
- Cutoff gate: UNBLOCKED (probe `research_state/cutoff_probe/cutoff_probe_20261102T092118Z.json`, EXIT=0; Oct 2026 BTCUSDT klines+funding HTTP 200).
- Data refresh done; marketcap panel advanced to 2026-10-31. Binance price/funding panels in `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/` currently end 2026-09-30 for most assets (no Oct 2026 data present). Only partial publication observed; fresh H10 block remains blocked.
- Tests: `python3 -m unittest discover -s tests` -> 167 run, 1 FAILURE (`test_forward_block_hashes_match_files_on_disk`) expected post-refresh (canonical block hashes pre-date refresh). Do NOT tamper with canonical H004V106 forward block (`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`), sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`.
- H10: preregistered at `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H10_FRESH_FORWARD_BLOCK_v1.md`, registry status CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / BLOCKED.

## Status: H10 fresh sealed forward block — BLOCKED by data availability
Need >=20 assets with complete October 2026 forward horizons (30-day maturity). Current data has insufficient coverage (root cause: remaining 30 assets' October monthly zips not published). Blocker preserved; do NOT relax 30-day maturity or >=20 asset minimum.

## Your task
1. Do NOT modify canonical forward block or DISPERSION-001/002 grids. Do not reuse inspected H004V106 as confirmation.
2. Monitor for October 2026 price-panel publication (>=20 assets complete). When ready:
   - Confirm probe unblocked.
   - Retry `scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff 2026-10-31 --output-dir <fresh dir>` (separate dir).
   - Evaluate H10 per preregistration: report n_formations/high/low/mid, date_first/last/last_allowed_formation, high_low_diff_net_1x/gross, HAC/overlap-aware interval. Confirmatory claim requires BOTH |high_low_diff_net_1x| above predeclared economic threshold (after costs) AND Holm-significance across complete family. Never promote from raw p-values/return alone.
   - Update handoff/registry/manifest/frontier.
3. If not published, preserve blocker and do another independent bounded task (tests/validation/design/red-team). No fabrication/silent exclusion/grid changes.
4. Maintain read-only state verification + durable-state refresh.

## Hard constraints
- Free public data only; historical research only (no trading).
- No look-ahead/fabrication/forward-fill/invented fills/silent exclusions/outcome-informed params/costs/hidden multiplicity/reuse of inspected holdout.
- Never shorten 30-day maturity; never relax costs; never change DISPERSION-001/002 grids after seeing outcomes.
- October 2026 ranks not backfilled as historical ranks; state universe/coverage if used.
- Synthetic fixtures are tests only.

## Concrete next action
Check publication of remaining assets' October 2026 Binance monthly zips for >=20 assets with complete 30-day horizons. If yes run H10 fresh-block sequence; if no preserve blocker and proceed to another bounded independent task (do not ask for new experiment ID).
