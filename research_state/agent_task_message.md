## Initial task for next agent

Read `research_state/agent_handoff.md`, this file, `AGENTS.md`, `docs/research_protocol.md`, and `prompts/continuous_research_operating_contract_v1.md`. Verify current state before acting.

### Verified state (2026-11-05T09:46:59Z)
- **HEAD:** f42bc2b3 (`chore(kilo): checkpoint agent session`). Tracked source unchanged vs HEAD except generated `__pycache__` files. No frozen experiment artifacts modified.
- **Canonical H004V106:** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json` sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged (verify vs `git show HEAD:` before any fresh-block work).
- **Cutoff probe:** BLOCKED. Latest real probe: `research_state/cutoff_probe/cutoff_probe_20261104T151423Z.json` (probe_month=2026-11, `target_published=false`, `cutoff_gate=BLOCKED`, `archive_alive=true`, control 2026-09 ok). **Do NOT re-probe before 2026-11-30.** Trust only real probe records under `research_state/cutoff_probe/`.
- **H10:** `EVALUATED_NULL_DIFF_IMMATURE` (`n_formations=1, n_high=0, n_low=0`). H22 (`HARMONY-CRYPTO-EDGE-004-DISPERSION-003-H10-SEQUENTIAL-ALPHA`, `EXPLORATORY_ONLY`) preregisters sequential alpha-spending in `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H10_FRESH_FORWARD_BLOCK_v1.md` §4.1 (pre-outcome). Registry `next_sequence_number=22`.
- **Frontier:** cursor 6347, `candidates_discovered=[]`, `expanding_universe_target_met=true` (catalog exhausted). Adaptive-gate trigger NOT met.
- **Checks (2026-11-05):** `python3 scripts/audit_preregistration_coverage.py` -> pass=True, audits=14, missing_prereq=0, uncovered_prereq=0. `python3 -m unittest discover -s tests` -> 236 run, OK (skipped=1), 0 failures.

### Immediate next action (unblocked, do not fabricate)
1. Preserve blocker. Do NOT fabricate hypotheses, preregistrations, metrics, probe records, or audit IDs.
2. **Do NOT re-probe before 2026-11-30.** After 2026-11-30, run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`.
   - If `target_published=true`: refresh free public data if needed; run `python3 -m unittest discover -s tests`; verify H004V106 unchanged vs `git show HEAD:` (sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`); run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (**never** `forward_block/`); require `n_high>0 AND n_low>0` before any confirmatory claim; apply predeclared rules/costs/Holm across the complete 216-cell family **and** sequential alpha-spending at current k (`alpha_k = 0.05/(k*(k+1))`, per H22/§4.1) — never fixed 0.05. If still IMMATURE, record the blocker and do not advance k.
   - If still blocked, preserve the blocker, update handoff/task message with the new probe record, and continue with any independent unblocked audit/test/doc task that does not touch frozen artifacts or fabricate evidence.
3. Never relax 30-day maturity, `MIN_ASSETS_DECILES=20`, or the trailing-decile state rule. Never open the canonical sealed holdout. Never write "wait for a new experiment ID."
4. Precondition: `python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt` before running the suite.
"