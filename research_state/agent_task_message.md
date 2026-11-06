## Initial task for next agent

Read `research_state/agent_handoff.md` (current session 2026-11-06T18:03Z), this file, `AGENTS.md`, `docs/research_protocol.md`, and `prompts/continuous_research_operating_contract_v1.md`. Verify current state before acting.

### Verified state (2026-11-06T18:03Z, HEAD at verify start `99722969d0397b8c60174cb2ce702c183a9b3deb`)
- **Prior task:** COMPLETE. Independent unblocked verification: deps present (Python 3.12.3, numpy 2.5.4, pandas 3.1.1); `compileall -q scripts tests` clean (EXIT=0); `audit_preregistration_coverage.py` pass=True (14/0/0); `unittest discover -s tests` 255 OK, skipped=1 (52.704s). `git ls-files tests/__pycache__` = 0; `git status --short` clean at start; `git diff --name-only -- artifacts/ configs/` empty. Verification: `research_state/session_verifications/session_verify_20261106T180350Z.json`.
- **Canonical H004V106 (DO NOT TOUCH):** sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` (`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`).
- **H10 fresh block (IMMATURE, preserved):** sha256 `9bdee66f737e492b3302a730af29ab9f811611e5a908ccf6002d08eab3e8bc5a` (cutoff 2026-10-31, n_high=0, n_low=0, n_mid=1; `forward_block_h10_fresh/`).
- **Cutoff probes:** October 2026 UNBLOCKED (target_published=true). November 2026 BLOCKED (latest `research_state/cutoff_probe/cutoff_probe_20261105T205749Z.json`, target_published=false). **Do NOT re-probe November 2026 before 2026-11-30.**
- **Frontier:** `research_state/universe_frontier.json` sha256 `ebd4406ab53f2265903a58ad8eda1dc24bcd5a3fcbb026d78c3b170cd9e59bb6` (unchanged). Adaptive-gate trigger NOT met. No confirmatory advance; k not advanced.

### Immediate next action (unblocked, do not fabricate)
1. Preserve blocker. Do NOT fabricate.
2. **Do NOT re-probe November 2026 before 2026-11-30.** Continue independent unblocked audit/test/doc/hygiene tasks that do not touch frozen artifacts or fabricate evidence.
3. **After 2026-11-30 only:** run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If `target_published=true`: refresh free public data if needed; install deps (`python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt`); run tests; verify H004V106 unchanged vs `git show HEAD:`; run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`) with `--forward-block-start 2026-09-30 --data-cutoff 2026-11-30 --output-dir ... --look-number 1` (k=1). Require `n_high>0 AND n_low>0` before any confirmatory claim; apply predeclared rules/costs/Holm across complete 216-cell family AND sequential alpha-spending `alpha_k = 0.05/(k*(k+1))`. If IMMATURE, record blocker and do not advance k.
4. Never relax 30-day maturity, `MIN_ASSETS_DECILES=20`, or trailing-decile state rule. Never open canonical sealed holdout. Never use today's rank as historical point-in-time truth.
5. Re-run `compileall -q scripts tests`, `audit_preregistration_coverage.py`, and `unittest discover -s tests` (baseline 255 OK, skipped=1) and record `research_state/session_verifications/session_verify_<UTC>.json` before sign-off. Check `git ls-files tests/__pycache__` is 0; re-apply `git rm --cached` on tracked `tests/__pycache__/*.pyc` if hygiene fails. **Never write "wait for a new experiment ID."**
