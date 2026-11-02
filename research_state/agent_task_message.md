## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-11-02T09:43:30Z)

## Situation
- Cutoff gate: UNBLOCKED. Real probe `python3 scripts/probe_cutoff_gate.py --probe-month 2026-10` (2026-11-02T09:22:09Z, record `research_state/cutoff_probe/cutoff_probe_20261102T092118Z.json`, EXIT=0): October 2026 monthly BTCUSDT klines HTTP 200 AND monthly BTCUSDT fundingRate HTTP 200; target_published true.
- Data refresh DONE this session: `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31` (free public only). BTCUSDT/ETHUSDT price now through 2026-10; the other 30 assets' October monthly zips are unpublished, so their klines/funding panels end 2026-09-30; marketcap panel spans 2023-01-01..2026-10-31.
- Tests: `python3 -m unittest discover -s tests` -> 167 run, 1 FAILURE (`test_forward_block_hashes_match_files_on_disk`), 0 errors, EXIT=1. That single failure is EXPECTED and correct post-refresh: the canonical block's recorded panel input hashes are pre-October while panels advanced; it signals the cutoff advanced past the frozen block. Do NOT tamper with the canonical forward block. All other 166 tests pass.
- Canonical H004V106 forward block verified byte-unchanged vs `git show HEAD:` sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` (n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z). It is development/exploratory evidence only; NOT a fresh holdout.
- Environment precondition: `python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt` (numpy 2.5.4 / pandas 3.1.0); guard `tests/test_requirements_importable.py` fails the build if any declared dependency is missing.
- Universe frontier: exhausted at cursor 6347, 0 newly discovered.
- `research_state/hypothesis_registry.json`: next_sequence_number 10 (H1..H10 present). H10 allocated and preregistered at `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H10_FRESH_FORWARD_BLOCK_v1.md`.

## Status: H10 fresh sealed forward block — BLOCKED by data availability
H10 was preregistered (methodology locked before computation): fresh sealed forward block, formations strictly after 2026-09-29, strict 30-day maturity, HAC/overlap-aware inference on completed 30-day outcomes only, evaluated via `scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff 2026-10-31 --output-dir <fresh dir>`.

The build was ATTEMPTED and returned BLOCKED: "no formations passed the data gate." Root cause: only BTCUSDT and ETHUSDT have complete October 2026 forward horizons (2 assets); the other 30 Binance klines panels end 2026-09-30 because their October monthly zips are unpublished. Max eligible assets with a complete 30-day forward horizon = 2 < MIN_ASSETS_DECILES=20.

H10 remains CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / BLOCKED. It CANNOT be evaluated with current data. The blocker is preserved; do NOT relax the 30-day maturity or the >=20 asset minimum, and do NOT loop on the known data-absence failure.

## Your task
1. Do NOT re-seal, overwrite, or modify the canonical forward block (`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`); do not reuse inspected H004V106 as confirmation. Do not modify `marketcap_panel_manifest.json` / `marketcap_panel.csv` except via the sanctioned refresh.
2. Monitor for October 2026 price-panel publication for the remaining 30 assets (their October monthly Binance zips). When >=20 assets have complete October 2026 forward horizons:
   - Confirm with probe (EXIT=0/UNBLOCKED).
   - Retry `scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff 2026-10-31 --output-dir <fresh dir>` (separate dir, never canonical).
   - Evaluate H10: report n_formations, n_high, n_low, n_mid, high_low_diff_net_1x, HAC/overlap-aware interval. A confirmatory claim requires BOTH |high_low_diff_net_1x| above a predeclared economic-significance threshold (after costs) AND Holm-significance across the complete declared multiple-testing family. Never promote from raw p-values or return alone.
   - Update handoff/registry/manifest/frontier.
3. If October price panels for the remaining assets do not publish, preserve the H10 blocker and continue with another independent task (tests, validation, design, or red-team). Do not fabricate metrics, silently drop candidates, or change grids after seeing outcomes.
4. Maintain read-only state verification + durable-state refresh after any work.

## Hard constraints
- Free public data only. No paid services/trials/compute, secrets, exchange credentials or non-public endpoints.
- Historical research only. Never place orders or deploy live/paper trading.
- No look-ahead, fabrication, forward-fill, invented fills, silent exclusions, outcome-informed parameters/costs, hidden multiplicity, or reuse of an inspected holdout as fresh confirmation.
- Never shorten 30-day maturity; never relax costs; never change DISPERSION-001/002 grids after seeing outcomes.
- October 2026 ranks are NOT backfilled as historical ranks; state the fresh block's narrower universe/coverage explicitly if used.
- Synthetic fixtures are software tests, never market evidence.

## Concrete next action
Check whether the remaining 30 assets' October 2026 Binance monthly zips have published (>=20 assets with complete October forward horizons). If yes, run the unblocked H10 fresh-block sequence above. If no, preserve the H10 blocker (documented in handoff and preregistration) and proceed to another bounded independent task; never write "wait for a new experiment ID."
