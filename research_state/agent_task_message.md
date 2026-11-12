# Agent Task Message — 2026-11-12T18:39:53Z (next session)

## Verified state (2026-11-12T18:39:53Z)
- **HEAD:** `26b849f2f5d66ff3d244407be0b0cad8ee22dc9e` (`main`). In-session changes are the F1COVERAGE-001 fix/additions only.
- **Frozen hashes unchanged:** canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`; registry `7faacdb3f7add98a9e6bddf3c4ab3403fd812711dd0ca601b5ddda031a664df4`; frontier `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e`; latest probe `25c11cbae9e62c9f5feb41d9f2de09a996dd4a0a1ddcfa4828ecc05daa73f7e6`.
- **Checks this session:** `python3 -m compileall -q scripts tests` EXIT=0; after adding a test, `python3 scripts/record_test_claim.py` refreshed the snapshot (106 files); final `python3 -m unittest discover -s tests` → `Ran 356 tests in 59.824s`, `OK (skipped=1)`, EXIT=0. Manifest claim `356/356/0`.
- **November 2026 probe (verdict only, NOT H10 gate):** `cutoff_probe_20261111T013459Z.json` — `probe_month=2026-11`, `target_published=false`. **Do not re-probe before 2026-11-30.**
- **H10 cutoff gate:** UNBLOCKED by October 2026 archive (probe 2026-11-05T10:38:51Z, `probe_month=2026-10`, `target_published=true`).
- **Frontier:** `ACTIVE_INCOMPLETE`, catalog exhausted (cursor 6347, verified 220, blocked 6127), `historical_rank_coverage_state=NOT_PROVEN_COMPLETE`, panel `2023-01-01..2026-10-31`.
- **H10:** CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / EVALUATED_NULL_DIFF_IMMATURE (`n_formations=1`, `n_high=0`, `n_low=0`, `high_low_diff_net_1x=null`); k not advanced.
- **F1COVERAGE-001 (exploratory arm):** repair verdict PASS; canonical-block eligible-asset count rises 26-27 → 29-31 (638 dates increased, 0 decreased). This arm is NOT part of the sealed 003 inputs and cannot promote any hypothesis.

## Prior task — complete
Read prior durable handoff/task (2026-11-12T18:26:10Z). Found and fixed a reproducible bounded gap in the F1COVERAGE-001 arm: (G1) doubled `experiment_id` prefix in `scripts/f1_panel_coverage_repair.py`; (G2) missing prereg-promised regression guard `tests/test_f1_panel_coverage_repair.py`. Added the test (8 guards), re-ran the repair offline (idempotent, PASS, corrected audit emitted), refreshed the verified test claim, and left all frozen artifacts/registry/frontier byte-unchanged.

## Initial task for next agent

### A) Before 2026-11-30 — registry reference reconciliation (bounded, no-cost)
The F1COVERAGE-001 preregistration names hypothesis **H23**, but `research_state/hypothesis_registry.json` still has H1–H22 and `next_sequence_number=22`.
1. Decide: (i) register H23 as a `SOURCE_COVERAGE_REPAIR` / `EXPLORATORY_ONLY` entry pointing at the F1COVERAGE-001 artifacts and bump `next_sequence_number` to 23, or (ii) amend the preregistration so it does not claim an unallocated hypothesis.
2. Add a stdlib guard test that every experiment id referenced under `artifacts/` resolves to a registered hypothesis (durable-state consistency, not a market test).
3. Do **not** re-probe November 2026 before 2026-11-30. Do not alter frozen 003 artifacts/configs/inputs or the frontier. Record a new `research_state/session_verifications/*.json` and update the handoff/task message.

### B) On/after 2026-11-30 (date-gated, executable)
1. `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`
2. If `target_published=true`: refresh free public data only (Coin Metrics Community API + Binance Public Data Archive); run `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests`; verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged; run fresh sealed H10 block **only** into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--look-number 1` (30-day maturity, `MIN_ASSETS_DECIMAL=20`, trailing-decile, 0.05 economic threshold, sequential `alpha_k = 0.05/(k*(k+1))`).
3. Require `n_high > 0 AND n_low > 0` before any confirmatory claim. If still immature, record outcome and **do not advance k**. Preserve all frozen artifacts/configs unchanged. Expect ~26 eligible assets on the sealed 003 inputs unless the F1COVERAGE-001 repaired panels are promoted via a separate new-ID confirmatory route.

### C) F1COVERAGE-001 → confirmatory route (new ID required, not now)
Promoting the repaired 29-31-asset coverage to a confirmatory estimate requires a NEW hypothesis/experiment ID, preregistration, and new artifact paths built from `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001/data/panels/`. Never overwrite the sealed 003 panels/raw/artifacts. Label EXPLORATORY_ONLY unless the full confirmatory gates are re-run on admissible data.

## Hard constraints
Free public data only; historical research only (no orders/live/paper trading); preserve DISPERSION-001/002 and frozen 003 artifacts/configs/inputs; no look-ahead/fabrication/forward-fill; today's rank ≠ historical truth; complete multiple-testing correction for any claim; do not reuse inspected holdout as fresh confirmation.

## End-of-session requirement
Leave clean state; update durable handoff/task message with verified evidence; leave a concrete next action. Never write "wait for a new experiment ID."

(End of file - total 47 lines)