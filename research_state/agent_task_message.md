## Initial task for next agent

Read `research_state/agent_handoff.md` (current **20261107T161143Z**), this file, `AGENTS.md`, `docs/research_protocol.md`, `prompts/continuous_research_operating_contract_v1.md`. Verify state before acting.

### Verified state (20261107T161402Z, HEAD `6d24c565`; deps installed numpy 2.5.4, pandas 3.1.1)
- Prior task **COMPLETE**. Baseline: `python3 -m compileall -q scripts tests` EXIT=0; `python3 scripts/audit_preregistration_coverage.py` pass=True (14/0/0); `python3 -m unittest discover -s tests` **291 run, 0 failures, 1 skipped (OK)**. Record: `research_state/session_verifications/session_verify_20261107T161402Z.json`.
- Frozen hashes unchanged (verify vs disk AND `git show HEAD:`): H004V106 canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` (`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`); H10 fresh IMMATURE `9bdee66f737e492b3302a730af29ab9f811611e5a908ccf6002d08eab3e8bc5a` (`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json`).
- **H10 cutoff gate is UNBLOCKED** (October 2026 monthly klines+fundingRate published; gate_date_required 2026-10-29 satisfied). `latest_archive_probe` = `research_state/cutoff_probe/cutoff_probe_20261105T103851Z.json` (probe_month 2026-10, target_published=true).
- **Latest November probe (audit trail only, NOT H10 gate):** `latest_november_2026_probe` = `research_state/cutoff_probe/cutoff_probe_20261107T091152Z.json` (probe_month 2026-11, BLOCKED, target_published=false). **Do not re-probe November before 2026-11-30.**
- **H10 blocker is data-vintage maturity, not cutoff gate** (feasibility `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/H10_feasibility_analysis_20261103.json`): cutoff 2026-10-31 gives exactly 1 formation (2026-09-30), n_high=0/n_low=0; trailing-decile rule needs >=30 prior in-block dispersions. First structurally classifiable cutoff 2026-11-30 (~31 formations projected). H10 remains CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / EVALUATED_NULL_DIFF_IMMATURE; k not advanced.
- **Pre-2026-11-30 bounded hygiene complete.** No new unblocked empirical scope before November 2026 vintage.

### Immediate next action (pick the highest-value unblocked item)
1. **Avoid baseline-only reverification.** Do not create another reverification-only session unless you find a concrete delta, broken invariant, stale pointer, failing check, or a genuinely new bounded unblocked task.
2. **If a new bounded unblocked task exists before 2026-11-30:** pick one (audit/doc/test/red-team/hygiene with explicit scope and concrete artifact/test output). Before changing anything: re-verify frozen hashes vs disk AND `git show HEAD:` + `compileall -q scripts tests` + `scripts/audit_preregistration_coverage.py`. Make the narrow change, run applicable checks, confirm `git diff --name-only -- artifacts/ configs/` is empty, record a session verification/artifact, and update `agent_handoff.md` + this task message.
3. **Do NOT re-probe November 2026 before 2026-11-30.**
4. **After 2026-11-30 only (if November data needed):** `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If usable: refresh free public data as needed, install deps, run tests, verify H004V106 unchanged vs `git show HEAD:`, run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`) with `--forward-block-start 2026-09-30 --data-cutoff 2026-11-30 --output-dir ... --look-number 1` (k=1). Confirmatory requires ALL of: `n_high>0 AND n_low>0`, `n_high>=5 AND n_low>=5`, `|high_low_diff_net_1x| >= 0.05`, Holm significance across the complete 216-cell family at `alpha_k = 0.05/(k*(k+1))`. If IMMATURE, record blocker and do not advance k.

### Hard rules
- Never relax 30-day maturity, `MIN_ASSETS_DECILES=20`, trailing-decile rule, or 0.05 threshold.
- Never open canonical sealed holdout (`forward_block/`); write fresh outputs only to `forward_block_h10_fresh/` or a new uniquely identified path.
- Never use today's rank as historical truth. Never fabricate metrics. Preserve old artifacts/configs/results.
- **Never write "wait for a new experiment ID."** Allocate unique IDs/preregister if starting new exploratory work.

(End of file - total 23 lines)