## Initial task for next agent

Read prior handoff + task message + AGENTS.md + research_protocol.md + operating contract; verify current state per instructions.

Current status: BLOCKED by data maturity (November 2026 not published; cutoff gate BLOCKED). Today is 2026-11-04, before the 2026-11-30 month-end; November 2026 monthly archive not yet published and cannot unblock H10. This is an immutable date gate; do NOT re-probe before 2026-11-30 (same-day repeat of known failure prohibited).

Verified this session (2026-11-04T09:45Z):
- Full suite: `python3 -m unittest discover -s tests` -> **220 run, OK (skipped=1), EXIT=0**.
- Latest genuine on-disk November 2026 probe: `research_state/cutoff_probe/cutoff_probe_20261104T083218Z.json`, target_published=false, cutoff_gate=BLOCKED, archive_alive=true (Sept 2026 control HTTP 200; November monthly klines/fundingRate both HTTP 404 = genuine month-not-over).
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged vs disk and `git show HEAD:`. Git clean apart from `__pycache__` bytecode churn.
- Cutoff-probe integrity hardening in place: a mocked run prints `"record": null`; tests enforce record path exists on disk and gate consistency (`scripts/probe_cutoff_gate.py` + `tests/test_cutoff_probe.py`).
- DISPERSION-003 grid complete (216/216 OK), H004V106/H004V105 preregistered/validated; fresh H10 block in `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` remains IMMATURE (n_formations=1, n_high=0, n_low=0, overlap_aware_uncertainty IMMATURE). Canonical `forward_block/` unchanged.

Frontier/registry: unchanged; cursor 6347, catalog exhausted; H1 NOT_SUPPORTED_AS_ROBUST_EDGE; H2-H7/H9/H10 CANDIDATE_UNVALIDATED; H8/H11/H12 EXPLORATORY_ONLY; H10 EVALUATED_NULL_DIFF_IMMATURE. Adaptive-gate trigger NOT met.

Next action: Re-probe November 2026 (`python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`) after 2026-11-30. A printed UNBLOCKED line is only evidence when its `record` field is non-null AND that path exists on disk (guard enforced). If target_published=true AND record confirmed on disk: refresh free public data if needed (`python3 scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>`), re-run `python3 -m unittest discover -s tests`, verify H004V106 unchanged vs `git show HEAD:`, run fresh sealed block into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`) via `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new cutoff> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/`, require n_high>0 AND n_low>0 before any confirmatory claim, apply predeclared rules/costs/Holm across complete family. If still IMMATURE, record blocker. Never relax 30-day maturity/MIN_ASSETS_DECILES=20/trailing-decile rule. Never open canonical sealed holdout. Never write "wait for a new experiment ID."

If probe remains BLOCKED after month-end and no alternative unblocked work emerges, preserve blocker and leave concrete next action per AGENTS.md.
