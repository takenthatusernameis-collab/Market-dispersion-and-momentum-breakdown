## Initial task for next agent

Read prior handoff + task message + AGENTS.md + research_protocol.md + operating contract; verify current state per instructions.

Current status: BLOCKED on data maturity (November 2026 not published; cutoff gate BLOCKED; do NOT re-probe before 2026-11-30). State re-verified 2026-11-05T02:04:18Z. Test suite green (229 run, 1 skipped, 0 failures).

Verified this pass (2026-11-05T02:04:18Z):
- Branch HEAD cb5d61165dd7a484f9ae2b6eb975d99b6993bc76; tests: `python3 -m unittest discover -s tests` -> Ran 229 tests, OK (skipped=1), EXIT=0.
- Probe guard respected: no re-probe before 2026-11-30. Latest probe on disk: `research_state/cutoff_probe/cutoff_probe_20261104T151423Z.json` (target_published=false, cutoff_gate=BLOCKED). Trust only real probe records under `research_state/cutoff_probe/`.
- No frozen experiment artifact changed; no fabrication performed. Canonical H004V106 forward block sha256 7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390 unchanged vs prior record. Only untracked `__pycache__` bytecode caches differ.

State summary:
- H22 (HARMONY-CRYPTO-EDGE-004-DISPERSION-003-H10-SEQUENTIAL-ALPHA, EXPLORATORY_ONLY) preregistered with sequential alpha-spending rule in `preregistrations/H10_FRESH_FORWARD_BLOCK_v1.md` section 4.1 (pre-outcome). Registry next_sequence_number=22.
- H10 still EVALUATED_NULL_DIFF_IMMATURE (n_formations=1, n_high=0, n_low=0). H1 immutable NOT_SUPPORTED_AS_ROBUST_EDGE.

IMMEDIATE NEXT ACTION (unblocked, do NOT fabricate):
1. Preserve blocker. Do NOT attempt to green the suite by fabricating hypotheses, preregistrations, metrics, or by nulling audit ids without an explicit research decision.
2. After 2026-11-30, re-probe November 2026 (`python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`). If target_published=true: refresh free public data if needed, re-run tests, verify H004V106 unchanged vs `git show HEAD:` (sha256 7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390), run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`), require n_high>0 AND n_low>0 before any confirmatory claim, apply predeclared rules/costs/Holm across the complete 216-cell family AND the sequential alpha-spending rule at the current look number k (alpha_k = 0.05/(k*(k+1)), per H22/section 4.1) — never a fixed 0.05. If still IMMATURE, record blocker and do not advance k.
3. Never relax 30-day maturity/MIN_ASSETS_DECILES=20/trailing-decile rule. Never open canonical sealed holdout. Never write "wait for a new experiment ID."

(End of file - total 19 lines)
