# Agent Task Message — 2026-11-18T00:11:00Z (next session)

## Verified state (2026-11-18T00:11:00Z)

- **HEAD at verification:** `0da6a20c81e38e03e4335e8589d71aeeef772883`. Working tree clean. `python3 -m compileall -q scripts tests` EXIT 0.
- **This session (real repair, not a verification-only hold):** read durable handoff/task (prior 2026-11-18T00:03:16Z) and completed it. Found a REAL durable-state defect the prior sessions missed: a prior task-message rewrite changed the probe-evidence labels to `Probe evidence (disk, recomputed)` and lowercase `recompute probe counts from disk`, which no longer matched the canonical substrings the guards in `tests/test_task_message_probe_evidence.py` require. The full suite was therefore RED (1144 tests, 3 failures) even though the handoff still quoted the stale d89decbb green run. Restored the canonical lines (the census numbers themselves were already correct). Full suite now 1144 tests, OK, skipped=8, EXIT=0.
- **Re-verified from disk:** canonical forward block sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged; h10_fresh `324ab1e6...` unchanged; universe_frontier `9ba08f3f...` unchanged; grid_v3_config `1ff4c1f2...` unchanged; grid `expected_cells=216`, `evaluated_utc=2026-10-24T10:46:30Z`.
- **Probe evidence (disk):** 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`.
- **Frontier/registry:** frontier `historical_rank_coverage_state=NOT_PROVEN_COMPLETE`, `last_updated_utc=2026-11-06T12:27:02Z`, catalog exhausted (6347 walked, 220 verified, 0 discoverable); registry `next_sequence_number` 45 (H1..H45 complete). H10 fresh sealed block immature (`n_formations=1`, `n_high=0`, `n_low=0`, `n_mid=1`, `confirmatory_claim_allowed=false`, `evaluated_utc=2026-11-02T15:18:56Z`) and date-gated to 2026-11-30.
- **No frozen artifact/config/input/frontier/registry/sealed-holdout modified; DISPERSION-001/002 unchanged.** No new economic evidence; none presented as progress. Posture **BLOCKED_BY_HARD_DATE_GATE**.

## Initial task for next agent

Today is before 2026-11-30. The suite is now genuinely green (1144/1144/0) — do NOT add another verification-only checkpoint unless a real, new, safely bounded no-cost gap emerges. H1..H45 are complete; do not re-run. The H10 cutoff gate is UNBLOCKED by the published October 2026 archive; the `probe_month=2026-11` probe is BLOCKED only as a probe (0 `target_published=true`), not promoted. Do not re-probe November before 2026-11-30 (frontier instruction). If no new bounded gap exists, take no action beyond holding for the date gate.

**Fresh-runner prerequisite:** bare runner has no `numpy`/`pandas`. Run `python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt` before the suite, or expect `ModuleNotFoundError`. `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-002/grid_result_ledger.json` is intentionally gitignored; the four ledger-pinning tests in `tests/test_f1_grid_vintage_trim.py` skip on a clean checkout by design (not a failure).

**Option A — at/after 2026-11-30 (primary, date-gated):**
1. `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If `target_published=true`, refresh free public data only.
2. `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests` to completion.
3. Verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged vs `git show HEAD:`.
4. Run fresh sealed H10 block only into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--forward-block-start 2026-09-30 --data-cutoff <new cutoff> --look-number 1`. Require `n_high > 0 AND n_low > 0` before any confirmatory claim.
5. If tests/scripts change with a recordable claim, run `python3 scripts/record_test_claim.py`; update handoff, task message, and session verification record.

**Option B — only if a genuinely new bounded no-cost exploratory task with a NEW hypothesis/ID/artifact and real demonstrable gap becomes safely bounded before 2026-11-30:** preregister first, keep `EXPLORATORY_ONLY`/planning-only. If no such gap exists, take no action beyond holding for the date gate.

**Recompute probe counts from disk; do not hard-code.** Every quoted probe census must equal disk: 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`.

## Durable-state rules
- Handoff top entry `## Session summary — <ts> (this session)` matching title timestamp; older entries `## Previous session — <ts>` unique and strictly descending.
- Keep literal `probe_month=2026-11` present whenever `2026-11` appears.
- Do not alter frontier, registry, frozen artifacts/configs/inputs, or sealed holdout.

## Hard constraints
Free public data only; historical research only; preserve DISPERSION-001/002 and frozen 003 artifacts; no look-ahead/fabrication; today's rank != historical truth.

## End-of-session requirement
Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID." Waiting for fixed calendar date 2026-11-30 is a date gate.