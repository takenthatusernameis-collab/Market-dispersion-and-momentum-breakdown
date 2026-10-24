# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Mandate
Continue quantitative research in this repository without waiting for a new manual experiment ID. Follow prompts/continuous_research_operating_contract_v1.md and docs/research_protocol.md. Historical-only, free-data-only, no live/paper orders.

## State on handoff
- Tests pass (21/21).
- DISPERSION-003 forward block evaluation complete: 2025-01-01..2026-09-29, 637 formations, high_low_diff_net_1x=-0.0097. Artifact at artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json.
- **BLOCKER (forward block):** Next sealed forward block for H004V106 requires formation dates >= 2026-09-30 with 30-day horizon; need completed UTC observations through at least 2026-10-29. Current data cutoff is 2026-10-23T00:00:00Z (frozen in the forward block artifact). **Do not compute outcomes prematurely.** When cutoff >= 2026-10-29, evaluate only preselected anchor H004V106 on the sealed block without parameter/asset/threshold/cost search.
- Universe: 32 cap+Binance assets (verified). Frontier cursor=76, 822 eligible candidates, rank_frontier_exhausted=false. **candidates_discovered queue is currently empty** (validation completed: discovered=0, to_process=0, verified=30, blocked=21). candidate_batch_validation.json written; universe_frontier.json updated.

## First measurable deliverable
1. **Record blocker** - Explicitly record the forward-block blocker (dates/cutoff/horizon/anchor) in handoff/task. Do not evaluate premature block.
2. **Assess frontier expansion** - candidates_discovered is empty. Assess whether new candidates need to be discovered/populated into candidates_discovered (respecting no fixed top-N cutoff). If needed, populate boundedly and validate with `scripts/validate_candidate_batch.py`; if not needed, proceed to red-team/tests without fabricating candidates.
3. **Red-team & regression tests** - Run red-team checks (inference/cost/funding/holdout/resume). Add regression tests for any gaps found (focus: dispersion accounting, bootstrap validity with overlapping horizons, cost/funding sign/convention, holdout separation, checkpoint/resume idempotency).
4. **Verify integrity** - Verify tests still pass (21/21); confirm DISPERSION-001/002 artifacts unchanged (git diff); update handoff and next task with a concrete measurable action.

## Mandatory sequencing
1. Validate prior artifacts intact; never overwrite DISPERSION-001/002.
2. Advance universe frontier state if new verified assets exist; persist hashes/provenance.
3. Red-team inference/cost/funding/holdout/resume logic; add regression tests.
4. Update hypothesis_registry.json (H6) if warranted.
5. Verify tests 21/21; confirm DISPERSION-001/002 unchanged; update handoff and next task.

## Definition of done
Provide verified test output, candidate batch/result state, explicit blocker record for forward block (with dates/cutoff/horizon), confirmation DISPERSION-001/002 unchanged, updated handoff + next task with one concrete next action. Do not declare program complete.

(End of file)
