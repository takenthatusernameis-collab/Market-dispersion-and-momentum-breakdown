# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Mandate
Continue quantitative research. Historical-only, free-data-only. No live/paper trading. No paid services or secrets.

## State on handoff
- Integrity audit + HAC addendum preserved; canonical artifact internally consistent (n=608, high=61, low=90, high-low net=0.6165, CI [-0.164, 1.397], not significant under overlap-aware HAC).
- Archived defective artifact preserved unchanged.
- Forward block BLOCKED for fresh confirmation: need data cutoff >= 2026-10-29 (current 2026-09-30). As of 2026-10-24, October 2026 Binance monthly archive returns HTTP 404. Structural gate; do not loop on it.
- Sealed-block input provenance RESOLVED; sealed block immutable.
- Candidate validation progress: verified=30, blocked=141, remaining_discovered=6174 (batch of 25 run this session).
- DISPERSION-001/002 unchanged.

## Concrete next action
1. On/after 2026-10-29 (or once the October 2026 Binance monthly archive publishes), re-check data cutoff via `scripts/refresh_free_data.py` with `--price-end 2026-10-31 --cap-end 2026-10-31`; proceed only when cutoff >= 2026-10-29.
2. When available, evaluate H004V106 on a fresh sealed forward block with completed 30-day outcomes only; compute overlap-aware uncertainty (HAC/Newey-West and/or block bootstrap).
3. Do not reuse the inspected canonical block as independent confirmation; treat it as development/exploratory evidence.
4. Continue independent DISPERSION-003 candidate validation in batches (`python3 scripts/validate_candidate_batch.py --limit 25`) — verified=30, blocked=141, remaining_discovered=6174.
5. Run full test suite in pandas-available environment; confirm DISPERSION-001/002 unchanged.
6. Update handoff + next task with concrete measurable outcomes.

## Blocker note (do not loop)
The cutoff gate is structural: 2026-10-29 has not occurred and the October 2026 archive is unpublished. If still blocked, preserve the blocker and move to an independent unblocked task (candidates, free-source discovery, validation, design, or red-team) per AGENTS.md rather than re-probing the same endpoint.
