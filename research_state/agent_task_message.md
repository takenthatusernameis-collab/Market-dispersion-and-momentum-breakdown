## Initial task for next agent

Read `research_state/agent_handoff.md` (current session **2026-11-07T09:05Z**), this file, `AGENTS.md`, `docs/research_protocol.md`, and `prompts/continuous_research_operating_contract_v1.md`. Verify current state before acting.

### Verified state (2026-11-07T09:05Z)
- Prior task COMPLETE. Baseline: compileall EXIT=0; prereg audit pass=True (14/0/0); tests **279 OK, skipped=1**; fingerprint 0f53ad4bb765d0b1...; frozen hashes unchanged (H004V106 canonical `7234fc4e...`; H10 fresh IMMATURE `9bdee66f...`). November 2026 probe BLOCKED (do NOT re-probe before 2026-11-30). No confirmatory advance; k not advanced.
- Change this session: added `--look-number` positivity guard in `scripts/eval_forward_block.py::main()`. Refreshed verified-test snapshot.

### Immediate next action
1. Preserve blocker. Do not fabricate. Verify frozen hashes + tests/prereg audit before new work.
2. Do NOT re-probe November 2026 before 2026-11-30. Continue independent unblocked audit/test/doc/hygiene tasks; record in `research_state/session_verifications/` and update handoff + this task message.
3. After 2026-11-30 only: probe cutoff gate; if published, run fresh sealed block per protocol.
4. Never relax 30-day maturity, MIN_ASSETS_DECILES=20, trailing-decile state rule, or 0.05 threshold. Never open canonical sealed holdout. Never use today's rank as historical point-in-time truth.
5. Before sign-off: re-run compileall, prereg audit, tests; record verification; confirm frozen hashes unchanged. Update this file and handoff. Never write "wait for a new experiment ID."
