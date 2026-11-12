# Agent Task Message — 2026-11-12T21:46:42Z (next session)

## Verified state (2026-11-12T21:46:42Z)
- **HEAD:** `441ac68c` (`main`). Working tree clean. All task-A changes committed.
- **Frozen hashes unchanged:** canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`; registry `693b13097ebaee14e16b18906e698478a5ccc2df7bac5c135af571a28195c6e5`; frontier `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e`.
- **Checks:** `python3 -m compileall -q scripts tests` EXIT=0; `python3 -m unittest discover -s tests` → `Ran 363 tests`, `OK (skipped=1)`, EXIT=0. Manifest claim `363/363/0`.
- **Prior task — complete:** Next action A (registry reference reconciliation) is done. H1–H23 registered, `next_sequence_number=23`; H23 = `HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001` (EXPLORATORY_ONLY) pointing at the F1COVERAGE-001 artifact; guard test `tests/test_experiment_registry_reference.py` added and passing (7 stdlib guards). Recorded in `research_state/session_verifications/session_verify_20261112T214642Z.json`.
- **November 2026 probe (verdict only, NOT H10 gate):** `cutoff_probe_20261107T091152Z.json` — `probe_month=2026-11`, `target_published=false`. **Do not re-probe before 2026-11-30.** H10 gate UNBLOCKED by October 2026 archive; fresh block IMMATURE (`n_formations=1`, `n_high=0`, `n_low=0`).
- **Frontier:** `ACTIVE_INCOMPLETE`, catalog exhausted (cursor 6347, verified 220, blocked 6127), `historical_rank_coverage_state=NOT_PROVEN_COMPLETE`, panel `2023-01-01..2026-10-31`.
- **H10:** CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / EVALUATED_NULL_DIFF_IMMATURE; k not advanced.

## Initial task for next agent

### On/after 2026-11-30 — H10 fresh sealed forward block (date-gated, bounded, no-cost)
Nothing bounded and unblocked remains before 2026-11-30. The next executable action is date-gated:

1. `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`
2. If `target_published=true`: refresh free public data only (Coin Metrics Community API + Binance Public Data Archive); run `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests`; verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged; run fresh sealed H10 block **only** into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--forward-block-start 2026-09-30 --data-cutoff <new cutoff> --look-number 1` (30-day maturity, `MIN_ASSETS_DECIMAL=20`, trailing-decile, 0.05 economic threshold, sequential `alpha_k = 0.05/(k*(k+1))` per H22/prereg sec 4.1).
3. Require `n_high > 0 AND n_low > 0` before any confirmatory claim. If still immature, record outcome and **do not advance k**. Preserve all frozen artifacts/configs unchanged.

Do **not** re-probe November 2026 before 2026-11-30. Do not alter frozen 003 artifacts/configs/inputs or the frontier.

## Hard constraints
Free public data only; historical research only (no orders/live/paper trading); preserve DISPERSION-001/002 and frozen 003 artifacts/configs/inputs; no look-ahead/fabrication/forward-fill; today's rank ≠ historical truth; complete multiple-testing correction for any claim; do not reuse inspected holdout as fresh confirmation.

## End-of-session requirement
Leave clean state; update durable handoff/task message with verified evidence; leave a concrete next action. Never write "wait for a new experiment ID." Waiting for the fixed calendar date 2026-11-30 is a date gate, not an experiment ID; the action above is concrete once the date arrives.

(End of file)
