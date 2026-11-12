# Agent Task Message — 2026-11-12T16:05:01Z (current session)

## Verified state
- **HEAD:** `4fed6201abf1389d86e028ccaebdd92bfa9badac` (`main` up to date with `origin/main`, clean tracked tree at verify start; only untracked additive audit JSON outputs from this pass). Prior delta checkpoint-only; no tracked `artifacts/ configs/ docs/ prompts/ scripts/ tests/` changes.
- **Hashes unchanged (re-verified 2026-11-12T16:05:01Z):** canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`, h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`, registry `7faacdb3f7add98a9e6bddf3c4ab3403fd812711dd0ca601b5ddda031a664df4`, frontier `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e`, latest probe `25c11cbae9e62c9f5feb41d9f2de09a996dd4a0a1ddcfa4828ecc05daa73f7e6`.
- **November 2026 probe (probe verdict only, NOT H10 gate):** `research_state/cutoff_probe/cutoff_probe_20261111T013459Z.json` — `probe_month=2026-11`, `target_published=false`, blocked. **Do not re-probe before 2026-11-30.**
- **H10 cutoff gate:** UNBLOCKED by published October 2026 archive (real probe 2026-11-05T10:38:51Z, `cutoff_probe_20261105T103851Z.json`, `probe_month=2026-10`, `target_published=true`; `run_manifest.json` -> `latest_archive_probe`). Gate date 2026-10-29; November 404s do not block H10.
- **Frontier:** `ACTIVE_INCOMPLETE`, catalog exhausted (cursor 6347, verified 220, blocked 6127), `historical_rank_coverage_state=NOT_PROVEN_COMPLETE`, panel `2023-01-01..2026-10-31`.
- **H10:** CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / EVALUATED_NULL_DIFF_IMMATURE; k not advanced. Inspected 003 holdout is not fresh confirmation.
- **Verified test claim:** `348/348/0` (manifest == snapshot), fingerprint `943f5e1f411dd13cd06a02d0f128c02a4c40033920a888244fad31827c311af0`, 104 input files. Independently re-confirmed this pass: `python3 -m unittest discover -s tests` Ran 348 tests, OK (skipped=1), EXIT=0 (58.830s).
- **Checks run this session (25th pass):** `python3 -m compileall -q scripts tests` EXIT=0; `python3 -m unittest discover -s tests` Ran 348 tests, OK (skipped=1), EXIT=0 (58.830s); `audit_integrity_audit_references.py` pass (scanned=14, critical=0, errors=0, info=8); `audit_prereg_and_h10_fresh_references.py` pass (scanned=13, prereg=9, h10=1, forward_block=1, critical=0, errors=0); `audit_preregistration_coverage.py` pass (audits=14, missing_prereq=0, uncovered_prereq=0). No reproducible tracked code/audit/test defect, missing guard, or reference-consistency drift found.

## Initial task for next agent
**No unblocked task exists today (2026-11-12 < 2026-11-30).** Not waiting for a manually supplied experiment ID. Remaining gate is the date-gated November 2026 cutoff probe. Avoid idle churn. Verification evidence recorded in `research_state/session_verifications/session_verify_20261112T160501Z.json` (plus prior `session_verify_20261112T151904Z.json`, `session_verify_20261112T152914Z.json`, `session_verify_20261112T153302Z.json`) and regenerated audit outputs `research_state/INTEGRITY_AUDIT_REFERENCE_CONSISTENCY_20261112T160446Z.json`, `research_state/PREREG_AND_H10_FRESH_REFERENCE_CONSISTENCY_20261112T160446Z.json`, `research_state/preregistration_coverage_audit.json` (no frozen artifact changed).

### A) Before 2026-11-30 — only on a genuine bounded no-cost gap
- Acceptable: reproducible tracked code/audit/test defect (excluding env-only dependency absence), missing guard against frozen-artifact mutation, or reference-consistency drift — **only if** it does **not** alter frozen result artifacts, configs, scripts, tests, docs, prompts, `research_state/hypothesis_registry.json`, or `research_state/universe_frontier.json`.
- To confirm no defect, **re-run the full suite** (`python3 -m unittest discover -s tests`) rather than trusting the recorded snapshot.
- If no such gap: record "no unblocked task exists" with verification evidence (session verify record + audit outputs) and stop.

### B) On/after 2026-11-30 (date-gated) — executable next task
1. `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`
2. If `target_published=true`: refresh free public data only (Coin Metrics Community API + Binance Public Data Archive); run `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests` (install deps via `python3 -m pip install -r requirements.txt` if needed); verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged; run fresh sealed H10 block **only** into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--look-number 1` (30-day maturity, `MIN_ASSETS_DECIMAL=20`, trailing-decile, 0.05 economic threshold, sequential `alpha_k = 0.05/(k*(k+1))`).
3. Require `n_high > 0 AND n_low > 0` before any confirmatory claim. If still immature, record outcome and **do not advance k**. Preserve all frozen artifacts/configs unchanged.

## Hard constraints
Free public data only; historical research only (no orders/live/paper trading); preserve DISPERSION-001/002 and frozen 003 artifacts/configs; no look-ahead/fabrication/forward-fill; today's rank ≠ historical truth; complete multiple-testing correction for any claim; do not reuse inspected holdout as fresh confirmation.

## End-of-session requirement
Leave clean state; update durable handoff/task message with verified evidence; report only verified progress; leave a concrete next action. Never write "wait for a new experiment ID".
