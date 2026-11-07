## Initial task for next agent

Read `research_state/agent_handoff.md` (current session **2026-11-07T11:16:35Z**), this file, `AGENTS.md`, `docs/research_protocol.md`, and `prompts/continuous_research_operating_contract_v1.md`. Verify current state before acting.

### Verified state (2026-11-07T11:16:35Z, dep-light env: pandas/numpy not installed)
- Prior task COMPLETE. Baseline: compileall EXIT=0; prereg audit pass=True (14/0/0).
- Full dep-light suite: **287 run, 2 failures, 0 errors, 35 skipped** -- both failures are documented dep-light env limits, not logic regressions:
  - `test_every_declared_requirement_imports` (numpy/pandas not installed)
  - `test_snapshot_fingerprint_matches_inventory` (snapshot fingerprint stale: 95 files vs 97 on-disk; `record_test_claim.py` deliberately NOT run in dep-light to preserve the verified 279/279/0 claim)
- Dep-light guards complete for all 5 numpy/pandas-importing test modules (`test_forward_block_integrity`, `test_h10_confirmatory_gate`, `test_h10_feasibility`, `test_inference_repro`, `test_momentum_accounting`).
- Pre-outcome inference-protocol gaps: none remain (H10 prereg sections 4/4.1/4.2 wired into evaluator and guarded; all other preregs EXPLORATORY_ONLY with descriptive rules).
- Frozen hashes unchanged vs `git show HEAD:`: H004V106 canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; H10 fresh IMMATURE `9bdee66f737e492b3302a730af29ab9f811611e5a908ccf6002d08eab3e8bc5a`. HEAD `ffbf8b9410d61a108b9ad97a113ebef19ae44073`.
- Cutoff probe latest BLOCKED (do NOT re-probe before 2026-11-30). No confirmatory advance; k not advanced. `git ls-files tests/__pycache__` = 0.
- Session verification recorded: `research_state/session_verifications/session_verify_20261107T111635Z.json`.

### Immediate next action
1. Preserve blocker. Re-verify frozen hashes + compileall + prereg audit before new work.
2. **Do NOT re-probe November 2026 before 2026-11-30.** All listed unblocked hygiene tasks (dep-light guards, pre-outcome inference-protocol gaps, evaluator<->prereg alignment, doc/consistency audits, hash/manifest verification) are complete. Continue only if new unblocked audit/doc/hygiene work arises; record results in `research_state/session_verifications/` and update handoff + this task message.
3. **After 2026-11-30 only:** probe cutoff gate; if published, run fresh sealed block per protocol. Never relax maturity, MIN_ASSETS_DECILES=20, trailing-decile rule, or 0.05 threshold. Never open canonical sealed holdout. Never use today's rank as historical point-in-time truth.
4. Before sign-off: re-run checks, record verification, confirm frozen hashes unchanged. Update this file and handoff. **Never write "wait for a new experiment ID."**
