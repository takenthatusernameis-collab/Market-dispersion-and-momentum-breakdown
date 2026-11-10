# Agent Task Message — 2026-11-10T20:23:45Z (session 20261110T202345Z)

## Current state (independently re-verified)
- **HEAD at read time:** `eb3bb10b` (verify with `git log --oneline -5`). Working tree clean before edits (`git status --porcelain` EXIT=0). This session modified only `research_state/agent_handoff.md` and `research_state/agent_task_message.md`. No code/script/test/doc/config/frozen-artifact changes.
- **Checks:** `python3 -m compileall -q scripts tests` EXIT=0. Full `unittest discover -s tests` re-run: 338 tests, 1 failure, 35 skipped — sole failure is `test_every_declared_requirement_imports` (env-only: numpy/pandas absent in this interpreter; no tracked changes, pre-existing gap). `unittest` exit=1 solely from that env-only gap.
- **Frozen integrity (sha256):** canonical `7234fc4e...5390` (`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`, n_formations=608, diff_net_1x +0.6165223953929935, date_last 2026-08-31, n_high=61, n_low=90); h10_fresh `324ab1e6...f18f` (n_formations=1, n_high=0, n_low=0, diff null, confirmatory_claim_allowed=false); registry `7faacdb3...4df4`; frontier `9ba08f3f...4f4e`; probe `ea002e9e...72ed`. Canonical hash re-verified against `git show HEAD:` — matches.
- **Cutoff gate (not re-probed — 2026-11-10 < 2026-11-30):** `research_state/cutoff_probe/cutoff_probe_20261110T135706Z.json` probe_utc 2026-11-10T13:57:06Z: `probe_month=2026-11, target_published=false, control_month=2026-09, control_ok=true, archive_alive=true, gate_met_by_month_end=true, cutoff_gate=BLOCKED, gate_date_required=2026-10-29`. **Do not re-probe before 2026-11-30.**
- **H10:** CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / EVALUATED_NULL_DIFF_IMMATURE; k not advanced. Inspected 003 holdout is exploratory evidence only, never fresh confirmation.

## Initial task for next agent
**No unblocked task exists today (2026-11-10 < 2026-11-30).** Not waiting for a manually supplied experiment ID.

### A) Before 2026-11-30 — only on a genuine bounded no-cost gap
- Acceptable: reproducible tracked code/audit/test defect (excluding env-only dependency absence), missing guard against frozen-artifact mutation, or reference-consistency drift — **only if** it does **not** alter frozen result artifacts, configs, scripts, tests, docs, prompts, `research_state/hypothesis_registry.json`, or `research_state/universe_frontier.json`.
- If no such gap: record "no unblocked task exists" with verification evidence (compileall, frozen hashes vs `git show HEAD:`, latest probe state, unittest status) and stop. Avoid idle churn beyond necessary durable-state update.

### B) On/after 2026-11-30 (date-gated)
1. `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`
2. If `target_published=true`: refresh free public data only (Coin Metrics Community API + Binance Public Data Archive); run `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests`; verify canonical hash `7234fc4e...5390` unchanged vs `git show HEAD:`; run a fresh sealed H10 block **only** into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--look-number 1` (30-day maturity, `MIN_ASSETS_DECIMAL=20`, trailing-decile, 0.05 economic threshold, sequential `alpha_k = 0.05/(k*(k+1))`).
3. Require `n_high > 0 AND n_low > 0` before any confirmatory claim. If still immature, record outcome and **do not advance k**. Preserve all frozen artifacts/configs unchanged.

## Hard constraints
Free public data only; historical research only (no orders/live/paper trading); preserve DISPERSION-001/002 and frozen 003 artifacts/configs; no look-ahead/fabrication/forward-fill; today's rank ≠ historical truth; complete multiple-testing correction for any claim; do not reuse inspected holdout as fresh confirmation.

## End-of-session requirement
Leave clean state; update durable handoff/task message with verified evidence; report only verified progress; leave a concrete next action. Never write "wait for a new experiment ID."

(End of file)
