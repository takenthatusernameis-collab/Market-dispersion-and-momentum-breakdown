# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Mandate
Continue quantitative research in this repository without waiting for a new manual experiment ID. Follow prompts/continuous_research_operating_contract_v1.md and docs/research_protocol.md. Historical-only, free-data-only, no live/paper orders.

## State on handoff
- Tests pass (21/21).
- DISPERSION-003 forward block evaluation complete: 2025-01-01..2026-09-29, 637 formations, high_low_diff_net_1x=-0.0097. Artifact at artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json.
- Next sealed forward block (formation >=2026-09-30) is BLOCKED until data cutoff reaches 2026-10-29 (30-day horizon). Current cutoff 2026-10-23. Do not compute outcomes prematurely.
- Universe: 32 cap+Binance assets (verified). Frontier cursor=76, 822 eligible candidates, rank_frontier_exhausted=false. candidates_discovered queue empty; validation run completed (verified=30, blocked=21).
- candidate_batch_validation.json written; universe_frontier.json updated.

## First measurable deliverable
1. Record explicit forward-block blocker in handoff/task with dates/cutoff/horizon and do not evaluate premature block.
2. If candidates_discovered is non-empty, validate next batch with validate_candidate_batch.py (bounded). Otherwise, assess frontier expansion path: document whether new candidates need to be discovered/populated into candidates_discovered (respecting no fixed top-N cutoff) and proceed with discovery or with tests/red-team if none available.
3. Run red-team checks (inference/cost/funding/holdout/resume) and add regression tests if gaps found.
4. Verify tests still pass; confirm DISPERSION-001/002 artifacts unchanged; update handoff and next task.

## Mandatory sequencing
1. Validate prior artifacts intact; never overwrite DISPERSION-001/002.
2. Advance universe frontier state if new verified assets exist; persist hashes/provenance.
3. Red-team inference/cost/funding/holdout/resume logic; add regression tests.
4. Update hypothesis_registry.json (H6) if warranted.
5. Verify tests 21/21; confirm DISPERSION-001/002 unchanged; update handoff and next task.

## Definition of done
Provide verified test output, candidate batch/result state, blocker record for forward block, confirmation DISPERSION-001/002 unchanged, updated handoff + next task with one concrete next action. Do not declare program complete.

(End of file)
