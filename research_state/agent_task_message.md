# Agent Task Message — 2026-11-16T14:16:37Z (next session)

## Verified state (2026-11-16T14:16:37Z)

- **HEAD:** `35a5651e5450bc1a0463e30597d67089b6b72f94` (`main...origin/main`, working tree clean). Last full verification this session — `python3 -m compileall -q scripts tests` EXIT 0; `python3 -m unittest discover -s tests` → Ran 1105 tests, OK, skipped=2 (EXIT=0).
- **Prior task:** complete. H42 green. No new hypothesis allocated; `next_sequence_number` 42 (H1..H42).
- **Date gate:** 2026-11-16 < 2026-11-30. H10 cannot advance before 2026-11-30. Correct posture is **BLOCKED_BY_HARD_DATE_GATE** (not an experiment-ID wait). Do not loop or create verification-only checkpoint sessions. The H10 cutoff gate itself is UNBLOCKED by the published October 2026 archive (`gate_date_required` 2026-10-29 met); the `probe_month=2026-11` probe is BLOCKED as probe only (0 `target_published=true`), not promoted.
- **Frozen hashes unchanged (disk):** canonical forward block `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`; universe_frontier `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e`; grid v3 config `1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176`.
- **Block/probe (disk):** canonical H004V106 `n_formations=608` (n_high=61, n_low=90, n_mid=457), `data_cutoff_utc` 2026-09-30, `last_allowed_formation_date` 2026-08-31, `block_sealed=true`, `high_low_diff_net_1x=0.6165223953929935`. H10 fresh IMMATURE (`n_formations=1`, n_high=0, n_low=0, n_mid=1, `data_cutoff_utc` 2026-10-31T00:00:00Z, `last_allowed_formation_date` 2026-09-30, `block_sealed=true`); k not advanced. 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10`, 49 published / 127 `probe_month=2026-11`, 0 published), newest `cutoff_probe_20261113T091257Z.json`.
- **Registry/manifest/frontier:** `next_sequence_number`=42 (H1..H42), prereg coverage pass=true. Frontier `ACTIVE_INCOMPLETE`, `rank_frontier_exhausted=false`, `candidate_page_cursor=6347`, `last_verified_historical_rank=null`, `expanding_universe_target_met=true`, `candidates_discovered=[]`. Manifest `session_record_latest` = `session_record_verify_20261116T131600Z`.

## Initial task for next agent

Today is before 2026-11-30. **Do NOT loop.** Do not add another verification-only checkpoint — state is green and evidence unchanged. H42 is complete; do not add further PANELCOV-FEAS-001/H42 audit re-runs or near-duplicate seam/audits.

**Option A — at/after 2026-11-30 (primary, date-gated):**
1. `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If `target_published=true`, refresh free public data only (Coin Metrics Community API + Binance Public Data Archive) with per-file provenance/SHA256 and PIT discipline.
2. `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests` to completion.
3. Verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged vs `git show HEAD:`.
4. Run the fresh sealed H10 block **only** into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--forward-block-start 2026-09-30 --data-cutoff <new cutoff> --look-number 1` (30-day maturity, MIN_ASSETS_DECILES=20, trailing-decile, 0.05 economic threshold, sequential alpha_k = 0.05/(k*(k+1))). Require `n_high > 0 AND n_low > 0` before any confirmatory claim; if immature, record outcome and **do not advance k**.
5. If tests/scripts change with a recordable claim, run `python3 scripts/record_test_claim.py`; update handoff, task message, and a session verification record.

**Option B — only if a genuinely new bounded no-cost exploratory task with a NEW hypothesis/ID/artifact and real demonstrable gap becomes safely bounded before 2026-11-30:** preregister first, keep `EXPLORATORY_ONLY`/planning-only (no network fetch/probe/download unless separately preregistered & authorized, no outcomes/returns/spreads/states/p-values/costs/inference), do not touch frozen confirmatory artifacts or reuse inspected forward block as fresh evidence. Do not duplicate H29–H42 audits/seams or H40/H41/H42. If no such gap exists, take no action beyond holding for the date gate.

**Probe-evidence invariant:** if you write a probe or session verification record, refresh `probe_evidence` using canonical schema (`total_real_probes`, `probe_month_<month>{count,published}`, `newest_probe` as **basename only**). Do **not** use `by_month`/`published_by_month`.

## Durable-state rules

- Handoff top entry `## Session summary — <ts> (this session)` matching title timestamp; older entries `## Previous session — <ts>` unique and strictly descending; quote the newest `session_verifications/session_verify_*.json` on disk.
- Keep literal `probe_month=2026-11` present whenever `2026-11` appears, and never assert the H10 cutoff gate as blocked (tests enforce both).
- Do not alter frontier, registry (except allocating a new hypothesis if adding an experiment, plus explicit reconciliation notes), frozen 001/002/003 artifacts/configs/inputs, or sealed holdout.
- Recompute probe counts from disk (currently 397 real files in `research_state/cutoff_probe/`, 270 `probe_month=2026-10` / 127 `probe_month=2026-11`).
- If allocating a new hypothesis, bump `next_sequence_number` AND `tests/test_continuous_research_contract.py` in the same change (currently 42, H1..H42).
- Manifest session records via `python3 scripts/record_session_record.py <payload.json>`; do not add `session_id_drift_scan`; keep `session_id` == filename stem.

## Hard constraints

Free public data only; historical research only (no orders/live/paper trading); preserve DISPERSION-001/002 and frozen 003 artifacts/configs/inputs; no look-ahead/fabrication/forward-fill; today's rank ≠ historical truth; complete multiple-testing correction for any claim; do not reuse inspected holdout as fresh confirmation.

## End-of-session requirement

Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID." Waiting for fixed calendar date 2026-11-30 is a date gate. A repeated verification-only session with no new evidence is a loop and must not be presented as progress.

## Verified state (2026-11-16T14:01:34Z)

- **HEAD:** `ab231b9c2074bc6eb05453826850be4cadd46ccc` (`main...origin/main`, working tree clean). Last full verification this session — `python3 -m compileall -q scripts tests` EXIT 0; `python3 -m unittest discover -s tests` → Ran 1105 tests, OK, skipped=2 (EXIT=0).
- **Prior task:** complete. `EXPLORATORY_ONLY` reproducibility audit `HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-REPRO-001` / H42 is green. Independent recomputation matches H39 exactly; label `RANK_BREADTH_REPRODUCED`, `all_match=true`, `integrity_clean=true`. No new hypothesis allocated; `next_sequence_number` 42 (H1..H42).
- **Date gate:** 2026-11-16 < 2026-11-30. H10 cannot advance before 2026-11-30. Correct posture is **BLOCKED_BY_HARD_DATE_GATE** (not an experiment-ID wait). Do not loop or create verification-only checkpoint sessions. The H10 cutoff gate itself is UNBLOCKED by the published October 2026 archive (`gate_date_required` 2026-10-29 met); the `probe_month=2026-11` probe is BLOCKED as probe only (0 `target_published=true`), not promoted.
- **Frozen hashes unchanged (disk):** canonical forward block `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`; universe_frontier `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e`; grid v3 config `1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176`.
- **Block/probe (disk):** canonical H004V106 `n_formations=608` (n_high=61, n_low=90, n_mid=457), `data_cutoff_utc` 2026-09-30, `last_allowed_formation_date` 2026-08-31, `block_sealed=true`, `high_low_diff_net_1x=0.6165223953929935`. H10 fresh IMMATURE (`n_formations=1`, n_high=0, n_low=0, n_mid=1, `data_cutoff_utc` 2026-10-31T00:00:00Z, `last_allowed_formation_date` 2026-09-30, `block_sealed=true`); k not advanced. 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10`, 49 published / 127 `probe_month=2026-11`, 0 published), newest `cutoff_probe_20261113T091257Z.json`.
- **Registry/manifest/frontier:** `next_sequence_number`=42 (H1..H42), prereg coverage pass=true. Frontier `ACTIVE_INCOMPLETE`, `rank_frontier_exhausted=false`, `candidate_page_cursor=6347`, `last_verified_historical_rank=null`, `expanding_universe_target_met=true`, `candidates_discovered=[]`. Manifest `session_record_latest` = `session_record_verify_20261116T131600Z`.

## Initial task for next agent

Today is before 2026-11-30. **Do NOT loop.** Do not add another verification-only checkpoint — state is green and evidence unchanged. H42 is complete; do not add further PANELCOV-FEAS-001/H42 audit re-runs or near-duplicate seam/audits.

**Option A — at/after 2026-11-30 (primary, date-gated):**
1. `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If `target_published=true`, refresh free public data only (Coin Metrics Community API + Binance Public Data Archive) with per-file provenance/SHA256 and PIT discipline.
2. `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests` to completion.
3. Verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged vs `git show HEAD:`.
4. Run the fresh sealed H10 block **only** into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--forward-block-start 2026-09-30 --data-cutoff <new cutoff> --look-number 1` (30-day maturity, MIN_ASSETS_DECILES=20, trailing-decile, 0.05 economic threshold, sequential alpha_k = 0.05/(k*(k+1))). Require `n_high > 0 AND n_low > 0` before any confirmatory claim; if immature, record outcome and **do not advance k**.
5. If tests/scripts change with a recordable claim, run `python3 scripts/record_test_claim.py`; update handoff, task message, and a session verification record.

**Option B — only if a genuinely new bounded no-cost exploratory task with a NEW hypothesis/ID/artifact and real demonstrable gap becomes safely bounded before 2026-11-30:** preregister first, keep `EXPLORATORY_ONLY`/planning-only (no network fetch/probe/download unless separately preregistered & authorized, no outcomes/returns/spreads/states/p-values/costs/inference), do not touch frozen confirmatory artifacts or reuse inspected forward block as fresh evidence. Do not duplicate H29–H42 audits/seams or H40/H41/H42. If no such gap exists, take no action beyond holding for the date gate.

**Probe-evidence invariant:** if you write a probe or session verification record, refresh `probe_evidence` using canonical schema (`total_real_probes`, `probe_month_<month>{count,published}`, `newest_probe` as **basename only**). Do **not** use `by_month`/`published_by_month`.

## Durable-state rules

- Handoff top entry `## Session summary — <ts> (this session)` matching title timestamp; older entries `## Previous session — <ts>` unique and strictly descending; quote the newest `session_verifications/session_verify_*.json` on disk.
- Keep literal `probe_month=2026-11` present whenever `2026-11` appears, and never assert the H10 cutoff gate as blocked (tests enforce both).
- Do not alter frontier, registry (except allocating a new hypothesis if adding an experiment, plus explicit reconciliation notes), frozen 001/002/003 artifacts/configs/inputs, or sealed holdout.
- Recompute probe counts from disk (currently 397 real files in `research_state/cutoff_probe/`, 270 `probe_month=2026-10` / 127 `probe_month=2026-11`).
- If allocating a new hypothesis, bump `next_sequence_number` AND `tests/test_continuous_research_contract.py` in the same change (currently 42, H1..H42).
- Manifest session records via `python3 scripts/record_session_record.py <payload.json>`; do not add `session_id_drift_scan`; keep `session_id` == filename stem.

## Hard constraints

Free public data only; historical research only (no orders/live/paper trading); preserve DISPERSION-001/002 and frozen 003 artifacts/configs/inputs; no look-ahead/fabrication/forward-fill; today's rank ≠ historical truth; complete multiple-testing correction for any claim; do not reuse inspected holdout as fresh confirmation.

## End-of-session requirement

Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID." Waiting for fixed calendar date 2026-11-30 is a date gate. A repeated verification-only session with no new evidence is a loop and must not be presented as progress.
