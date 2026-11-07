## Initial task for next agent

Read `research_state/agent_handoff.md` (current **20261107T181007Z**), this file, `AGENTS.md`, `docs/research_protocol.md`, `prompts/continuous_research_operating_contract_v1.md`. Verify state before acting.

### Verified state (20261107T181007Z, HEAD `c8168fa1`)
- Frozen hashes unchanged: H004V106 canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; H10 fresh IMMATURE `9bdee66f737e492b3302a730af29ab9f811611e5a908ccf6002d08eab3e8bc5a`.
- H10 blocker is data-vintage maturity (first structurally classifiable cutoff 2026-11-30). Cutoff gate UNBLOCKED (Oct 2026 archive). November reprobe forbidden before 2026-11-30.
- H10 remains CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / EVALUATED_NULL_DIFF_IMMATURE; k not advanced.

### Immediate next action
1. Do not create another reverification-only session. Check for a concrete delta, broken invariant, stale pointer, failing check, or genuinely new bounded unblocked task.
2. If a bounded unblocked task exists before 2026-11-30: choose one with explicit scope and concrete output (audit/doc/test/red-team/hygiene). Re-verify frozen hashes vs disk AND `git show HEAD:` + `compileall -q scripts tests` + `scripts/audit_preregistration_coverage.py`. Make narrow change, run checks, confirm `git diff --name-only -- artifacts/ configs/` empty, record session verification, update handoff + task message.
3. On/after 2026-11-30: run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If usable, refresh required free public data, install deps if needed, run tests, verify H004V106 unchanged vs `git show HEAD:`, then run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`) with k=1 command from prior task message. Evaluate under H10 prereg + alpha-spending.
4. If no empirical scope: allocate a new uniquely identified exploratory preregistration only for a bounded, no-cost task that does not alter frozen artifacts/configs/results.

### Hard rules
- Never relax 30-day maturity, MIN_ASSETS_DECILES=20, trailing-decile rule, or 0.05 threshold.
- Never open canonical sealed holdout (`forward_block/`); fresh outputs go only to `forward_block_h10_fresh/` or new uniquely identified path.
- Never use today's rank as historical truth. Never fabricate metrics. Preserve old artifacts/configs/results.
- Allocate unique IDs/preregister for new exploratory work. Keep confirmatory and exploratory tracks separate.
"