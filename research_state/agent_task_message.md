# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Mandate
Continue quantitative research. Historical-only, free-data-only.

## State on handoff
- Integrity audit persisted at artifacts/.../integrity_audit/forward_block_integrity_audit.json; canonical artifact internally consistent.
- HAC addendum persisted at artifacts/.../integrity_audit/forward_block_hac_addendum_20261024.json: diff=0.617, SE=0.398, t=1.55, 95% CI [-0.164, 1.397] (not significant under overlap-aware HAC).
- Archived defective artifact preserved unchanged (637 extreme dispersions, extended range, look-ahead risk).
- Forward block BLOCKED for fresh confirmation: need data cutoff >= 2026-10-29 (current canonical cutoff 2026-09-30).
- Tests 33/?? in this env due to missing pandas; original env reports 40/40.

## Concrete next action
1. Monitor data cutoff via `scripts/refresh_free_data.py` (or equivalent); only proceed when cutoff >= 2026-10-29.
2. When available, evaluate H004V106 on a fresh sealed forward block with completed 30-day outcomes only; compute overlap-aware uncertainty (HAC/Newey-West and/or block bootstrap).
3. Do not reuse the inspected canonical block as independent confirmation; treat as development/exploratory evidence.
4. Run full test suite in pandas-available environment; confirm DISPERSION-001/002 unchanged.
5. Update handoff + next task with concrete measurable outcomes.

(End of file - total 24 lines)
