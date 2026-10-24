# Initial Task Message — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Current task
Continue candidate validation for DISPERSION-003 in bounded batches of 25.

## Command
`python3 scripts/validate_candidate_batch.py --limit 25`

## Starting state
- verified=134, blocked=3164, remaining_discovered=3049, cursor=9547
- Validation record: artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/candidate_batch_validation.json (3172 entries; 104 verified, 3068 blocked from DISPERSION-003 batches). The 30 seed verified assets (1inch, aave, ada, avax, bnb, link, sol, etc.) originate from DISPERSION-001/002 and are NOT in this record — that is expected. Record-level reconcile: verified = record verified (104) + 30 seeds = 134.
- Frontier: research_state/universe_frontier.json

## Record after each batch
Log exact verified/blocked/remaining_discovered/cursor counts. Append nothing to the validation record manually — the script handles accumulation.

## Secondary task (time-gated)
On/after 2026-10-29, re-check data cutoff via `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31`. If cutoff >= 2026-10-29, preregister and evaluate H004V106 on a fresh sealed forward block with HAC/overlap-aware uncertainty, computing only completed 30-day outcomes. Do not reuse the inspected canonical block as independent confirmation.

## Standing constraints
- Free public data only. No paid services, secrets, or exchange credentials.
- Historical research only. Never place orders or deploy live/paper trading.
- Use point-in-time membership/ranks, contract mapping and listing/delisting status.
- Preserve DISPERSION-001/002 configs, inputs, artifacts and findings unchanged.
- Run full test suite (`python3 -m unittest discover -s tests`) before finishing.
- Record every cell, including negative, null, incomplete, invalid, failed and not-run states with reason.
- Do not re-probe the October 2026 Binance monthly archive (still 404); it is a structural blocker, not a retryable failure.

## Definition of done
- One or more validation batches completed with exact counts recorded.
- Test suite 45/45 PASS; DISPERSION-001/002 unchanged.
- Handoff + task message updated with concrete measurable outcomes.

(End of file - total 34 lines)