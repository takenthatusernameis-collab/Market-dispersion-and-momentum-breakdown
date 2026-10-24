# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Mandate
Continue quantitative research in this repository without waiting for a new manual experiment ID. Follow prompts/continuous_research_operating_contract_v1.md and docs/research_protocol.md. Historical-only, free-data-only, no live/paper orders.

## State on handoff
- Tests pass (21/21).
- DISPERSION-003 forward block evaluation complete: 2025-01-01..2026-09-29, 637 formations, high_low_diff_net_1x=-0.0097. Artifact at artifacts/.../forward_block/forward_block_evaluation.json.
- Next sealed forward block (formation >=2026-09-30) is BLOCKED until data cutoff reaches 2026-10-29 (30-day horizon). Current cutoff 2026-10-23. Do not compute outcomes prematurely.
- Universe: 32 cap+Binance assets; frontier cursor=76, 822 eligible candidates, rank_frontier_exhausted=false.

## First measurable deliverable
Advance candidate frontier: process next batch of eligible candidates, verify cap+Binance assets, add verified ones to refresh_free_data.py, regenerate marketcap_panel.csv. Record blocker for forward block until 2026-10-29.

## Mandatory sequencing
1. Validate prior artifacts intact; never overwrite DISPERSION-001/002.
2. Advance universe_frontier.json cursor; persist verified assets.
3. Red-team inference/cost/funding/holdout/resume logic; add regression tests.
4. Update hypothesis_registry.json (H6) if warranted.
5. Verify tests 21/21; confirm DISPERSION-001/002 unchanged; update handoff and next task.

## Definition of done
Provide verified test output, candidate batch result, updated frontier, blocker record for forward block, confirmation DISPERSION-001/002 unchanged, one next concrete task. Do not declare program complete.
