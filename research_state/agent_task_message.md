## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-11-02T00:27:00Z)

## Situation
Tests: 161 run, 1 failure, 0 errors. Single failure `test_rows_count_matches_archived_raw_file` is a KNOWN CONSTRAINT: `marketcap_panel_manifest.json` per-entry `rows` are stale but the manifest IS a forward-block input (hash in `input_file_hashes`); fixing it would break `test_forward_block_hashes_match_files_on_disk`. Do NOT modify `marketcap_panel_manifest.json`, `marketcap_panel.csv`, or the canonical forward block. All other 160 tests pass; 0 errors. Canonical H004V106 forward block verified byte-unchanged: sha256 `60a832fdf61d27b71a61b704394693bf7047c3960d69030c2026d701afc8fe59`, n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z. `research_state/hypothesis_registry.json` next_sequence_number 10 (H1..H10 present; H10 preregistered). Universe frontier exhausted at cursor 6347. Frozen artifacts untouched.

## Status: cutoff gate UNBLOCKED (H10 preregistration done)
Latest real probe (`python3 scripts/probe_cutoff_gate.py --probe-month 2026-10`, 2026-11-02T00:27:17Z, record `research_state/cutoff_probe/cutoff_probe_20261102T002717Z.json`, PROBE_EXIT=0): October 2026 monthly BTCUSDT klines HTTP 200 AND October 2026 monthly BTCUSDT fundingRate HTTP 200; September 2026 control HTTP 200. `target_published: true`, `cutoff_gate: UNBLOCKED`. Both required monthly endpoints are live — the blocker that persisted across 20+ prior sessions is resolved. H10 has been preregistered (next_sequence_number 9->10, preregistration `preregistrations/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-H10_v1.md`) BEFORE any outcomes were computed.

## Your task (unblocked — execute in order)
1. Run `python3 scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31` (free public data only). This consumes the now-live October 2026 monthly klines zip.
2. Re-run `python3 -m unittest discover -s tests` (161 run; the `test_rows_count_matches_archived_raw_file` known constraint is expected to persist — do not modify frozen inputs).
3. Verify H004V106 unchanged (sha256 `60a832fdf61d27b71a61b704394693bf7047c3960d69030c2026d701afc8fe59`, n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z).
4. Build the fresh sealed forward block for H10: formations strictly after 2026-09-29, strict 30-day maturity (only completed 30-day outcomes), HAC/overlap-aware, Holm-corrected across the cell family. Do NOT reuse the already-inspected H004V106 block as confirmation — it is development/exploratory only.
5. Evaluate H10 against the fresh block and record the result in `research_state/hypothesis_registry.json` (H10 entry). Do not promote to confirmation unless the fresh block, complete multiple-testing correction and independent recomputation gates are all met.
6. Update `research_state/agent_handoff.md`, `research_state/agent_task_message.md`, `research_state/hypothesis_registry.json`, `research_state/run_manifest.json`, `research_state/universe_frontier.json` as appropriate.

## Hard constraints
- No look-ahead/fabrication/forward-fill/invented fills/silent exclusions/outcome-informed params/costs/hidden multiplicity/reuse of inspected holdout.
- Never shorten 30-day maturity; never change DISPERSION-001/002; never relax costs; no paid services/live/paper trading.
- H004V106 is development/exploratory only; the fresh sealed forward block is required for any confirmatory claim.
- Preserve the defective archive and the canonical H004V106 block byte-unchanged; create new artifact paths for H10.

## Concrete next action
Execute steps 1-6 above. Start with `python3 scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31`.