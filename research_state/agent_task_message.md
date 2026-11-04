## Initial task for next agent

Read prior handoff + task message + AGENTS.md + research_protocol.md + operating contract; verify current state per instructions.

Current status: BLOCKED on data maturity (November 2026 not published; cutoff gate BLOCKED; do NOT re-probe before 2026-11-30). Preregistration reconciliation RESOLVED (2026-11-04T14:06Z): 8 diagnostic audits registered as H14-H21; 4 addenda declared by nulling ids; H12 experiment_id corrected. No fabrication performed.

Verified this pass (2026-11-04T16:14Z):
- Full suite: `python3 -m unittest discover -s tests` -> OK (223 run, 1 skipped, 0 failures).
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged vs disk and `git show HEAD:`.
- Probe guard respected: no re-probe before 2026-11-30. November monthly archive unavailable until after 2026-11-30. Last probe on disk: `research_state/cutoff_probe/cutoff_probe_20261104T151423Z.json` (target_published=false, all six target endpoints HTTP 404, control month 2026-09 alive HTTP 200).
- No frozen experiment artifact changed; no fabrication performed.

Probe guard: November monthly archive unavailable until after 2026-11-30; a printed UNBLOCKED line with `record: null` is not evidence of an unblocked state.

IMMEDIATE NEXT ACTION (unblocked, do NOT fabricate):
1. Preserve blocker. Do NOT attempt to green the suite by fabricating hypotheses, preregistrations, metrics, or by nulling audit ids without an explicit research decision.
2. After 2026-11-30, re-probe November 2026 (`python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`). A printed UNBLOCKED line is only evidence when its `record` field is non-null AND that path exists on disk. If target_published=true AND record confirmed on disk: refresh free public data if needed, re-run tests, verify H004V106 unchanged vs `git show HEAD:`, run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`), require n_high>0 AND n_low>0 before any confirmatory claim, apply predeclared rules/costs/Holm across complete family. If still IMMATURE, record blocker.
3. Never relax 30-day maturity/MIN_ASSETS_DECILES=20/trailing-decile rule. Never open canonical sealed holdout. Never write "wait for a new experiment ID."
" filePath">
research_state/agent_task_message.md