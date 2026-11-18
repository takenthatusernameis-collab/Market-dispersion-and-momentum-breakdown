# Agent Task Message — 2026-11-18T06:52:38Z (next session)

## Verified state (2026-11-18T06:52:38Z, this session)

- **HEAD at this session:** `e38805e4faab1602dc2de58498191b54d48d0a49` (clean at read). `python3 -m compileall -q scripts tests` EXIT 0. No code or frozen-artifact changes since last green full suite.
- **Last verified full suite:** **1163 tests, OK, skipped=8, EXIT=0** (`python3 -m unittest discover -s tests`, 94.748s); record `research_state/session_verifications/session_verify_20261118T061700Z.json` (HEAD `96bcf6cd1e88c79b8939315928c4c6f18f165ba9`). This session verification: `research_state/session_verifications/session_verify_20261118T065238Z.json`.
- **Canonical/h10_fresh/grid (unchanged):** canonical forward block sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`; grid config `1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176`; frontier sha256 `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e`.
- **Probe evidence (disk):** 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`.
- **Frontier/registry:** frontier `historical_rank_coverage_state=NOT_PROVEN_COMPLETE`, `last_updated_utc=2026-11-06T12:27:02Z`, catalog exhausted, `expanding_universe_target_met=true`, `rank_frontier_exhausted=false`; registry `next_sequence_number` 46 (H1..H46 complete). H10 fresh sealed block immature and date-gated to **2026-11-30**.
- **No frozen artifact/config/input/frontier/registry/sealed-holdout modified; DISPERSION-001/002 unchanged.** Posture **BLOCKED_BY_HARD_DATE_GATE**.

## Initial task for next agent

Today is before **2026-11-30**. Last full suite is green (1163/OK/skipped=8) and no code/frozen-artifact changes have occurred since. **Do NOT add another verification-only checkpoint unless a real, new, safely bounded no-cost gap emerges.** H1..H46 are complete; do not re-run them. Do not re-probe `probe_month=2026-11` before 2026-11-30. If no new bounded gap exists, take no action beyond holding for the date gate.

**Fresh-runner prerequisite:** bare runner may lack `numpy`/`pandas`. Run `python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt` before the suite. `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-002/grid_result_ledger.json` is intentionally gitignored; the four ledger-pinning tests in `tests/test_f1_grid_vintage_trim.py` skip on a clean checkout by design.

**Option A — at/after 2026-11-30 (primary, date-gated):**
1. `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If `target_published=true`, refresh free public data only: `python3 scripts/refresh_free_data.py --price-end 2026-11-30 --cap-end 2026-11-30` (adjust only if protocol/source cutoffs require).
2. `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests` to completion.
3. Verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged vs `git show HEAD:artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`.
4. Run fresh sealed H10 block only into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--forward-block-start 2026-09-30 --data-cutoff <new cutoff>`. Require `n_high > 0 AND n_low > 0` before any confirmatory claim; preserve prior artifacts unchanged.
5. If tests/scripts change with a recordable claim, run `python3 scripts/record_test_claim.py`; update handoff, task message, and session verification record with exact commands/outcomes.

**Option B — only if a genuinely new bounded no-cost exploratory task with a NEW hypothesis/ID/artifact and real demonstrable gap becomes safely bounded before 2026-11-30:** preregister first, keep `EXPLORATORY_ONLY`/planning-only, and follow adaptive research-gate policy v1. Concretely: H46 already located ALPHA funding tail 2025-10..2026-10 as known trailing 404s (13 files) vs benign pre-listing absences (18); re-probing the same endpoints is not a distinct attempt. A NEW-ID bounded step is valid only if it targets a different admissible source/route or a justified estimand change (e.g. narrow expanding universe excluding ALPHA) with preregistration and explicit non-claim boundaries — never fabricating files. If no such gap exists, take no action beyond holding for the date gate.

**Recompute probe counts from disk; do not hard-code.** 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`.

## Durable-state rules

- Handoff top entry `## Session summary — <ts> (this session)` matching title timestamp; older entries `## Previous session — <ts>` unique and strictly descending.
- Keep literal `probe_month=2026-11` present whenever `2026-11` appears.
- Do not alter frontier, registry, frozen artifacts/configs/inputs, or sealed holdout.

## Hard constraints

Free public data only; historical research only; preserve DISPERSION-001/002 and frozen 003 artifacts; no look-ahead/fabrication; today's rank != historical truth.

## End-of-session requirement

Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID." Waiting for fixed calendar date **2026-11-30** is a date gate.
