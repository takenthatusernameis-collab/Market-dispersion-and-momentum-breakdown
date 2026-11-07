## Initial task for next agent

Read `research_state/agent_handoff.md` (current session **2026-11-07T11:14Z**), this file, `AGENTS.md`, `docs/research_protocol.md`, and `prompts/continuous_research_operating_contract_v1.md`. Verify current state before acting.

### Verified state (2026-11-07T11:14Z, dep-light env: pandas/numpy not installed)
- Prior task COMPLETE. Baseline: compileall EXIT=0; prereg audit pass=True (14/0/0). 287 run, 2 failures, 0 errors, 35 skipped (dep-light env limits).
- Frozen hashes unchanged: H004V106 canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; H10 fresh IMMATURE `9bdee66f737e492b3302a730af29ab9f811611e5a908ccf6002d08eab3e8bc5a`. HEAD `eccd947dd73c8d372794a4fbe9f94d1360496e87`.
- Cutoff probe latest BLOCKED (do NOT re-probe before 2026-11-30). No confirmatory advance; k not advanced.

### Immediate next action
1. Preserve blocker. Re-verify frozen hashes + compileall + prereg audit before new work.
2. **Do NOT re-probe November 2026 before 2026-11-30.** Continue independent unblocked audit/test/doc/hygiene tasks (dep-light guards for remaining numpy-importing tests, pre-outcome inference-protocol gaps, evaluator↔prereg alignment, doc/consistency audits, hash/manifest verification). Record results in `research_state/session_verifications/` and update handoff + this task message.
3. **After 2026-11-30 only:** probe cutoff gate; if published, run fresh sealed block per protocol. Never relax maturity, MIN_ASSETS_DECILES=20, trailing-decile rule, or 0.05 threshold. Never open canonical sealed holdout. Never use today's rank as historical point-in-time truth.
4. Before sign-off: re-run checks, record verification, confirm frozen hashes unchanged. Update this file and handoff. **Never write "wait for a new experiment ID."**
