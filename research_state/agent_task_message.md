## Initial task for next agent

Read `research_state/agent_handoff.md`, this file, `AGENTS.md`, `docs/research_protocol.md`, and `prompts/continuous_research_operating_contract_v1.md`. Verify current state before acting.

### Verified state (2026-11-05T22:06Z, HEAD `90764cd6328b210931e54965d9ec37140a48660c`)
- **Prior task:** COMPLETE. Session verification `research_state/session_verifications/session_verify_20261105T220645Z.json`: pip install requirements satisfied; compileall clean; unittest discover 241 tests OK skipped=1; preregistration coverage audit pass=True (14/0/0); all canonical/frozen hashes unchanged; no frozen experiment artifacts modified.
- **Canonical H004V106 (DO NOT TOUCH):** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json` sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`.
- **H10 fresh block (IMMATURE):** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json` sha256 `9bdee66f737e492b3302a730af29ab9f811611e5a908ccf6002d08eab3e8bc5a` (cutoff 2026-10-31, n_high=0, n_low=0, n_mid=1, high_low_diff_net_1x=null). H10 `CANDIDATE_UNVALIDATED`/`EVALUATED_NULL_DIFF_IMMATURE`. H22 `EXPLORATORY_ONLY`. Registry next=22 (H1..H22).
- **Cutoff probes:** October 2026 UNBLOCKED (`research_state/cutoff_probe/cutoff_probe_20261105T103851Z.json`); November 2026 BLOCKED (latest: `research_state/cutoff_probe/cutoff_probe_20261105T205749Z.json`). **Do NOT re-probe November 2026 before 2026-11-30.**
- **Frontier/registry:** `research_state/universe_frontier.json` sha256 `13fe75a27f1eccca0850afef133691ce0af72458108f2ead68fdc4381bc4c563` ACTIVE_INCOMPLETE. `research_state/hypothesis_registry.json` sha256 `497e0b5157671400206c6ae358dd4db214a69e753c555093753605e6c360f599`. Adaptive-gate trigger NOT met.

### Immediate next action (unblocked, do not fabricate)
1. Preserve blocker. Do NOT fabricate hypotheses, preregistrations, metrics, probe records, or audit IDs.
2. **Do NOT re-probe November 2026 before 2026-11-30.** Continue with independent unblocked audit/test/doc tasks that do not touch frozen artifacts or fabricate evidence (e.g., re-run `python3 scripts/audit_preregistration_coverage.py`, frontier/registry consistency checks, red-team diagnostics, script hygiene). After 2026-11-30, run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`:
   - If `target_published=true`: refresh free public data if needed; run tests; verify H004V106 unchanged; run fresh sealed block into `.../forward_block_h10_fresh/` (never `forward_block/`) with `--forward-block-start 2026-09-30 --data-cutoff 2026-11-30 --output-dir ... --look-number 1` (keep k=1); require `n_high>0 AND n_low>0` before any confirmatory claim; apply predeclared rules/costs/Holm across complete 216-cell family AND sequential alpha-spending at current k (`alpha_k = 0.05/(k*(k+1))`). If still IMMATURE, record blocker and do not advance k.
   - If still blocked, preserve blocker, update handoff/task message with new probe record, continue with independent unblocked audit/test/doc tasks.
3. Never relax 30-day maturity, `MIN_ASSETS_DECILES=20`, or trailing-decile state rule. Never open canonical sealed holdout. Never write "wait for a new experiment ID."
4. Precondition: `python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt` before running the suite.
5. Measurable progress this session: re-run `python3 -m compileall -q scripts tests` and `python3 -m unittest discover -s tests` (baseline: 241 OK, skipped=1) and record a new `research_state/session_verifications/session_verify_<UTC>.json` before signing off.
