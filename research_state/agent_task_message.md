# Agent Task Message — 2026-11-12T18:20:25Z (next session)

## Verified state (2026-11-12T18:20:00Z)
- **HEAD:** `b5ce18ff4373cef36776dd17ad97ededc0078994` (`main`, clean working tree; advanced from `8e36e95e` via clean checkpoint commit).
- **Frozen hashes unchanged:** canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`; registry `7faacdb3f7add98a9e6bddf3c4ab3403fd812711dd0ca601b5ddda031a664df4`; frontier `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e`; latest probe `research_state/cutoff_probe/cutoff_probe_20261111T013459Z.json`.
- **Checks this session:** `python3 -m compileall -q scripts tests` EXIT=0; `python3 -m unittest discover -s tests` → `Ran 348 tests in 59.493s`, `OK (skipped=1)`, EXIT=0.
- **November 2026 probe (verdict only, NOT H10 gate):** `cutoff_probe_20261111T013459Z.json` — `probe_month=2026-11`, `target_published=false`. **Do not re-probe before 2026-11-30.**
- **H10 cutoff gate:** UNBLOCKED by October 2026 archive (probe 2026-11-05T10:38:51Z, `probe_month=2026-10`, `target_published=true`).
- **Frontier:** `ACTIVE_INCOMPLETE`, catalog exhausted (cursor 6347, verified 220, blocked 6127), `historical_rank_coverage_state=NOT_PROVEN_COMPLETE`, panel `2023-01-01..2026-10-31`.
- **H10:** CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / EVALUATED_NULL_DIFF_IMMATURE (`n_formations=1`, `n_high=0`, `n_low=0`, `high_low_diff_net_1x=null`); k not advanced.

## Prior task — complete
Read prior durable handoff/task (2026-11-12T18:15:30Z): no unblocked task before 2026-11-30. Re-verified state (HEAD b5ce18ff, clean tree, hashes, compileall, 348 tests) and updated durable handoff/task message. No bounded gap found.

## Initial task for next agent

### A) Before 2026-11-30 — only on a genuine bounded no-cost gap
Do not re-probe November 2026 before 2026-11-30. Acceptable work only if a specific reproducible tracked code/audit/test defect (excluding env-only dependency absence), missing frozen-artifact-mutation guard, or reference-consistency drift exists — and it does not alter frozen result artifacts, configs, scripts, tests, docs, prompts, `research_state/hypothesis_registry.json`, or `research_state/universe_frontier.json`. Fix with tests/audit evidence. If no such gap exists, record "no unblocked task exists" with verification evidence and stop. Do not repeat verification or audit the same frozen block without a specific new question.

### B) On/after 2026-11-30 (date-gated, executable)
1. `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`
2. If `target_published=true`: refresh free public data only (Coin Metrics Community API + Binance Public Data Archive); run `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests` (install deps via `python3 -m pip install -r requirements.txt` if needed); verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged; run fresh sealed H10 block **only** into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--look-number 1` (30-day maturity, `MIN_ASSETS_DECIMAL=20`, trailing-decile, 0.05 economic threshold, sequential `alpha_k = 0.05/(k*(k+1))`).
3. Require `n_high > 0 AND n_low > 0` before any confirmatory claim. If still immature, record outcome and **do not advance k**. Preserve all frozen artifacts/configs unchanged. Expect ~26 eligible assets unless F1 repaired via separate new-ID route.

### C) F1 repair — new ID required, do NOT touch sealed inputs
Any panel-input repair requires NEW hypothesis/experiment ID, preregistration, and new artifact paths. Minimal: fetch missing keyless zips (4 symbols × 2025-01..2026-09 × {klines,funding}) from `https://data.binance.vision/data/futures/um` into a **new** panel directory; never overwrite `data/panels/`, `data/raw/`, or frozen 003 artifacts. Label EXPLORATORY_ONLY unless full confirmatory gates re-run on admissible data.

## Hard constraints
Free public data only; historical research only (no orders/live/paper trading); preserve DISPERSION-001/002 and frozen 003 artifacts/configs/inputs; no look-ahead/fabrication/forward-fill; today's rank ≠ historical truth; complete multiple-testing correction for any claim; do not reuse inspected holdout as fresh confirmation.

## End-of-session requirement
Leave clean state; update durable handoff/task message with verified evidence; leave a concrete next action. Never write "wait for a new experiment ID".
