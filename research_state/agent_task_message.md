# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Mandate
Continue quantitative research. Historical-only, free-data-only. No live/paper trading. No paid services or secrets.

## State on handoff
- Full test suite now runs in the default Python env (pandas+numpy installed): **44/44 tests PASS**.
- Forward-block provenance repaired: committed `forward_block_evaluation.json` carried a stale `candidate_batch_validation.json` hash (`e0ae358af7…`) vs on-disk `25bc1592c5…`. Re-ran `eval_forward_block.py --data-cutoff 2026-09-30`; outcomes byte-identical (n=608, high=61, low=90, high_low_diff_net_1x = 0.6165223953929935, date_last=2026-08-31). Block diff is only the provenance hash line.
- **Frontier integrity repaired:** `btc` and `eth` existed in validated panels but were missing from `candidates_verified`, making `expanding_universe_assets_with_cap_and_binance=32` inconsistent with `len(candidates_verified)=30`. Re-admitted from existing panel evidence (no fresh probe); verified=32 now consistent.
- Candidate validation batch of 25 run this session: all 25 BLOCKED. verified=32, blocked=191, remaining_discovered=6124, cursor=6472.
- DISPERSION-001/002 and all configs unchanged.

## Concrete next action
1. On/after 2026-10-29 (or once the October 2026 Binance monthly archive publishes), re-check data cutoff via `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31`; proceed only when cutoff >= 2026-10-29.
2. When available, evaluate H004V106 on a fresh sealed forward block with completed 30-day outcomes only; compute overlap-aware uncertainty (HAC/Newey-West and/or block bootstrap).
3. Do not reuse the inspected canonical block as independent confirmation; treat it as development/exploratory evidence.
4. Continue independent DISPRESSION-003 candidate validation in batches (`python3 scripts/validate_candidate_batch.py --limit 25`) — verified=32, blocked=191, remaining_discovered=6124.
5. Run full test suite (`python3 -m unittest discover -s tests`); confirm DISPERSION-001/002 unchanged.
6. Update handoff + next task with concrete measurable outcomes.

## Blocker note (do not loop)
The cutoff gate is structural: 2026-10-29 has not occurred and the October 2026 archive is unpublished. If still blocked, preserve the blocker and move to an independent unblocked task (candidates, free-source discovery, validation, design, or red-team) per AGENTS.md rather than re-probing the same endpoint.