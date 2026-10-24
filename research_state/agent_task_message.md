# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Mandate
Continue quantitative research in this repository without waiting for a new manual experiment ID. Follow prompts/continuous_research_operating_contract_v1.md and docs/research_protocol.md. Historical-only, free-data-only, no live/paper orders.

## State on handoff
- Tests pass (21/21). DISPERSION-001/002 artifacts unchanged (git diff clean except pycache).
- DISPERSION-003 grid complete: 216 OK / 0 BLOCKED / 0 FAILED / 0 Holm-rejected. Forward block H004V106: 2025-01-01..2026-09-29, 637 formations, high_low_diff_net_1x=-0.0097.
- **BLOCKER (forward block):** Next sealed forward block for H004V106 requires formation dates >= 2026-09-30 with 30-day horizon; need completed UTC observations through at least 2026-10-29. Current data cutoff is 2026-10-23T00:00:00Z (frozen in artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json). **Do not compute outcomes prematurely.** When cutoff >= 2026-10-29, evaluate only preselected anchor H004V106 on the sealed block without parameter/asset/threshold/cost search.
- Universe: 32 cap+Binance assets verified. Frontier cursor=76, 822 eligible candidates, rank_frontier_exhausted=false. candidates_discovered queue empty (validation: discovered=0, to_process=0, verified=30, blocked=21).

## First measurable deliverable
1. **Red-team & regression tests** — Run red-team checks (inference/cost/funding/holdout/resume). Add regression tests for gaps found (focus: dispersion accounting, bootstrap validity with overlapping horizons, cost/funding sign/convention, holdout separation, checkpoint/resume idempotency). Verify 21/21 (or more) tests pass.
2. **Frontier expansion** — candidates_discovered empty; do not fabricate. Populate boundedly via documented discovery if new candidates found; validate with scripts/validate_candidate_batch.py; else proceed.
3. **Data cutoff monitoring** — Refresh free data only when completed UTC candles are available; do not evaluate the next sealed block before 2026-10-29 cutoff.
4. **Integrity check** — Confirm DISPERSION-001/002 unchanged; update handoff and next task with one concrete measurable action.

## Mandatory sequencing
1. Red-team inference/cost/funding/holdout/resume logic; add regression tests.
2. Advance universe frontier if new verified assets exist; persist hashes/provenance.
3. Update hypothesis_registry.json (H6) if warranted.
4. Verify tests; confirm DISPERSION-001/002 unchanged; update handoff and next task.

## Definition of done
Provide verified test output, red-team findings/regression tests added, explicit forward-block blocker record (dates/cutoff/horizon), confirmation DISPERSION-001/002 unchanged, updated handoff + next task with one concrete next action. Do not declare program complete.
