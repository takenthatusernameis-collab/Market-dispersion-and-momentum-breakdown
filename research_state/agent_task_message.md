# NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-10-31T18:33:22Z)

## Situation
Program active and verified. HEAD `022c442` (branch `main` tracks origin/main; checkpoint chain `4130eb9`..`7023749`..`022c442`). Working tree contains only tracked `__pycache__` timestamp drift and untracked bytecode caches — no source changes; `git diff --stat -- ':!**/__pycache__'` empty for tracked non-pycache files. `scripts/alpha_spending.py` committed clean — single implementation, no duplicate defs, no scratch code. Full suite `python3 -m unittest discover -s tests` -> 145 run, 145 OK, 0 failures. Canonical H004V106 sealed forward block verified byte-unchanged by direct field read: n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z. `research_state/hypothesis_registry.json` `next_sequence_number`: 9 (H1..H9 present; H1 immutable NOT_SUPPORTED_AS_ROBUST_EDGE; H2-H9 candidate/exploratory). Universe frontier exhausted at cursor 6347. All DISP-003 exploratory audits complete EXPLORATORY_ONLY (CLUSTER_DOMINATED, ROLLING_FRAGILE, TAIL_ROBUST, temporal-stability, cluster-bootstrap CI spanning zero); none unlocks the confirmatory track.

## Blocker (respect it — do not re-probe)
October 2026 Binance public archive is unpublished; data-cutoff gate BLOCKED (requires cutoff >= 2026-10-29 on a published archive). Price/funding panels end 2026-09-30. Today is 2026-10-31; October month not yet closed; archive expected early November. Last direct probe 2026-10-31T17:45Z: October 2026 klines/funding all HTTP 404 (endpoint live; miss is genuine absence). Do not re-probe while unpublished. Adaptive-gate trigger not met (single route, temporary timing — not three distinct failed routes).

## Prior task status
**DONE**: Prior agent task (alpha_spending regression fix) complete. `scripts/alpha_spending.py` is the single clean implementation committed at HEAD `022c442`; full test suite passes (145/145 OK).

## Your task
1. **Respect cutoff**: Do not re-probe the October 2026 Binance archive before publication.
2. **When unblocked** (October 2026 Binance archive published, cutoff >= 2026-10-29):
   - a. Confirm publication (October 2026 klines/funding return HTTP 200).
   - b. Run `scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>` (free public data only; no paid services/secrets).
   - c. Re-run `python3 -m unittest discover -s tests` and confirm all pass.
   - d. Verify integrity: confirm H004V106 canonical forward block unchanged (n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z). H004V106 is development/exploratory evidence only (already inspected); cannot confirm any hypothesis.
   - e. Preregister H10: allocate `next_sequence_number` 9->10 in `research_state/hypothesis_registry.json`, preregister a fresh sealed forward block (strict 30-day maturity, formations after 2026-09-29) before computing outcomes, HAC/overlap-aware, evaluate only completed 30-day formations.
   - f. Update `research_state/agent_handoff.md`, `research_state/agent_task_message.md`, `research_state/hypothesis_registry.json`, `research_state/run_manifest.json`, `research_state/universe_frontier.json` as appropriate.

## Hard constraints (never relax)
- No look-ahead, fabricated/forward-filled observations, invented fills, silent sample exclusions.
- Never shorten 30-day maturity; never inspect sealed holdout as fresh evidence; never change DISPERSION-001/002; never relax costs; never call paid services; no live/paper trading.
- H004V106 (+0.617) is development/exploratory evidence only (already inspected); cannot confirm hypothesis. Genuinely fresh sealed forward block (formations after 2026-09-29) required for confirmatory claim.
- Historical research only.

## Concrete next action for this session
Nothing bounded and unblocked remains. Preserve the BLOCKED cutoff and the H10 preregistration plan. When the October 2026 Binance archive publishes, execute steps 2a-2f and update durable state.
EOF
