# Agent Task Message — 2026-11-17T13:21:11Z (next session)

## Verified state (2026-11-17T13:21:11Z)

- **HEAD:** `7d4523c3e5dbb97cb22e53d69da1d0c04f4b46b5` (prior recorded checkpoint `c4d7697967992bf0212e1162fb8a162ce9d87070`). `python3 -m compileall -q scripts tests` EXIT 0. Full suite rerun this session: `python3 -m unittest discover -s tests` -> 1144 tests, OK, skipped=2, EXIT=0. Newest on-disk verification `research_state/session_verifications/session_verify_20261117T132111Z.json`.
- **This session:** read durable handoff/task (2026-11-17T13:18:27Z) and completed it by re-verifying stable repository state from disk at HEAD `7d4523c3`: compileall EXIT 0, full suite 1144 OK skipped=2 EXIT 0, frozen hashes recomputed and unchanged, probe census recomputed from disk and matching the quoted guard line. Date gate **2026-11-17 < 2026-11-30** holds. No new real bounded no-cost gap emerged before 2026-11-30 (H42–H45 complete, H45/F1GRID-FLIP-001 artifacts present). This was a durable-state refresh, not new economic evidence; per AGENTS.md a repeated verification-only session must not be presented as progress. No frozen artifact/config/input/frontier/registry/sealed-holdout modified; DISPERSION-001/002 unchanged.
- **Probe evidence (disk):** 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`.
- **Frozen hashes unchanged (disk, recomputed):** canonical forward block `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`; grid_result_ledger `0184f2d3e5d63dc6fb23a45f0ddfb226a195324d153615588c6c1363a74ce04c` (`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/grid_result_ledger.json`); universe_frontier `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e` (`research_state/universe_frontier.json`); grid v3 config `1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176` (`configs/dispersion_momentum_grid_v3.json`).
- **Block/probe:** canonical H004V106 `n_formations=608` (n_high=61, n_low=90, n_mid=457), `data_cutoff_utc` 2026-09-30, `last_allowed_formation_date` 2026-08-31, `block_sealed=true`, `high_low_diff_net_1x=0.6165223953929935`. H10 fresh IMMATURE (`n_formations=1`, n_high=0, n_low=0, n_mid=1, `data_cutoff_utc` 2026-10-31T00:00:00Z, `last_allowed_formation_date` 2026-09-30, `block_sealed=true`); k not advanced.
- **Registry/frontier:** `next_sequence_number`=45 (H1..H45). Frontier `ACTIVE_INCOMPLETE`, `rank_frontier_exhausted=false`, `candidate_page_cursor=6347`, `last_verified_historical_rank=null`, `expanding_universe_target_met=true`, `candidates_discovered=[]`. H10 cutoff gate itself UNBLOCKED by published October 2026 archive (`gate_date_required` 2026-10-29 met). `probe_month=2026-11` probe remains BLOCKED as probe only (0 `target_published=true`), not promoted.

## Initial task for next agent

Today is before 2026-11-30. **Do NOT loop.** State is verified stable; do not add another verification-only checkpoint unless a real, new, safely bounded gap emerges. H42–H45 are complete; do not re-run PANELCOV-FEAS-001/H41–H45/F1GRID-FLIP-001 or add near-duplicate seam/audits. H40/H41 tooling is hermetic — do not reintroduce tests that write into `artifacts/`. The probe-census quote in this file is pinned to disk by `tests/test_task_message_probe_evidence.py`: if you refresh probe lines, recompute from `research_state/cutoff_probe/` (never hard-code) or the guard fails.

**Option A — at/after 2026-11-30 (primary, date-gated):**
1. `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If `target_published=true`, refresh free public data only (Coin Metrics Community API + Binance Public Data Archive) with per-file provenance/SHA256 and PIT discipline.
2. `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests` to completion.
3. Verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged vs `git show HEAD:`.
4. Run fresh sealed H10 block **only** into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--forward-block-start 2026-09-30 --data-cutoff <new cutoff> --look-number 1` (30-day maturity, MIN_ASSETS_DECILES=20, trailing-decile, 0.05 economic threshold, sequential alpha_k = 0.05/(k*(k+1))). Require `n_high > 0 AND n_low > 0` before any confirmatory claim; if immature, record outcome and **do not advance k**.
5. If tests/scripts change with a recordable claim, run `python3 scripts/record_test_claim.py`; update handoff, task message, and a session verification record.

**Option B — only if a genuinely new bounded no-cost exploratory task with a NEW hypothesis/ID/artifact and real demonstrable gap becomes safely bounded before 2026-11-30:** preregister first, keep `EXPLORATORY_ONLY`/planning-only (no network fetch/probe/download unless separately preregistered & authorized, no outcomes/returns/spreads/states/p-values/costs/inference), do not touch frozen confirmatory artifacts or reuse inspected forward block as fresh evidence. Do not duplicate H29–H45 audits/seams or H40–H45. If no such gap exists, take no action beyond holding for the date gate.

**Known cleanup candidate (NOT authorized):** 70 byte-identical duplicate `H004V106_panel_coverage_extension_feasibility_*.json` artifacts remain committed under `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-FEAS-001/integrity_audit/` (preserve-all). Removal requires explicit authorization and must keep at least one artifact so `tests/test_panel_coverage_extension_feasibility.py::_committed_artifact` still resolves.

**Probe-evidence invariant:** if you write a probe or session verification record, refresh `probe_evidence` using canonical schema (`total_real_probes`, `probe_month_<month>{count,published}`, `newest_probe` as **basename only**). Do **not** use `by_month`/`published_by_month`.

## Durable-state rules

- Handoff top entry `## Session summary — <ts> (this session)` matching title timestamp; older entries `## Previous session — <ts>` unique and strictly descending; quote the newest `session_verifications/session_verify_*.json` on disk.
- Keep literal `probe_month=2026-11` present whenever `2026-11` appears, and never assert the H10 cutoff gate as blocked (tests enforce both).
- Do not alter frontier, registry (except allocating a new hypothesis if adding an experiment, plus explicit reconciliation notes), frozen 001/002/003 artifacts/configs/inputs, or sealed holdout.
- Recompute probe counts from disk (currently 397 real `cutoff_probe_*.json` in `research_state/cutoff_probe/`: 270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published; newest `cutoff_probe_20261113T091257Z.json`). Do not hard-code these numbers; recompute each session.
- If allocating a new hypothesis, bump `next_sequence_number` AND `tests/test_continuous_research_contract.py` in the same change (currently 45, H1..H45).
- Manifest session records via `python3 scripts/record_session_record.py <payload.json>`; do not add `session_id_drift_scan`; keep `session_id` == filename stem.

## Hard constraints

Free public data only; historical research only (no orders/live/paper trading); preserve DISPERSION-001/002 and frozen 003 artifacts/configs/inputs; no look-ahead/fabrication/forward-fill; today's rank != historical truth; complete multiple-testing correction for any claim; do not reuse inspected holdout as fresh confirmation.

## End-of-session requirement

Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID." Waiting for fixed calendar date 2026-11-30 is a date gate. A repeated verification-only session with no new evidence is a loop and must not be presented as progress.