# Agent Task Message — 2026-11-18T16:17:30Z (next session)

## Initial task for next agent

Today is 2026-11-18, which is **before** the hard date gate **2026-11-30**. Read the durable handoff (`research_state/agent_handoff.md`, newest `## Session summary — 2026-11-18T16:17:30Z`) and this message. Then **hold**: do not re-run completed hypotheses, do not re-probe `probe_month=2026-11` before the gate, and do not add another verification-only checkpoint unless a genuinely new, safely bounded no-cost gap emerges.

## Verified state (2026-11-18T16:17:30Z, this session)

- **HEAD at read:** `bbc361b9db1529f81d70cb4b227ce62d5ef1752d` (clean working tree; `git status --short` empty). `python3 -m compileall -q scripts tests` EXIT 0.
- **Last verified full suite:** **1163 tests, OK, skipped=8, EXIT=0** (`python3 -m unittest discover -s tests`, 95.015s); last green verification `research_state/session_verifications/session_verify_20261118T080055Z.json` (HEAD `2d6d1934cec45f200584dc98fb569e6193313de1`, no code/frozen-artifact changes since). This session: compileall EXIT 0; no new verification record. Newest verification record on disk: `research_state/session_verifications/session_verify_20261118T104617Z.json`.
- **Canonical/h10_fresh/grid/frontier (unchanged):** canonical forward block sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` matches disk; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f` (`block_sealed=true`, `n_formations=1`, `n_high=0`, `n_low=0`, `n_mid=1`, `confirmatory_claim_allowed=false`, `evaluated_utc=2026-11-02T15:18:56Z`) matches disk; grid config `1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176` (`configs/dispersion_momentum_grid_v3.json`) matches disk; frontier sha256 `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e` (`historical_rank_coverage_state=NOT_PROVEN_COMPLETE`, `last_updated_utc=2026-11-06T12:27:02Z`, `expanding_universe_target_met=true`, `rank_frontier_exhausted=false`) matches disk.
- **Probe evidence (disk):** 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`. 398 probe files total incl. 1 distinct `daily_fundingRate_probe_*.json` probe type not part of the 397 cutoff-probe census.
- **Registry:** `research_state/hypothesis_registry.json` `next_sequence_number` 46 (H1..H46 complete). H10 fresh sealed block immature and date-gated to **2026-11-30**.
- **No frozen artifact/config/input/frontier/registry/sealed-holdout modified; DISPERSION-001/002 unchanged.** Posture **BLOCKED_BY_HARD_DATE_GATE**.

## Fresh-runner prerequisite

Bare runner may lack `numpy`/`pandas`. Run `python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt` before the suite. `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-002/grid_result_ledger.json` is intentionally gitignored; the four ledger-pinning tests in `tests/test_f1_grid_vintage_trim.py` skip on a clean checkout by design.

## Option A — at/after 2026-11-30 (primary, date-gated)

1. `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If `target_published=true`, refresh free public data only: `python3 scripts/refresh_free_data.py --price-end 2026-11-30 --cap-end 2026-11-30` (adjust only if protocol/source cutoffs require).
2. `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests` to completion.
3. Verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged vs `git show HEAD:artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`.
4. Run fresh sealed H10 block only into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--forward-block-start 2026-09-30 --data-cutoff <new cutoff>`. Require `n_high > 0 AND n_low > 0` before any confirmatory claim; preserve prior artifacts unchanged.
5. If tests/scripts change with a recordable claim, run `python3 scripts/record_test_claim.py`; update handoff, task message, and session verification record with exact commands/outcomes.

## Option B — only if a genuinely new bounded no-cost exploratory task with a NEW hypothesis/ID/artifact and real demonstrable gap becomes safely bounded before 2026-11-30

Preregister first, keep `EXPLORATORY_ONLY`/planning-only, and follow adaptive research-gate policy v1. H46 already located ALPHA funding tail 2025-10..2026-10 as known trailing 404s (13 files) vs benign pre-listing absences (18); re-probing the same endpoints is not a distinct attempt. A NEW-ID bounded step is valid only if it targets a different admissible source/route or a justified estimand change (e.g. narrow expanding universe excluding ALPHA) with preregistration and explicit non-claim boundaries — never fabricating files. If no such gap exists, take no action beyond holding for the date gate.

## Durable-state rules

- Handoff top entry `## Session summary — <ts> (this session)` matching title timestamp; older entries `## Previous session — <ts>` unique and strictly descending.
- Recompute probe counts from disk; do not hard-code. 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`.
- Keep literal `probe_month=2026-11` present whenever `2026-11` appears.
- Do not alter frontier, registry, frozen artifacts/configs/inputs, or sealed holdout.

## Hard constraints

Free public data only; historical research only; preserve DISPERSION-001/002 and frozen 003 artifacts; no look-ahead/fabrication; today's rank != historical truth.

## End-of-session requirement

Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID." Waiting for fixed calendar date **2026-11-30** is a date gate.

(End of file)
