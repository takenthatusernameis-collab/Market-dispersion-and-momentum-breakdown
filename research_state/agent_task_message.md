## Initial task for next agent

Read prior handoff + task message + AGENTS.md + research_protocol.md + operating contract; verify current state per instructions.

Current status: BLOCKED by data maturity (November 2026 not published; cutoff gate BLOCKED). Today is 2026-11-04, before the 2026-11-30 month-end; November 2026 monthly archive not yet published and cannot unblock H10. This is an immutable date gate; do NOT re-probe before 2026-11-30 (same-day repeat of known failure prohibited; last genuine probe 2026-11-04T08:32:18Z, target_published=false, cutoff_gate=BLOCKED).

Verified this session (2026-11-04T11:21Z):
- Full suite initially 223 run, 16 failures, 1 error (regressions from HEAD commit b17d5302). Fixed clear test-file regressions:
  * tests/test_state_consistency.py: INTEGRITY_AUDITS filename typos `2028.json`/`2025.json` -> `20261028.json`/`20261025.json`; assertion count 11 -> 12.
  * tests/test_continuous_research_contract.py: next_sequence_number 12 -> 13 (registry now H1..H13).
  * research_state/run_manifest.json: narrative next_sequence_number 12 -> 13 + H13 clause; fixed line indent.
  * artifacts/.../integrity_audit/H004V106_forward_block_placebo_red_team_20261028.json: added additive `conclusion` field mirroring existing `label` (no finding changed).
- After fixes: `python3 -m unittest discover -s tests` -> 223 run, **13 failures, 0 errors, skipped=1, EXIT=1**. All 13 remaining failures are in tests/test_preregistration_completeness.py (gate added in HEAD) and are durable-state mismatches requiring RESEARCH DECISIONS, not test-file typos; left unfixed to avoid fabricating hypotheses:
  * 12 x test_every_committed_audit_is_registered_or_excluded: diagnostic audits regime/rolling/cluster/tail/temporal/state_rep/overlap_aware not registered-or-addenda; addenda files hac_addendum/recomputation x2/integrity_audit carry non-null ids; final_integrity audit_id `H004V106_FORWARD_BLOCK_FINAL_INTEGRITY_AUDIT_20261102` != AUDIT_TO_HYPOTHESIS key `HARMONY-CRYPTO-EDGE-004-DISPERSION-003-FINAL-INTEGRITY-AUDIT`.
  * 1 x test_registered_hypothesis_names_its_experiment_id (hyp='H12'): H12 experiment_id `HARMONY-CRYPTO-EDGE-004-DISPERSION-003-H10-FEASIBILITY` != audit artifact_id `DISP-003-H10-FEASIBILITY-001`.
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged vs disk and `git show HEAD:`. Fresh H10 block unchanged: n_formations=1, n_high=0, n_low=0, overlap_aware_uncertainty IMMATURE. Canonical `forward_block/` unchanged. Git status clean apart from intended changes and `__pycache__`.
- Cutoff gate BLOCKED. Adaptive-gate trigger NOT met.

Frontier/registry: unchanged; cursor 6347, catalog exhausted; H1 NOT_SUPPORTED_AS_ROBUST_EDGE; H2-H7/H9/H10 CANDIDATE_UNVALIDATED; H8/H11/H12 EXPLORATORY_ONLY; H10 EVALUATED_NULL_DIFF_IMMATURE; H13 EXPLORATORY_ONLY (placebo, PLACEBO_SENSITIVE).

IMMEDIATE NEXT ACTION (unblocked, do this first):
1. Reconcile tests/test_preregistration_completeness.py with committed state so the suite goes green:
   - Register outstanding diagnostic audits (regime conditioning, rolling window, cluster bootstrap, tail influence, temporal stability, state representativeness, overlap aware) as hypotheses with preregistrations, OR declare them addenda; reconcile H11/H12/hac_addendum/recomputation x2/integrity_audit audit_id vs experiment_id mismatches; reconcile H12 experiment_id vs audit artifact_id.
   - Do NOT fabricate hypotheses, preregistrations, or metrics. Do not modify frozen experiment artifacts or decision rules.
   - Re-run `python3 -m unittest discover -s tests` and confirm green (target: 0 failures, 0 errors).
2. Record exact commands/outcomes; inspect the diff; confirm old experiment artifacts (canonical forward_block/, forward_block_h10_fresh/, DISPERSION-001/002, defective archive) unchanged.
3. Update frontier, registry, manifest and handoff as appropriate.

THEN (only after suite is green AND after 2026-11-30):
- Re-probe November 2026 (`python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`). A printed UNBLOCKED line is only evidence when its `record` field is non-null AND that path exists on disk (guard enforced).
- If target_published=true AND record confirmed on disk: refresh free public data if needed (`python3 scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>`), re-run `python3 -m unittest discover -s tests`, verify H004V106 unchanged vs `git show HEAD:`, run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`) via `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new cutoff> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/`, require n_high>0 AND n_low>0 before any confirmatory claim, apply predeclared rules/costs/Holm across complete family. If still IMMATURE, record blocker.
- Never relax 30-day maturity/MIN_ASSETS_DECILES=20/trailing-decile rule. Never open canonical sealed holdout. Never write "wait for a new experiment ID."

If the preregistration reconciliation remains infeasible and probe remains BLOCKED after month-end, preserve the blocker and leave a concrete next action per AGENTS.md.
