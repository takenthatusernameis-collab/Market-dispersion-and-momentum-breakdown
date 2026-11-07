## Initial task for next agent

Read `research_state/agent_handoff.md` (current **2026-11-07T11:23:45Z**), this file, `AGENTS.md`, `docs/research_protocol.md`, and `prompts/continuous_research_operating_contract_v1.md`. Verify state before acting.

### Verified state (2026-11-07T11:23:45Z, dep-light env: pandas/numpy not installed)
- Prior task COMPLETE. Baseline: `python3 -m compileall -q scripts tests` EXIT=0; `python3 scripts/audit_preregistration_coverage.py` pass=True (14/0/0). `git status` clean (before your changes). HEAD `1f3843d9`.
- Frozen hashes unchanged: H004V106 canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; H10 fresh IMMATURE `9bdee66f737e492b3302a730af29ab9f811611e5a908ccf6002d08eab3e8bc5a`.
- Dep-light guards, pre-outcome inference-protocol gaps, evaluator↔prereg alignment, doc/consistency audits, and hash/manifest verification complete per handoff. Cutoff probe BLOCKED. No confirmatory advance; k not advanced.

### Immediate next action
1. **Preserve blocker.** Re-verify frozen hashes + compileall + prereg audit before any new work.
2. **Do NOT re-probe November 2026 before 2026-11-30.** Do not repeat baseline-only checks without new scope. Continue only if a *new* unblocked audit/doc/hygiene task arises (e.g., newly identified doc/contract drift, a specific test-hardening gap not already covered, or manifest/hash verification with a concrete delta). Record results in `research_state/session_verifications/` and update handoff + this message.
3. **After 2026-11-30 only:** `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If published: refresh free public data if needed, install deps, run tests, verify H004V106 unchanged vs `git show HEAD:`, run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`) with `--forward-block-start 2026-09-30 --data-cutoff 2026-11-30 --output-dir ... --look-number 1` (k=1). Require ALL of `n_high>0 AND n_low>0`, `n_high>=5 AND n_low>=5`, `|high_low_diff_net_1x| >= 0.05`, and Holm-significance across the complete 216-cell family at `alpha_k = 0.05/(k*(k+1))` before any confirmatory claim. If IMMATURE, record blocker and do not advance k.
4. **Hard rules:** Never relax 30-day maturity, `MIN_ASSETS_DECILES=20`, trailing-decile rule, or 0.05 threshold. Never open canonical sealed holdout. Never use today's rank as historical truth. Never fabricate metrics. Update handoff + this message before sign-off. **Never write "wait for a new experiment ID."**
