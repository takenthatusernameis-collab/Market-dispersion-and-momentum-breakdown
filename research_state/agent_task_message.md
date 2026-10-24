# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Mandate
Continue quantitative research. Historical-only, free-data-only.

## State on handoff
- Integrity audit persisted at artifacts/.../integrity_audit/forward_block_integrity_audit.json; canonical artifact internally consistent.
- Archived defective artifact preserved unchanged (637 extreme dispersions, extended range).
- Forward block still BLOCKED: cutoff 2026-10-23 < 2026-10-29.
- Tests 33/?? in this env due to missing pandas; original env reports 40/40.

## Concrete next action
1. Compute overlap-aware (HAC/Newey-West) uncertainty for canonical high-low difference; persist audit addendum.
2. Monitor data cutoff via scripts/refresh_free_data.py; evaluate H004V106 only when >= 2026-10-29.
3. Run full test suite in pandas-available environment; confirm DISPERSION-001/002 unchanged.
4. Update handoff + next task with one concrete measurable action.
