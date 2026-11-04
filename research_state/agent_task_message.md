## Initial task for next agent

Read prior handoff + task message + AGENTS.md + research_protocol.md + operating contract; verify current state per instructions.

Current status: BLOCKED on data maturity (November 2026 not published; cutoff gate BLOCKED; do NOT re-probe before 2026-11-30). Preregistration reconciliation RESOLVED (2026-11-04T14:06Z). Durable-state drift repaired 2026-11-04T16:41Z. State re-verified 2026-11-04T18:42Z. Test suite now green (223 run, 1 skipped, 0 failures) after installing numpy/pandas from requirements.txt.

Verified this pass (2026-11-04T18:42Z):
- Dependencies installed from requirements.txt (numpy 2.5.4, pandas 3.1.1, python-dateutil, tzdata).
- Full suite: `python3 -m unittest discover -s tests` -> OK (223 run, 1 skipped, 0 failures). Printed UNBLOCKED lines with `record: null` during the run are not evidence per instructions.
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged vs disk and `git show HEAD:`.
- Probe guard respected: no re-probe before 2026-11-30. November monthly archive unavailable until after 2026-11-30. Last probe on disk: `research_state/cutoff_probe/cutoff_probe_20261104T151423Z.json` (probe_month=2026-11, target_published=false, all six target endpoints HTTP 404, control month 2026-09 alive HTTP 200, cutoff_gate=BLOCKED).
- Printed UNBLOCKED lines with `record: null` are not evidence.
- No frozen experiment artifact changed; no fabrication performed. Only `__pycache__` bytecode caches differ (untracked, not source).

Probe guard: November monthly archive unavailable until after 2026-11-30; a printed UNBLOCKED line with `record: null` is not evidence of an unblocked state.

IMMEDIATE NEXT ACTION (unblocked, do NOT fabricate):
1. Preserve blocker. Do NOT attempt to green the suite by fabricating hypotheses, preregistrations, metrics, or by nulling audit ids without an explicit research decision.
2. After 2026-11-30, re-probe November 2026 (`python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`). A printed UNBLOCKED line is only evidence when its `record` field is non-null AND that path exists on disk. If target_published=true AND record confirmed on disk: refresh free public data if needed, re-run tests, verify H004V106 unchanged vs `git show HEAD:`, run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`), require n_high>0 AND n_low>0 before any confirmatory claim, apply predeclared rules/costs/Holm across complete family. If still IMMATURE, record blocker.
3. Never relax 30-day maturity/MIN_ASSETS_DECILES=20/trailing-decile rule. Never open canonical sealed holdout. Never write "wait for a new experiment ID."
