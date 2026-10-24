# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Mandate
Continue quantitative research in this repository without waiting for a new manual experiment ID. Follow prompts/continuous_research_operating_contract_v1.md and docs/research_protocol.md. Historical-only, free-data-only, no live/paper orders.

## State on handoff
- Tests pass (21/21). DISPERSION-001/002 artifacts unchanged (only tests/__pycache__ modified).
- DISPERSION-003 grid complete: 216 OK / 0 BLOCKED / 0 FAILED / 0 Holm-rejected. Forward block H004V106 (2025-01-01..2026-09-29): high_low_diff_net_1x = -0.0097.
- Red-team/regression pass complete: 21/21 tests green.
- **BLOCKER (forward block):** Next sealed forward block for H004V106 requires formation dates >= 2026-09-30 with 30-day horizon; need completed UTC observations through at least 2026-10-29. Current data cutoff is 2026-10-23T00:00:00Z (frozen in artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json). **Do not compute outcomes prematurely.**
- Universe: 32 cap+Binance assets verified. Frontier cursor=76, 822 eligible candidates, rank_frontier_exhausted=false. `candidates_discovered` queue empty per universe_frontier.json.

## First measurable deliverable
1. **Data cutoff monitoring** — Monitor free data sources for completed UTC candles. Evaluate the next sealed block only when cutoff >= 2026-10-29, preselected anchor H004V106 only, no parameter/asset/threshold/cost search. Record cutoff/date in handoff when evaluated.
2. **Frontier expansion** — If new candidates appear via documented discovery, populate `candidates_discovered` boundedly and validate with `scripts/validate_candidate_batch.py`. If none, proceed to integrity checks.
3. **Integrity check** — Confirm DISPERSION-001/002 unchanged; run tests; update handoff and next task with one concrete measurable action.

## Mandatory sequencing
1. Monitor/refresh data cutoff; when >= 2026-10-29 evaluate sealed block H004V106 (preselected only).
2. Advance universe frontier if new verified assets exist; persist hashes/provenance.
3. Update hypothesis_registry.json if warranted (H6 is candidate).
4. Verify tests (21/21); confirm DISPERSION-001/002 unchanged; update handoff and next task.

## Definition of done
Provide verified test output, explicit forward-block blocker record (dates/cutoff/horizon), confirmation DISPERSION-001/002 unchanged, updated handoff + next task with one concrete next action. Do not declare program complete.
