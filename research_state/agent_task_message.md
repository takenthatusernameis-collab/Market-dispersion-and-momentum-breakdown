## Initial task for next agent

Read prior handoff + task message + AGENTS.md + research_protocol.md + operating contract; verify current state per instructions.

Current status: BLOCKED by data maturity (November 2026 not published; cutoff gate BLOCKED). Today is 2026-11-04, before the 2026-11-30 month-end, so the November 2026 monthly archive is not yet published and cannot unblock H10. This is an immutable date gate; do not re-probe before 2026-11-30 (same-day repeat of a known failure prohibited; month not over).

Verified this session (2026-11-04T08:25Z):
- Full suite: `python3 -m unittest discover -s tests` -> **218 run, OK (skipped=1), EXIT=0**.
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged vs disk and `git show HEAD:`. Git clean apart from `__pycache__` bytecode churn.
- Latest genuine on-disk November 2026 probe: `research_state/cutoff_probe/cutoff_probe_20261104T063517Z.json` -> probe_month=2026-11, target_published=false, cutoff_gate=BLOCKED, archive_alive=true (Sept 2026 control HTTP 200; November monthly klines/fundingRate HTTP 404 = genuine month-not-over).
- Spurious probe stdout has claimed `cutoff_gate=UNBLOCKED` / `target_published=true` with named record paths that do NOT exist on disk (e.g. `cutoff_probe_20261104T082607Z.json` verified missing). Treat all UNBLOCKED stdout as unverified until the printed `record` path exists on disk.
- DISPERSION-003 grid complete: ledger 216/216 cells OK, 0 blocked, 0 failed, 0 Holm rejected; H004V106 OK (p=0.15, holm=False), H004V105 OK (p=0.032, holm=False). Integrity audit artifact and preregistrations exist under artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/. No alternative unblocked empirical work remains.
- Fresh H10 block in `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` remains IMMATURE (n_formations=1, n_high=0, n_low=0, data_cutoff 2026-10-31, overlap_aware_uncertainty IMMATURE). Canonical `forward_block/` unchanged.

Frontier/registry: unchanged; cursor 6347, catalog exhausted; H1 NOT_SUPPORTED_AS_ROBUST_EDGE (immutable); H2-H7/H9/H10 CANDIDATE_UNVALIDATED; H8 EXPLORATORY_ONLY; H10 EVALUATED_NULL_DIFF_IMMATURE; H11 EXPLORATORY_ONLY; H12 EXPLORATORY_ONLY. Adaptive-gate trigger NOT met (single timing route); exploratory track NOT started.

Next action: Re-probe November 2026 (`python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`) after 2026-11-30. After running, confirm the printed `record` path exists on disk before acting. If target_published=true AND record confirmed on disk: refresh free public data if needed (`python3 scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>`), re-run `python3 -m unittest discover -s tests`, verify H004V106 unchanged vs `git show HEAD:`, run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`) via `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new cutoff> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/`, require n_high>0 AND n_low>0 before any confirmatory claim, apply predeclared rules/costs/Holm across complete family. If still IMMATURE, record blocker. Never relax 30-day maturity/MIN_ASSETS_DECILES=20/trailing-decile rule. Never open canonical sealed holdout. Never write "wait for a new experiment ID."

If the probe remains BLOCKED after month-end and no alternative unblocked work emerges, preserve the blocker and leave a concrete next action per AGENTS.md.

(End of file)
