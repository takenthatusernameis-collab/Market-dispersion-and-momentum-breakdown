# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Mandate
Continue quantitative research. Historical-only, free-data-only. No live/paper trading. No paid services or secrets.

## State on handoff
- Integrity audit persisted at artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/forward_block_integrity_audit.json; canonical artifact internally consistent.
- HAC addendum persisted at artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/forward_block_hac_addendum_20261024.json: diff=0.6165, SE=0.3982, t=1.548, 95% CI [-0.164, 1.397] (not significant under overlap-aware HAC).
- Archived defective artifact preserved unchanged (637 extreme dispersions, extended range, look-ahead risk).
- Forward block BLOCKED for fresh confirmation: need data cutoff >= 2026-10-29 (current canonical cutoff 2026-09-30). As of 2026-10-24T16:56:53Z, the threshold date is still in the future and the October 2026 Binance monthly archive returns HTTP 404 (not yet published). No fresh block available.
- Tests unavailable in this env (missing pandas/numpy/pytest); original env reports 40/40.

## Concrete next action
1. On/after 2026-10-29 (or once the October 2026 Binance monthly archive publishes), re-check data cutoff via `scripts/refresh_free_data.py` with `--price-end 2026-10-31 --cap-end 2026-10-31`; proceed only when cutoff >= 2026-10-29.
2. When available, evaluate H004V106 on a fresh sealed forward block with completed 30-day outcomes only; compute overlap-aware uncertainty (HAC/Newey-West and/or block bootstrap).
3. Do not reuse the inspected canonical block as independent confirmation; treat it as development/exploratory evidence.
4. Run full test suite in pandas-available environment; confirm DISPERSION-001/002 unchanged.
5. Update handoff + next task with concrete measurable outcomes.

## Blocker note (do not loop)
The cutoff gate is structural: 2026-10-29 has not occurred and the October 2026 archive is unpublished. If this check is repeated and still blocked, preserve the blocker and move to an independent unblocked task (candidates, free-source discovery, validation, design, or red-team) per AGENTS.md rather than re-probing the same endpoint.
