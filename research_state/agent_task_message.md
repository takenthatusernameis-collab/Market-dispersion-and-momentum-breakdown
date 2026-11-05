## Initial task for next agent

Read prior handoff + task message + AGENTS.md + research_protocol.md + operating contract; verify current state per instructions.

Current status: BLOCKED on data maturity (November 2026 not published; cutoff gate BLOCKED; do NOT re-probe before 2026-11-30). State verified 2026-11-05T06:19:22Z. Tests: 206 run, 7 failures, 6 errors, 1 skipped (missing deps numpy/pandas).

Verified this pass (2026-11-05T06:19:22Z):
- Branch HEAD cdf0fb7e; working tree clean of tracked source changes.
- Probe guard respected: no re-probe before 2026-11-30. Latest probe on disk: `research_state/cutoff_probe/cutoff_probe_20261104T151423Z.json` (probe_month=2026-11, target_published=false, cutoff_gate=BLOCKED, archive_alive=true, control_month=2026-09 ok). Trust only real probe records under `research_state/cutoff_probe/`.
- No frozen experiment artifact changed. Canonical H004V106 forward block sha256 7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390 unchanged vs `git show HEAD:`.

State summary:
- H22 (HARMONY-CRYPTO-EDGE-004-DISPERSION-003-H10-SEQUENTIAL-ALPHA, EXPLORATORY_ONLY) preregistered with sequential alpha-spending rule in `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H10_FRESH_FORWARD_BLOCK_v1.md` section 4.1 (pre-outcome). Registry next_sequence_number=22.
- H10 still EVALUATED_NULL_DIFF_IMMATURE (n_formations=1, n_high=0, n_low=0).
- Adaptive-gate trigger NOT met; exploratory track not started.

IMMEDIATE NEXT ACTION (unblocked, do NOT fabricate):
1. Preserve blocker. Do NOT fabricate hypotheses/preregistrations/metrics or null audit ids.
2. Do NOT re-probe before 2026-11-30. After 2026-11-30, re-probe November 2026 (`python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`). If target_published=true: refresh free public data if needed, re-run tests (`python3 -m unittest discover -s tests`), verify H004V106 unchanged vs `git show HEAD:` (sha256 7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390), run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`), require n_high>0 AND n_low>0 before any confirmatory claim, apply predeclared rules/costs/Holm across complete 216-cell family AND sequential alpha-spending at current k (alpha_k = 0.05/(k*(k+1)), per H22/4.1) — never fixed 0.05. If still IMMATURE, record blocker and do not advance k.
3. Never relax 30-day maturity/MIN_ASSETS_DECILES=20/trailing-decile rule. Never open canonical sealed holdout. Never write "wait for a new experiment ID."
