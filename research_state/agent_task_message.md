## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-11-02T05:33:38Z)

## Situation
Tests: `python3 -m unittest discover -s tests` -> 162 run, 162 OK, 0 failures (EXIT=0).

**ENVIRONMENT PREREQUISITE:** the bare runner interpreter does NOT ship with numpy/pandas even though `requirements.txt` declares them. Before running the suite, install:

    python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt

Canonical H004V106 forward block verified byte-unchanged: sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`, n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z. `research_state/hypothesis_registry.json` next_sequence_number 9 (H1..H9 present); H10 never allocated. Universe frontier exhausted at cursor 6347. Frozen artifacts untouched.

## Status: cutoff gate BLOCKED
Latest authoritative probe (`python3 scripts/probe_cutoff_gate.py --probe-month 2026-10`, 2026-11-02T05:33:38Z, record `research_state/cutoff_probe/cutoff_probe_20261102T053338Z.json`, EXIT=1): October 2026 monthly BTCUSDT klines HTTP 404 (0 bytes); October 2026 monthly BTCUSDT fundingRate HTTP 200 (943 bytes); October 2026 daily klines 2026-10-29/30/31 HTTP 200; September 2026 control HTTP 200. `target_published: false`, `cutoff_gate: BLOCKED`. Monthly klines not published; partial publication unusable. Adaptive-gate trigger NOT met. Do not loop on known failure. NOTE: the test suite stdout may carry a synthetic `"cutoff_gate": "UNBLOCKED"` line from `tests/test_cutoff_probe.py:138`; that is mock data (mocks `probe_month` and `Path.write_text`, hits no network, writes no record) — trust only real probe records under `research_state/cutoff_probe/`.

## Your task (blocked — preserve state)
1. Do NOT run refresh while gate is BLOCKED.
2. Preserve BLOCKED cutoff and H10 preregistration plan (allocate next_sequence_number 9->10 when unblocked).
3. When October 2026 Binance monthly archives publish (both monthly klines AND monthly fundingRate HTTP 200, cutoff >= 2026-10-29): confirm with probe (EXIT=0/UNBLOCKED), run `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31` (free public only), re-run tests, verify H004V106 unchanged (sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`), preregister H10 (9->10) with fresh sealed forward block (formations after 2026-09-29, strict 30-day maturity, HAC/overlap-aware), evaluate H10, update handoff/registry/manifest/frontier.
4. Do not modify `marketcap_panel_manifest.json`, `marketcap_panel.csv`, or the canonical forward block; do not reuse inspected H004V106 as confirmation.

## Hard constraints
- No look-ahead/fabrication/forward-fill/invented fills/silent exclusions/outcome-informed params/costs/hidden multiplicity/reuse of inspected holdout.
- Never shorten 30-day maturity; never change DISPERSION-001/002; never relax costs; no paid services/live/paper trading.
- H004V106 development/exploratory only; fresh sealed forward block required for any confirmatory claim.

## Concrete next action
Re-probe with `python3 scripts/probe_cutoff_gate.py --probe-month 2026-10`. If EXIT=0/UNBLOCKED, execute unblocked sequence; else preserve BLOCKED and update durable state.
" filePath">
/home/runner/work/Market-dispersion-and-momentum-breakdown/Market-dispersion-and-momentum-breakdown/research_state/agent_task_message.md