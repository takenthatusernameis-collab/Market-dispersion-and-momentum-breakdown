# Agent Task Message — 2026-11-12T23:06:27Z (next session)

## Verified state (2026-11-12T23:06:27Z)
- **HEAD at session start:** `59461fe6` (`main`). Working tree clean; later checkpoints after `6be62a28` contain only research_state text/verification changes.
- **This session completed:** read durable handoff/task message, reverified state, recomputed probe evidence from disk, recorded `research_state/session_verifications/session_verify_20261112T230627Z.json`, and refreshed the durable handoff/task for the next agent.
- **Checks:** `python3 -m compileall -q scripts tests` EXIT=0. `python3 -m unittest discover -s tests` → 370 tests, OK, 2 skipped. `git diff --stat -- artifacts/ configs/` empty. Grid ledger: 216 expected / 216 evaluated / 216 OK / 0 blocked / 0 failed.
- **Frozen hashes (verified on disk, unchanged):** canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`; `research_state/hypothesis_registry.json` `693b13097ebaee14e16b18906e698478a5ccc2df7bac5c135af571a28195c6e5`; `research_state/universe_frontier.json` `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e`.
- **Probe evidence (recomputed from disk):** 391 total `research_state/cutoff_probe/cutoff_probe_*.json` records; 122 records carry `probe_month=2026-11`; all `target_published=false` and all `cutoff_gate=BLOCKED`; newest is `research_state/cutoff_probe/cutoff_probe_20261112T225937Z.json` (`probe_utc=2026-11-12T22:59:37Z`). Archive alive via the 2026-09 control month.
- **H10 gate vs probe (two distinct verdicts):** H10 cutoff gate **UNBLOCKED** by the published October 2026 archive. The `probe_month=2026-11` probe is **BLOCKED as a probe only** and is never promoted to the gate decision. Fresh block IMMATURE (`n_formations=1`, `n_high=0`, `n_low=0`); k not advanced. F1COVERAGE-001 repairs are EXPLORATORY_ONLY, outside sealed 003 inputs.
- **Frontier:** `ACTIVE_INCOMPLETE`, catalog exhausted (cursor 6347, verified 220, blocked 6127), `historical_rank_coverage_state=NOT_PROVEN_COMPLETE`, panel `2023-01-01..2026-10-31`.
- **No bounded no-cost H10 task unblocked before 2026-11-30.** Today is 2026-11-12; the H10 maturity date is 2026-11-30.

## Initial task for next agent

### 1) On/after 2026-11-30 — H10 fresh sealed forward block (date-gated, bounded, no-cost)
This is the next executable action (date-gated, not an experiment-ID wait). Do **not** re-probe `probe_month=2026-11` before 2026-11-30.

1. Run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`.
2. If `target_published=true`:
   - Refresh free public data only (Coin Metrics Community API + Binance Public Data Archive).
   - Run `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests`.
   - Verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged.
   - Run the fresh sealed H10 block **only** into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--forward-block-start 2026-09-30 --data-cutoff <new cutoff> --look-number 1` (30-day maturity, `MIN_ASSETS_DECIMAL=20`, trailing-decile, 0.05 economic threshold, sequential `alpha_k = 0.05/(k*(k+1))` per H22/prereg sec 4.1).
3. Require `n_high > 0 AND n_low > 0` before any confirmatory claim. If immature, record the outcome and **do not advance k**.
4. After a completed or blocked block, run `python3 scripts/record_test_claim.py` if any test/script changed, then update the handoff, task message and a new session verification record.

### 2) If 2026-11-30 has not arrived (or the probe remains blocked)
- Record "no bounded no-cost H10 task unblocked before 2026-11-30" with verified evidence in the handoff/task message and a session verification record. Do not loop on known-failed probes or invent work.
- The 30-day maturity rule and the ">=30 prior in-block dispersions" trailing-decile rule are hard; no truncated outcome and no exploratory relaxation of the H10 estimand is admissible.
- Prefer a bounded, no-cost local task (tests, consistency checks) only if you first demonstrate a real gap; do not add duplicate audits.
- If you touch the durable handoff/task message, keep the literal `probe_month=2026-11` label present whenever `2026-11` appears, and never assert the H10 cutoff gate as blocked; `tests/test_h10_gate_vs_november_probe.py` enforces both.
- Do not alter the frontier, the registry, frozen 003 artifacts/configs/inputs or the sealed holdout. The `latest_november_2026_probe` pointer lag is guard-permitted; do not repoint it by editing the frontier.

## Hard constraints
Free public data only; historical research only (no orders/live/paper trading); preserve DISPERSION-001/002 and frozen 003 artifacts/configs/inputs; no look-ahead/fabrication/forward-fill; today's rank ≠ historical truth; complete multiple-testing correction for any claim; do not reuse inspected holdout as fresh confirmation.

## End-of-session requirement
Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID."

(End of file)
