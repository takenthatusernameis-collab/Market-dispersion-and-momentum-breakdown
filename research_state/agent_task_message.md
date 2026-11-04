## Initial task for next agent

Read prior handoff + task message + AGENTS.md + research_protocol.md + operating contract; verify current state per instructions.

Current status: BLOCKED on two fronts: (1) data maturity (November 2026 not published; cutoff gate BLOCKED; do NOT re-probe before 2026-11-30); (2) preregistration reconciliation requires explicit research decisions and is NOT completable by fabricating hypotheses/preregistrations/metrics.

Verified this pass (2026-11-04T12:05Z):
- Full suite: `python3 -m unittest discover -s tests` -> FAILED (failures=20, errors=6, skipped=1); 6 errors are ModuleNotFoundError (pandas/numpy) in this environment; durable-state preregistration mismatches remain (8 committed audits not in AUDIT_TO_HYPOTHESIS/addenda, 4 addenda carrying ids, H12 experiment_id != audit_id).
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged vs disk and `git show HEAD:`.
- Blocker preserved; no frozen experiment artifact changed; no fabrication performed.
- Probe guard: November monthly archive unavailable until after 2026-11-30; latest probe shows cutoff_gate=BLOCKED for November target; record field null; not evidence.
- Handoff and task message updated for continuity.

IMMEDIATE NEXT ACTION (unblocked, do NOT fabricate):
1. Preserve blocker. Do NOT attempt to green the suite by fabricating hypotheses, preregistrations, metrics, or by nulling audit ids without an explicit research decision.
2. Await research decision on preregistration reconciliation (register diagnostic audits as hypotheses with preregistrations, or declare addenda and null their ids). Record decision + rationale before changing durable state.
3. After 2026-11-30, re-probe November 2026 (`python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`). A printed UNBLOCKED line is only evidence when its `record` field is non-null AND that path exists on disk. If target_published=true AND record confirmed on disk: refresh free public data if needed, re-run tests, verify H004V106 unchanged vs `git show HEAD:`, run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`), require n_high>0 AND n_low>0 before any confirmatory claim, apply predeclared rules/costs/Holm across complete family. If still IMMATURE, record blocker.
4. Never relax 30-day maturity/MIN_ASSETS_DECILES=20/trailing-decile rule. Never open canonical sealed holdout. Never write "wait for a new experiment ID."
