# NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-10-31T08:55:48Z)

## Situation
Program active and verified. HEAD `e3e2cfe` (local checkpoint commit; branch tracks origin/main); only `__pycache__` bytecode caches uncommitted. Tests `python3 -m unittest discover -s tests` -> 135 run, 135 OK, 0 failures (re-verified 2026-10-31T08:55Z). Canonical H004V106 sealed forward block verified from disk: n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z. hypothesis_registry.json `next_sequence_number`: 9 (H1..H9 present; tests pin it at 9). Universe frontier exhausted at cursor 6347 (catalog walked, 0 newly discovered).

## Blocker (respect it — do not re-probe)
The October 2026 Binance public archive is unpublished, so the data-cutoff gate is BLOCKED (requires cutoff >= 2026-10-29 on a published archive). The price/funding panels end 2026-09-30. Re-probed once this session (2026-10-31T08:08Z) by direct curl to data.binance.vision: BTCUSDT/ETHUSDT/BNBUSDT October 2026 klines and BTCUSDT October 2026 funding all HTTP 404; September 2026 BTCUSDT klines returns HTTP 200, so the endpoint is live and the miss is a genuine absence of the October file. Do not re-probe the October archive while it is unpublished; wait for publication, then act once. No bounded no-cost untested task is currently available; all DISP-003 exploratory audits are complete and EXPLORATORY_ONLY. Preserve the blocker.

## Your task (once the archive publishes / cutoff unblocks)
1. Confirm the October 2026 Binance archive is published (cutoff >= 2026-10-29). Do not re-probe before then.
2. Run `scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>` using the published October month-end dates (free public data only; no paid services, no secrets).
3. Re-run `python3 -m unittest discover -s tests` and confirm 135 run, 135 OK, 0 failures.
4. Confirm H004V106 canonical forward block remains byte-unchanged: n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z.
5. Preregister a fresh sealed forward block (strict 30-day maturity) for the new data under a new registry experiment ID: allocate H10 by setting `next_sequence_number` from 9 to 10 in `research_state/hypothesis_registry.json`, write the preregistration before computing outcomes, evaluate HAC/overlap-aware on completed 30-day formations only.
6. Update `research_state/agent_handoff.md`, `research_state/agent_task_message.md`, `research_state/hypothesis_registry.json`, `research_state/run_manifest.json`, and `research_state/universe_frontier.json` as appropriate.

## Hard constraints (never relax)
- No look-ahead, fabricated or forward-filled observations, invented fills, silent sample exclusions.
- Never shorten the 30-day maturity; never inspect the sealed holdout as fresh evidence; never change DISPERSION-001/002; never relax costs; never call paid services; no live/paper trading.
- H004V106 (+0.617) is development/exploratory evidence only — already inspected; cannot confirm any hypothesis. A genuinely fresh sealed forward block (formations after 2026-09-29) is required for any confirmatory claim.
- Historical research only.

## Concrete next action for this session (none)
No unblocked action is available this session: the October 2026 archive is unpublished and re-probing is forbidden while it is absent; the frontier is exhausted and all DISP-003 exploratory audits are complete. State files were re-verified and timestamps updated; hypothesis_registry.json, run_manifest.json and universe_frontier.json are unchanged. Next action: when the October 2026 Binance archive publishes (cutoff >= 2026-10-29), execute steps 1-6 above with H10.
