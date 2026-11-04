## Initial task for next agent

Read prior handoff + task message + AGENTS.md + research_protocol.md + operating contract; verify current state per instructions.

Current status: UNBLOCKED cutoff (probe UNBLOCKED) but fresh H10 sealed block still IMMATURE (n_formations=1, n_high=0, n_low=0; data cutoff 2026-10-31, last formation 2026-09-30). Tests green (218 run, OK skipped=1). Canonical H004V106 sha256 7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390 unchanged. Fresh block written to forward_block_h10_fresh/.

Next action: When newer panel data is available (post-2026-11-30), refresh free public data (`python3 scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>`), re-run `python3 -m unittest discover -s tests`, verify H004V106 unchanged vs `git show HEAD:`, then re-run `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new panel date> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/`. Require n_high>0 AND n_low>0 before any confirmatory claim; apply predeclared rules/costs/Holm across complete family. If still IMMATURE, record blocker. Never relax 30-day maturity/MIN_ASSETS_DECILES=20/trailing-decile rule. Never open canonical sealed holdout. Never write "wait for a new experiment ID."
