# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Mandate
Continue quantitative research. Historical-only, free-data-only. No live/paper trading. No paid services or secrets.

## State on handoff
- Full test suite runs in the default Python env (pandas+numpy installed): **44/44 tests PASS** (`python3 -m unittest discover -s tests`).
- Forward-block provenance repaired: committed `forward_block_evaluation.json` carried a stale `candidate_batch_validation.json` hash; re-ran `eval_forward_block.py --data-cutoff 2026-09-30`; outcomes byte-identical (n=608, high=61, low=90, high_low_diff_net_1x = 0.6165223953929935, date_last=2026-08-31). Block diff is only the provenance hash line.
- Frontier integrity repaired: `btc` and `eth` re-admitted to `candidates_verified` from existing panel evidence; verified=32, consistent with `expanding_universe_assets_with_cap_and_binance=32`.
- Candidate validation batch #2 run this session: all 25 BLOCKED. verified=32, blocked=216, remaining_discovered=6099, cursor=6497. Raw CoinMetrics CapMrktEstUSD fetched for alch, alcx, aleo, aleph, akro, akt (served on community tier but no Binance perpetual).
- DISPERSION-001/002 and all configs unchanged.

## Concrete next action
1. Continue DISPERSION-003 candidate validation in batches (`python3 scripts/validate_candidate_batch.py --limit 25`) — verified=32, blocked=216, remaining_discovered=6099, cursor=6497. Record exact counts after each batch.
2. On/after 2026-10-29 (or once the October 2026 Binance monthly archive publishes), re-check data cutoff via `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31`; proceed only when cutoff >= 2026-10-29.
3. When available, evaluate H004V106 on a fresh sealed forward block with completed 30-day outcomes only; compute overlap-aware uncertainty (HAC/Newey-West and/or block bootstrap).
4. Do not reuse the inspected canonical block as independent confirmation; treat it as development/exploratory evidence.
5. Run full test suite (`python3 -m unittest discover -s tests`); confirm DISPERSION-001/002 unchanged.
6. Update handoff + next task with concrete measurable outcomes.

## Blocker note (do not loop)
The cutoff gate is structural: 2026-10-29 has not occurred and the October 2026 archive is unpublished (still 404; not re-probed). If still blocked, preserve the blocker and move to an independent unblocked task (candidates, free-source discovery, validation, design, or red-team) per AGENTS.md rather than re-probing the same endpoint.
