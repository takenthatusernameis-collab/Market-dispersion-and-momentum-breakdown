## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-11-01T22:01:00Z)

## Situation
Tests restored to green: `python3 -m unittest discover -s tests` -> 161 run, 161 OK, 0 failures. Fixed marketcap panel/provenance/canonical-block hash drift by restoring frozen-input artifacts to match the sealed forward block (restored `marketcap_panel.csv`, `marketcap_panel_manifest.json`, related raw CoinMetrics files, `data_refresh_provenance.json`, and other sealed inputs to the state recorded at block seal `b5cb0941`). Canonical H004V106 forward block verified byte-unchanged: sha256 `60a832fdf61d27b71a61b704394693bf7047c3960d69030c2026d701afc8fe59`, n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z. `research_state/hypothesis_registry.json` next_sequence_number 9 (H1..H9 present). Universe frontier exhausted at cursor 6347 (6127 blocked / 220 verified / 32 legacy). All DISP-003 exploratory audits complete EXPLORATORY_ONLY; none unlock confirmatory track. Frozen artifacts untouched.

## Status: cutoff gate BLOCKED (preserved)
Latest real probe (from tests): October 2026 monthly BTCUSDT klines HTTP 404; October 2026 monthly BTCUSDT fundingRate HTTP 200; September 2026 control HTTP 200. `target_published: false`, `cutoff_gate: BLOCKED`. Probe requires BOTH monthly endpoints HTTP 200 and `scripts/refresh_free_data.py` consumes the monthly klines zip; partial publication unusable. Gate stays BLOCKED. Do NOT repeatedly re-probe known-failed endpoints.
Warning: test-suite tail may print `"cutoff_gate": "UNBLOCKED"` from mocks (synthetic). Only `python3 scripts/probe_cutoff_gate.py --probe-month 2026-10` (EXIT=1 BLOCKED, EXIT=0 UNBLOCKED) is authoritative.

## Your task (gated)
1. Preserve BLOCKED cutoff. Do NOT run `scripts/refresh_free_data.py` or preregister H10 while October 2026 monthly klines is not HTTP 200.
2. Do NOT repeatedly re-probe known-failed endpoints.
3. Keep tests green (161/161). Do not modify frozen canonical artifacts.
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
Tests green, cutoff BLOCKED, marketcap hash-drift resolved. Wait for October 2026 Binance monthly archives (both klines+funding HTTP 200). When published, confirm with probe, execute steps 4-8.
