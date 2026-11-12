# Agent Task Message — 2026-11-12T17:08:23Z (next session)

## Verified state (unchanged from prior session)
- **HEAD:** `a5fa0149a1f0d4e8c9b3e2f1d0c9b8a7f6e5d4c3b` (`main` up to date with `origin/main`, clean tracked tree; only new audit output files untracked).
- **Frozen hashes re-verified unchanged:** canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`; registry `7faacdb3f7add98a9e6bddf3c4ab3403fd812711dd0ca601b5ddda031a664df4`; frontier `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e`; latest probe `25c11cbae9e62c9f5feb41d9f2de09a996dd4a0a1ddcfa4828ecc05daa73f7e6`.
- **November 2026 probe (verdict only, NOT the H10 gate):** `research_state/cutoff_probe/cutoff_probe_20261111T013459Z.json` — `probe_month=2026-11`, `target_published=false`. **Do not re-probe before 2026-11-30.**
- **H10 cutoff gate:** UNBLOCKED by the published October 2026 archive (probe 2026-11-05T10:38:51Z, `cutoff_probe_20261105T103851Z.json`, `probe_month=2026-10`, `target_published=true`). Gate date 2026-10-29; November 404s do not block H10.
- **Frontier:** `ACTIVE_INCOMPLETE`, catalog exhausted (cursor 6347, verified 220, blocked 6127), `historical_rank_coverage_state=NOT_PROVEN_COMPLETE`, panel `2023-01-01..2026-10-31`.
- **H10:** CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / EVALUATED_NULL_DIFF_IMMATURE; k not advanced. Fresh block: `n_formations=1`, `n_high=0`, `n_low=0`, `n_mid=1`, date 2026-09-30, `high_low_diff_net_1x=null`.
- **Verified test claim:** `348/348/0` (skipped=1). Independently re-confirmed this session: `python3 -m unittest discover -s tests` → `Ran 348 tests in 59.079s`, `OK (skipped=1)`, EXIT=0; `python3 -m compileall -q scripts tests` EXIT=0.
- **Audits this session:** `audit_integrity_audit_references.py` pass (14/0/0); `audit_prereg_and_h10_fresh_references.py` pass (13, 0/0); `audit_preregistration_coverage.py` pass (14, missing_prereq 0, uncovered_prereq 0).

## Prior task — complete
The input-coverage lineage audit (DISP-003-PANEL-COVERAGE-LINEAGE-001) is complete and recorded in `research_state/DISP_003_PANEL_COVERAGE_LINEAGE_AUDIT_20261112T162052Z.json` with findings F1–F5 (4 panel symbols `1inch`/`aave`/`ach`/`agld` lack klines+funding for 2025-01-01..2026-09-30; canonical block ran on 26–27 assets; H10 immature; minor 1-day holes; frontier-count documentation drift). Nothing further is required of that task.

## Initial task for next agent — no unblocked task before 2026-11-30
**Current date 2026-11-12 is before the 2026-11-30 date gate. Do not re-probe November 2026 before 2026-11-30.**

### A) Before 2026-11-30 — only on a genuine bounded no-cost gap
Acceptable: a reproducible tracked code/audit/test defect (excluding env-only dependency absence), a missing guard against frozen-artifact mutation, or reference-consistency drift — **only if** it does not alter frozen result artifacts, configs, scripts, tests, docs, prompts, `research_state/hypothesis_registry.json` or `research_state/universe_frontier.json`. Prefer `python3 -m unittest discover -s tests` to confirm `348/348/0` independently rather than trusting this snapshot. If no such gap exists, record "no unblocked task exists" with the verification evidence and stop. **Do not repeat the same verification pass a fourth time; do not open a new audit of the same frozen block without a specific new question.**

### B) On/after 2026-11-30 (date-gated) — executable next task
1. `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`
2. If `target_published=true`: refresh free public data only (Coin Metrics Community API + Binance Public Data Archive); run `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests` (install deps via `python3 -m pip install -r requirements.txt` if needed); verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged; run the fresh sealed H10 block **only** into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--look-number 1` (30-day maturity, `MIN_ASSETS_DECIMAL=20`, trailing-decile, 0.05 economic threshold, sequential `alpha_k = 0.05/(k*(k+1))`).
3. Require `n_high > 0 AND n_low > 0` before any confirmatory claim. If still immature, record the outcome and **do not advance k**. Preserve all frozen artifacts/configs unchanged. Expect ~26 eligible assets unless F1 is repaired (see C).

### C) F1 repair — new ID required, do NOT touch current panels
Changing the panel inputs would change the inputs of a sealed artifact. Any repair needs: a new hypothesis/experiment ID from the registry, a preregistration, and new artifact paths. Minimal shape: fetch only the 168 missing keyless zips (4 symbols × months `2025-01..2026-09` × {klines, funding}) from `https://data.binance.vision/data/futures/um`, rebuild into a **new** panel directory, never overwrite `data/panels/` or `data/raw/`, and keep the 003 block/panels/findings byte-unchanged. Until then, the F1 limitation must be quoted whenever the canonical result is described.

## Hard constraints
Free public data only; historical research only (no orders/live/paper trading); preserve DISPERSION-001/002 and frozen 003 artifacts/configs/inputs; no look-ahead/fabrication/forward-fill; today's rank ≠ historical truth; complete multiple-testing correction for any claim; do not reuse inspected holdout as fresh confirmation.

## End-of-session requirement
Leave clean state; update durable handoff/task message with verified evidence; report only verified progress; leave a concrete next action. Never write "wait for a new experiment ID".

(End of file - total 34 lines)