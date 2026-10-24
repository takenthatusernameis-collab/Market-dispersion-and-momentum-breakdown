# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Mandate
Continue quantitative research. Historical-only, free-data-only. No live/paper trading. No paid services or secrets.

## State on handoff
- Full test suite: **45/45 tests PASS** (`python3 -m unittest discover -s tests`).
- Candidate validation batch #24 run (cursor 7572 → 7597): 25 candidates processed, 1 VERIFIED (crv), 24 BLOCKED; verified=75, blocked=1273, remaining_discovered=4999, cursor=7597. Validation record updated at artifacts/.../data/panels/candidate_batch_validation.json.
- Cutoff gate: BLOCKED (structural). Today 2026-10-24; gate requires cutoff >= 2026-10-29. October 2026 Binance monthly archive still 404; not re-probed per blocker note. Existing sealed forward block (cutoff 2026-09-30, last formation 2026-08-31) is development/exploratory evidence only; not reused as independent confirmation.
- DISPERSION-001/002 unchanged (no code or artifact modifications; git diff empty).
- Forward block + integrity audit artifacts unchanged (git diff empty).

## Concrete next action
1. Continue DISPERSION-003 candidate validation in batches (`python3 scripts/validate_candidate_batch.py --limit 25`) — verified=75, blocked=1273, remaining_discovered=4999, cursor=7597. Record exact counts after each batch.
2. On/after 2026-10-29 (or once the October 2026 Binance monthly archive publishes), re-check data cutoff via `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31`; proceed only when cutoff >= 2026-10-29. Then preregister/evaluate H004V106 on a fresh sealed forward block with HAC/overlap-aware uncertainty, computing only completed 30-day outcomes.
3. Do not reuse the inspected canonical block as independent confirmation; treat it as development/exploratory evidence.
4. Run full test suite (`python3 -m unittest discover -s tests`); confirm DISPERSION-001/002 unchanged.
5. Update handoff + next task with concrete measurable outcomes.

## Blocker note (do not loop)
The cutoff gate is structural: 2026-10-29 has not occurred and the October 2026 archive is unpublished (still 404; not re-probed). If still blocked, preserve the blocker and move to an independent unblocked task (candidates, free-source discovery, validation, design, or red-team) per AGENTS.md rather than re-probing the same endpoint.
