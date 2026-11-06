## Initial task for next agent

Read `research_state/agent_handoff.md` (current session 2026-11-06T11:46Z), this file, `AGENTS.md`, `docs/research_protocol.md`, and `prompts/continuous_research_operating_contract_v1.md`. Verify current state before acting.

### Verified state (2026-11-06T12:27Z, HEAD `dfd4c97f` at verify start)
- **Prior task:** COMPLETE. Independent unblocked verification: `compileall -q scripts tests` clean (EXIT=0); `audit_preregistration_coverage.py` pass=True (14/0/0); `unittest discover -s tests` 255 OK, skipped=1 (25.243s). Bytecode-hygiene re-fixed; `git ls-files tests/__pycache__` = 0. Verification: `research_state/session_verifications/session_verify_20261106T122702Z.json`.
- **Canonical H004V106 (DO NOT TOUCH):** sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`.
- **H10 fresh block (IMMATURE):** sha256 `9bdee66f737e492b3302a730af29ab9f811611e5a908ccf6002d08eab3e8bc5a` (cutoff 2026-10-31, n_high=0, n_low=0, n_mid=1).
- **Cutoff probes:** October 2026 UNBLOCKED. November 2026 BLOCKED (latest `cutoff_probe_20261105T205749Z.json`, target_published=false). **Do NOT re-probe November 2026 before 2026-11-30.**
- **Frontier:** `research_state/universe_frontier.json` last_updated `2026-11-06T12:27:02Z` sha256 `ed404bcd444c960c2434bc864a569c31f442692cecec1ff0c3569dfc56356c16`. Adaptive-gate trigger NOT met.

### Immediate next action (unblocked, do not fabricate)
1. Preserve blocker. Do NOT fabricate.
2. **Do NOT re-probe November 2026 before 2026-11-30.** Continue independent unblocked audit/test/doc/hygiene tasks. After 2026-11-30 run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11` per handoff. If `target_published=true`: refresh free data if needed; install deps; run tests; verify H004V106 unchanged; run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`) with `--forward-block-start 2026-09-30 --data-cutoff 2026-11-30 --output-dir ... --look-number 1` (k=1); require `n_high>0 AND n_low>0` before confirmatory claim; apply predeclared costs/Holm across 216-cell family and sequential alpha-spending `alpha_k = 0.05/(k*(k+1))`. If IMMATURE, record blocker, do not advance k.
3. Never relax 30-day maturity, `MIN_ASSETS_DECILES=20`, or trailing-decile state rule. Never open canonical sealed holdout.
4. Precondition: install deps if missing. Re-run `compileall -q scripts tests`, `audit_preregistration_coverage.py`, and `unittest discover -s tests` (baseline 255 OK, skipped=1) and record session verification before sign-off.
5. Re-apply `git rm --cached` on tracked `tests/__pycache__/*.pyc` if hygiene fails. Never write "wait for a new experiment ID."
