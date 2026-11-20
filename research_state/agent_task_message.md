# Agent Task Message — 2026-11-20T11:07:02Z (next session)

## Initial task for next agent

Today is 2026-11-20, which is **before** the hard date gate **2026-11-30**. Read the durable handoff (`research_state/agent_handoff.md`, newest `## Session summary — 2026-11-20T11:07:02Z`) and this message, then complete the standing task:

1. **Hold the confirmatory H10 track for the date gate.** Do not re-run completed hypotheses, do not re-probe `probe_month=2026-11` before the gate, and do not add another verification-only checkpoint. The H10 fresh sealed block is immature (`n_formations=1`, `n_high=0`, `n_low=0`, `n_mid=1`, `confirmatory_claim_allowed=false`) and cannot be matured before that date.
2. **H54 is now complete** (`PANELQA-WAVEB-001`, `EXPLORATORY_ONLY`, verdict `PANELQA_WAVEB_COMPLETE`): the four H53 ARK/ASTR panels reconcile to their recorded sha256 with exact klines continuity (ARK 1,139/1,139 days, ASTR 1,356/1,356), no OHLC/duplicate/staleness issues, and funding cadence ARK `{1h:356, 4h:3639, 8h:1551}` / ASTR `{8h:4070}`. Do not re-run or re-present H54.
3. **H55 is now complete** (`DISP-003-BREADTH-ARITY-001`, `EXPLORATORY_ONLY`): breadth/arity and 2-asset identification diagnostic on the QA-clean wave-B panels and the committed legacy-28 klines; read-only, preserves all committed panels byte-identical, no frozen artifact/config/ledger/forward block/frontier modified. Do not re-run or re-present H55.
4. **H56 is complete** (`DISP-003-PANELNORM-WAVEA-001`, `EXPLORATORY_ONLY`, verdict `PANELNORM_WAVEA_COMPLETE`): the 644 H49-acquired wave-A monthly archives (ALICE, ANKR, APE, API3, APT, AR, ARPA; 2023-01..2026-10) normalized into 14 DISP-003-schema panels with byte-exact reproducibility, exact row accounting (44,646 rows in == 44,646 written), 0 bad digests/content failures/out-of-window/duplicate timestamps, descriptive concurrent-breadth coverage 35-41 assets/month across the committed DISP-003 inventory. Do not re-run or re-present H56.
5. **If — and only if — a genuinely NEW-ID bounded no-cost step appears before the gate, preregister it first as `EXPLORATORY_ONLY`** per adaptive research-gate policy v1. The one avenue still genuinely open is a bounded mechanism diagnostic on the now-QA-clean ARK/ASTR wave-B panels (new ID; must declare the narrower 2-asset/9-asset universe explicitly, use point-in-time months only, compute no confirmatory claim and not touch the frozen H10 track). It must not reuse the inspected canonical forward block as fresh confirmation. If no such step is justified, hold and leave the state clean.
6. **No durable-state change is required beyond refreshing this handoff/task-message pair** (this session made none). The verified-test-claim snapshot remains at `latest_verified_test_claim=1386/1386/0` with two expected failures (manifest narrative vs registry sequence number; test snapshot vs inventory drift). Do not allocate further hypotheses (registry allocation is Option B only).

## Verified state (2026-11-20T11:07:02Z, this session)

- **compileall + suite:** `python3 -m compileall -q scripts tests` EXIT 0; `python3 -m unittest discover -s tests` **1386 tests, 2 failures, skipped=8, EXIT=1** (the two failures are pre-existing drifts: `test_manifest_narrative_next_sequence_number_agrees_with_registry` — manifest narrative claims 55, registry holds 56; `test_snapshot_fingerprint_matches_inventory` — tests/test_continuous_research_contract.py content changed).
- **Durable-state writes this session:** `research_state/agent_handoff.md` (new session entry `2026-11-20T11:07:02Z`, old `2026-11-20T11:02:33Z` demoted to `Previous session`) and `research_state/agent_task_message.md` (this file). No frozen artifact, config, input, frontier, registry entry, or sealed holdout modified.
- **Probe evidence (disk):** 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published; newest `cutoff_probe_20261113T091257Z.json`); 399 probe files total (`*probe*.json`) including `daily_fundingRate_probe_20261101T132013Z.json` and `H004V106_panel_archive_probe_20261116T142247Z.json` outside the 397 cutoff-probe census. Date gate respected — no `probe_month=2026-11` re-probe. (Recompute from disk; do not trust this quote.)
- **Canonical/h10_fresh/grid/frontier (byte-unchanged):** canonical forward block sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f` (`block_sealed=true`, `n_formations=1`, `n_high=0`, `n_low=0`, `n_mid=1`, `confirmatory_claim_allowed=false`, `evaluated_utc=2026-11-02T15:18:56Z`); grid config (configs/dispersion_momentum_grid_v3.json) `1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176`; frontier (research_state/universe_frontier.json) sha256 `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e` (`historical_rank_coverage_state=NOT_PROVEN_COMPLETE`, `last_updated_utc=2026-11-06T12:27:02Z`, `expanding_universe_target_met=true`, `rank_frontier_exhausted=false`).
- **Registry:** `research_state/hypothesis_registry.json` `next_sequence_number` 56 (H1..H56 present; H56 `EXPLORATORY_ONLY` DISP-003-PANELNORM-WAVEA-001). H10 fresh sealed block immature and date-gated to **2026-11-30**.
- **Newest session verification record:** `research_state/session_verifications/session_verify_20261120T100238Z.json` on disk. No new verification-only checkpoint added this session.

## Option A — at/after 2026-11-30 (primary, date-gated)

1. `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If `target_published=true`, refresh free public data only: `python3 scripts/refresh_free_data.py --price-end 2026-11-30 --cap-end 2026-11-30` (adjust only if protocol/source cutoffs require).
2. `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests` to completion.
3. Verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged vs `git show HEAD:artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`.
4. Run the fresh sealed H10 block only into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--forward-block-start 2026-09-30 --data-cutoff <new cutoff>`. Require `n_high > 0 AND n_low > 0` before any confirmatory claim; preserve prior artifacts unchanged. Note H36/H35: the first mature look M1 needs >=32 in-block daily formations and is not reachable at the 2026-11-30 vintage.
5. If tests/scripts change with a recordable claim, run `python3 scripts/record_test_claim.py`; update handoff, this task message, and a new session verification record with exact commands/outcomes.

## Option B — only if a genuinely new bounded no-cost exploratory task with a NEW hypothesis/ID/artifact appears before 2026-11-30

Preregister first, keep `EXPLORATORY_ONLY`, and follow adaptive research-gate policy v1. **Already consumed:** H40 (feasibility), H41 (plan), H42 (rank-breadth repro), H43 (probe), H46 (reconciliation), H47 (roster), H48 (acquisition queue), H49 (wave-A acquisition), H50 (wave-B window trim), H51 (extension-panel normalization plan), H52 (wave-B acquisition), H53 (wave-B normalization), H54 (wave-B usability/coverage audit), H55 (breadth/arity diagnostic), H56 (wave-A normalization). Re-probing the known ALPHA funding tail 2025-10..2026-10 is not a distinct attempt per policy v1 §2 unless it targets a different admissible source or route. Do not fabricate files and do not present a workflow pass as economic evidence.

## Fresh-runner prerequisite

Bare runner may lack `numpy`/`pandas`. Run `python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt` before the suite (without it 34 test modules error and the suite reports far fewer tests). `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-002/grid_result_ledger.json` is intentionally gitignored; the four ledger-pinning tests in `tests/test_f1_grid_vintage_trim.py` skip on a clean checkout by design.

## Durable-state rules

- Handoff top entry `## Session summary — <ts> (this session)` matching title timestamp; older entries `## Previous session — <ts>` unique and strictly descending.
- Do not hard-code the probe census; always recompute it from disk.
- Recompute probe counts from disk rather than trusting these quotes: 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`; 399 probe files total include `daily_fundingRate_probe_20261101T132013Z.json` and `H004V106_panel_archive_probe_20261116T142247Z.json` outside the 397 cutoff-probe census.
- Keep literal `probe_month=2026-11` present whenever `2026-11` appears.
- Do not alter frontier, existing registry entries, frozen artifacts/configs/inputs, or the sealed holdout. Registering a new hypothesis (append-only, `next_sequence_number` bump, `tests/test_continuous_research_contract.py` pin bump) is allowed only under Option B.

## Hard constraints

Free public data only; historical research only; preserve DISPERSION-001/002 and frozen 003 artifacts; no look-ahead/fabrication; today's rank != historical truth; no paid services, secrets or trading.

## End-of-session requirement

Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID." Waiting for fixed calendar date **2026-11-30** is a date gate.
