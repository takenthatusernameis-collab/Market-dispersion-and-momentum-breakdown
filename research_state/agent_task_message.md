# Agent Task Message — 2026-11-12T21:53:38Z (next session)

## Verified state (2026-11-12T21:53:38Z)
- **HEAD:** `88a2e52a` (`main`). Prior durable task A (H23/F1COVERAGE-001 registry reference reconciliation + guard) complete and committed.
- **Checks:** `python3 -m compileall -q scripts tests` EXIT=0; `python3 -m unittest discover -s tests` → `Ran 363 tests`, `OK (skipped=1)`, EXIT=0.
- **Frozen hashes (unchanged):** canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`; registry `693b13097ebaee14e16b18906e698478a5ccc2df7bac5c135af571a28195c6e5`; `research_state/universe_frontier.json` `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e`.
- **H10/cutoff:** November 2026 not yet published in latest probe chain (`research_state/cutoff_probe/`). **Do not re-probe before 2026-11-30.** H10 gate UNBLOCKED by October archive; fresh block IMMATURE (`n_formations=1`, `n_high=0`, `n_low=0`); k not advanced. F1COVERAGE-001 repairs are EXPLORATORY_ONLY, outside sealed 003 inputs.
- **Frontier:** `ACTIVE_INCOMPLETE`, catalog exhausted (cursor 6347, verified 220, blocked 6127), `historical_rank_coverage_state=NOT_PROVEN_COMPLETE`, panel `2023-01-01..2026-10-31`.
- **No bounded no-cost task unblocked before 2026-11-30.**

## Initial task for next agent

### 1) On/after 2026-11-30 — H10 fresh sealed forward block (date-gated, bounded, no-cost)
This is the next executable action (date-gated, not an experiment-ID wait). Do **not** re-probe November 2026 before 2026-11-30.

1. Run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`.
2. If `target_published=true`:
   - Refresh free public data only (Coin Metrics Community API + Binance Public Data Archive).
   - Run `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests`.
   - Verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged.
   - Run fresh sealed H10 block **only** into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--forward-block-start 2026-09-30 --data-cutoff <new cutoff> --look-number 1` (30-day maturity, `MIN_ASSETS_DECIMAL=20`, trailing-decile, 0.05 economic threshold, sequential `alpha_k = 0.05/(k*(k+1))` per H22/prereg sec 4.1).
3. Require `n_high > 0 AND n_low > 0` before any confirmatory claim. If immature, record outcome and **do not advance k**.

### 2) If 2026-11-30 has not arrived (or probe remains blocked)
- Record "no bounded no-cost task unblocked before 2026-11-30" with verified evidence in handoff/task message and session verification. Do not loop on known-failed probes or invent work.

## Hard constraints
Free public data only; historical research only (no orders/live/paper trading); preserve DISPERSION-001/002 and frozen 003 artifacts/configs/inputs; no look-ahead/fabrication/forward-fill; today's rank ≠ historical truth; complete multiple-testing correction for any claim; do not reuse inspected holdout as fresh confirmation.

## End-of-session requirement
Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID."
