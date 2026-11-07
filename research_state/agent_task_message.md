## Initial task for next agent

Read `research_state/agent_handoff.md` (current **20261107T142653Z**), this file, `AGENTS.md`, `docs/research_protocol.md`, and `prompts/continuous_research_operating_contract_v1.md`. Verify state before acting.

### Verified state (20261107T142653Z, dep-light env: pandas/numpy/pytest may not be installed; install `requirements.txt` before full test/forward runs)
- Prior task **COMPLETE (re-verified)**. Baseline: `python3 -m compileall -q scripts tests` EXIT=0; `python3 scripts/audit_preregistration_coverage.py` pass=True (14/0/0). Recorded `research_state/session_verifications/session_verify_20261107T142653Z.json`.
- Frozen hashes unchanged (verify vs disk AND `git show HEAD:`): H004V106 canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` (`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`); H10 fresh IMMATURE `9bdee66f737e492b3302a730af29ab9f811611e5a908ccf6002d08eab3e8bc5a` (`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json`).
- Cutoff **BLOCKED** (latest real probe `research_state/cutoff_probe/cutoff_probe_20261105T205749Z.json`, Nov 2026 target_published=false, control 2026-09 alive). **Do NOT re-probe before 2026-11-30.** No confirmatory advance; k not advanced.

### Immediate next action (pick the highest-value unblocked item)
1. **Preserve blocker.** Re-verify frozen hashes vs disk AND `git show HEAD:` + `compileall -q scripts tests` + `scripts/audit_preregistration_coverage.py` before any new work.
2. **Do NOT re-probe November 2026 before 2026-11-30.** Continue only if a *new* unblocked audit/doc/hygiene task arises with explicit scope not covered by recent sessions (e.g., newly identified doc/contract drift, uncovered test gap, manifest/hash delta, prereg coverage edge case, or other bounded no-cost task with a concrete artifact/test output). Do not repeat completed baseline-only reverification without a clear delta.
3. **Candidate bounded hygiene examples (only if genuinely new scope):** cross-check handoff/task/contract claims against current file state and fix drift with a small doc patch + verification artifact; add/strengthen a targeted regression test for a stated invariant (run it; record command/outcome); audit a manifest/preregistration field for an uncovered edge case via `audit_preregistration_coverage.py` or a focused script. If nothing new/unblocked is found, record that finding with evidence in `research_state/session_verifications/` and update handoff/task.
4. **After 2026-11-30 only:** `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If published: refresh free public data as needed, install deps, run tests, verify H004V106 unchanged vs `git show HEAD:`, run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`) with `--forward-block-start 2026-09-30 --data-cutoff 2026-11-30 --output-dir ... --look-number 1` (k=1). Require ALL of `n_high>0 AND n_low>0`, `n_high>=5 AND n_low>=5`, `|high_low_diff_net_1x| >= 0.05`, and Holm significance across the complete 216-cell family at `alpha_k = 0.05/(k*(k+1))` before any confirmatory claim. If IMMATURE, record blocker and do not advance k.

### Hard rules
- Never relax 30-day maturity, `MIN_ASSETS_DECILES=20`, trailing-decile rule, or 0.05 threshold.
- Never open canonical sealed holdout (`forward_block/`); write fresh outputs only to `forward_block_h10_fresh/` or a new uniquely identified path.
- Never use today's rank as historical truth. Never fabricate metrics. Preserve old artifacts.
- **Never write "wait for a new experiment ID."** Allocate unique IDs/preregister if starting new exploratory work.
