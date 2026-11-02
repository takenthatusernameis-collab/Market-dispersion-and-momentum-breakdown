## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-11-02T00:48:33Z)

## Situation
Tests: 161 run, 1 failure, 0 errors. Single failure `test_panel_start_end_match_csv_min_max` is a KNOWN CONSTRAINT (stale `marketcap_panel_manifest.json` rows; manifest is a frozen forward-block input — do not modify). All other 160 tests pass; 0 errors. Canonical H004V106 forward block verified byte-unchanged: sha256 `60a832fdf61d27b71a61b704394693bf7047c3960d69030c2026d701afc8fe59`, n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z. `research_state/hypothesis_registry.json` next_sequence_number 9 (H1..H9 present). No preregistration yet; H10 remains pending. Universe frontier exhausted at cursor 6347. Frozen artifacts untouched.

## Status: cutoff gate BLOCKED
Latest real probe (`python3 scripts/probe_cutoff_gate.py --probe-month 2026-10`, 2026-11-02T00:48:33Z, record `research_state/cutoff_probe/cutoff_probe_20261102T004833Z.json`, EXIT=1): October 2026 monthly BTCUSDT klines HTTP 404 (0 bytes); October 2026 monthly BTCUSDT fundingRate HTTP 200; September 2026 control HTTP 200. `target_published: false`, `cutoff_gate: BLOCKED`. The monthly klines archive has not published; partial publication unusable (`refresh_free_data.py` consumes the monthly klines zip). Adaptive-gate trigger NOT met. Do not loop on known failure.

## Your task (blocked — preserve state)
1. Do NOT run refresh while gate is BLOCKED.
2. Preserve BLOCKED cutoff and H10 preregistration plan (allocate next_sequence_number 9->10 when unblocked).
3. When October 2026 Binance monthly archives publish (both monthly klines AND monthly fundingRate HTTP 200, cutoff >= 2026-10-29): confirm with probe (expect EXIT=0/UNBLOCKED), then run `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31` (free public data only), re-run `python3 -m unittest discover -s tests`, verify H004V106 unchanged, preregister H10 (next_sequence_number 9->10) with fresh sealed forward block (formations after 2026-09-29, strict 30-day maturity, HAC/overlap-aware, only completed 30-day outcomes), evaluate H10 against the fresh block, update handoff/registry/manifest/frontier.
4. Do not modify `marketcap_panel_manifest.json`, `marketcap_panel.csv`, or the canonical forward block; do not reuse the inspected H004V106 block as confirmation.

## Hard constraints
- No look-ahead/fabrication/forward-fill/invented fills/silent exclusions/outcome-informed params/costs/hidden multiplicity/reuse of inspected holdout.
- Never shorten 30-day maturity; never change DISPERSION-001/002; never relax costs; no paid services/live/paper trading.
- H004V106 is development/exploratory only; fresh sealed forward block required for any confirmatory claim.

## Concrete next action
Re-probe monthly availability with `python3 scripts/probe_cutoff_gate.py --probe-month 2026-10`. If EXIT=0/UNBLOCKED, execute the unblocked sequence above; otherwise preserve BLOCKED and update durable state.
