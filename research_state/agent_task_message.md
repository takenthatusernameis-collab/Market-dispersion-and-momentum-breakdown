# Agent Task Message — 2026-11-17T23:03:58Z (next session)

## Verified state (2026-11-17T23:03:58Z)

- **HEAD at verification:** `db874853bcea38968e353c02e4f9d2435af6c68a`. Working tree clean at verification. `python3 -m compileall -q scripts tests` EXIT 0. Full suite not rerun (no code/test/script changes this session); last recorded green run `research_state/session_verifications/session_verify_20261117T211552Z.json` (HEAD `d89decbb0e698dabdddefd1e9e97a2d87b4d1c36`, **1144 tests, OK, skipped=8, EXIT=0**, claim 1144/1144/0).
- **This session:** read durable handoff/task (prior 2026-11-17T22:54:13Z) and completed it. Re-verified compileall, canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` (sha256 of `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`), probe census, grid summary (`expected_cells=216`, `evaluated_utc=2026-10-24T10:46:30Z`), H10 fresh sealed block (`n_formations=1`, `n_high=0`, `n_low=0`, `n_mid=1`, `confirmatory_claim_allowed=false`, `evaluated_utc=2026-11-02T15:18:56Z`), and frontier `historical_rank_coverage_state=NOT_PROVEN_COMPLETE` / `last_updated_utc=2026-11-06T12:27:02Z` from disk. Registry per prior verified durable state: `next_sequence_number` 45 (H1..H45 complete). Searched for a real, new, safely bounded no-cost gap — none found before 2026-11-30. No new economic evidence and none presented as progress. No frozen artifact/config/input/frontier/registry/sealed-holdout modified; DISPERSION-001/002 unchanged. Posture **BLOCKED_BY_HARD_DATE_GATE**.
- **Probe evidence (disk, recomputed):** 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`.
- **Frozen hash unchanged (disk, recomputed):** canonical forward block `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`.

## Initial task for next agent

Today is before 2026-11-30. **Do NOT loop.** State is verified stable and the suite is green; do not add another verification-only checkpoint unless a real, new, safely bounded no-cost gap emerges. H39–H45 are complete; do not re-run. H10 cutoff gate itself UNBLOCKED by the published October 2026 archive. `probe_month=2026-11` probe remains BLOCKED as a probe only (0 `target_published=true`), not promoted. If no new bounded gap exists, take no action beyond holding for the date gate.

**Fresh-runner prerequisite:** bare runner has no `numpy`/`pandas`. Run `python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt` before the suite, or expect `ModuleNotFoundError` (see `requirements.txt`). `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-002/grid_result_ledger.json` is intentionally gitignored; the four ledger-pinning tests in `tests/test_f1_grid_vintage_trim.py` skip on a clean checkout by design (not a failure).

**Option A — at/after 2026-11-30 (primary, date-gated):**
1. `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If `target_published=true`, refresh free public data only.
2. `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests` to completion.
3. Verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged vs `git show HEAD:`.
4. Run fresh sealed H10 block only into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--forward-block-start 2026-09-30 --data-cutoff <new cutoff> --look-number 1`. Require `n_high > 0 AND n_low > 0` before any confirmatory claim.
5. If tests/scripts change with a recordable claim, run `python3 scripts/record_test_claim.py`; update handoff, task message, and session verification record.

**Option B — only if a genuinely new bounded no-cost exploratory task with a NEW hypothesis/ID/artifact and real demonstrable gap becomes safely bounded before 2026-11-30:** preregister first, keep `EXPLORATORY_ONLY`/planning-only. If no such gap exists, take no action beyond holding for the date gate.

**Probe-evidence invariant:** recompute probe counts from disk; do not hard-code.
**Recompute probe counts from disk:** 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`.

## Durable-state rules
- Handoff top entry `## Session summary — <ts> (this session)` matching title timestamp; older entries `## Previous session — <ts>` unique and strictly descending.
- Keep literal `probe_month=2026-11` present whenever `2026-11` appears.
- Do not alter frontier, registry, frozen artifacts/configs/inputs, or sealed holdout.

## Hard constraints
Free public data only; historical research only; preserve DISPERSION-001/002 and frozen 003 artifacts; no look-ahead/fabrication; today's rank != historical truth.

## End-of-session requirement
Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID." Waiting for fixed calendar date 2026-11-30 is a date gate.
