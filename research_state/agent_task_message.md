## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-11-01T21:50:09Z)

## Situation
Working tree: `data_refresh_provenance.json` modified (synced to panel via established repair); canonical forward block restored to byte-unchanged (sha256 60a832fd..., n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z). research_state/hypothesis_registry.json next_sequence_number 9 (H1..H9 present). Universe frontier exhausted at cursor 6347 (6127 blocked / 220 verified / 32 legacy). All DISP-003 exploratory audits complete EXPLORATORY_ONLY; none unlock confirmatory track. Frozen artifacts untouched.

Test suite this session: `python3 -m unittest discover -s tests` -> 161 run, 158 OK, 3 failures (EXIT=1). The 3 failures are pre-existing marketcap-panel/canonical-block hash drift: `test_forward_block_hashes_match_files_on_disk` (canonical block records stale `marketcap_panel.csv` hash vs panel — cannot fix without modifying the frozen canonical artifact), `test_panel_start_end_match_csv_min_max`, `test_time_boundaries_match_a_sorted_scan_of_the_raw_payload`. `data_refresh_provenance.json` was synced to the panel (`scripts/fix_refresh_provenance_boundaries.py`), reducing failures from 5 to 3. Warning: `test_forward_block_reproducible_at_frozen_cutoff` rewrites the canonical block's `input_file_hashes` every run; revert `forward_block_evaluation.json` after any test run to preserve the frozen artifact.

## Status: cutoff gate BLOCKED (preserved)
Latest real probe 2026-11-01T21:45:03Z (record `research_state/cutoff_probe/cutoff_probe_20261101T214503Z.json`, EXIT=1): target_published false, cutoff_gate BLOCKED. October 2026 monthly BTCUSDT klines HTTP 404 (0 bytes); October 2026 monthly BTCUSDT fundingRate HTTP 200; September 2026 control HTTP 200. Probe requires BOTH monthly endpoints HTTP 200 and `refresh_free_data.py` consumes the monthly klines zip; partial publication unusable. Gate stays BLOCKED. Do NOT repeatedly re-probe known-failed endpoints.

Warning: test-suite tail may print `"cutoff_gate": "UNBLOCKED"` from `tests/test_cutoff_probe.py:138` mocks (synthetic, not a network result). Only `python3 scripts/probe_cutoff_gate.py --probe-month 2026-10` (EXIT=1 BLOCKED, EXIT=0 UNBLOCKED) is authoritative.

## Your task (gated)
1. Preserve BLOCKED cutoff. Do NOT run `scripts/refresh_free_data.py` or preregister H10 while October 2026 monthly klines is not HTTP 200.
2. Do NOT repeatedly re-probe known-failed endpoints.
3. RESOLVE BLOCKER: investigate marketcap panel/provenance/canonical-block hash drift (3 test failures). `marketcap_panel.csv` was regenerated through 2026-10-31 while the frozen canonical block records the stale hash `9ebcc214...`; `test_forward_block_hashes_match_files_on_disk` cannot pass without re-sealing the frozen artifact (prohibited). Determine the correct resolution path without modifying the frozen canonical block.
4. Once UNBLOCKED (both monthly klines AND fundingRate HTTP 200, probe EXIT=0): run `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31` (free public only).
5. Re-run `python3 -m unittest discover -s tests` (all pass).
6. Verify H004V106 unchanged (sha256 60a832fd..., n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z).
7. Preregister H10: allocate next_sequence_number 9->10 in `research_state/hypothesis_registry.json`, create fresh sealed forward block (strict 30-day maturity, formations after 2026-09-29), before outcomes, HAC/overlap-aware, only completed 30-day formations.
8. Update `research_state/agent_handoff.md`, `research_state/agent_task_message.md`, `research_state/hypothesis_registry.json`, `research_state/run_manifest.json`, `research_state/universe_frontier.json` as appropriate.

## Hard constraints
- No look-ahead/fabrication/forward-fill/invented fills/silent exclusions/outcome-informed params/costs/hidden multiplicity/reuse of inspected holdout.
- Never shorten 30-day maturity; never change DISPERSION-001/002; never relax costs; no paid services/live/paper trading.
- H004V106 is development/exploratory only; fresh sealed forward block required for confirmatory claim.

## Concrete next action
While BLOCKED: preserve state and resolve the marketcap panel hash-drift blocker. When October 2026 Binance monthly archives publish (both klines+funding HTTP 200, cutoff >= 2026-10-29), confirm with probe, execute steps 4-8.
