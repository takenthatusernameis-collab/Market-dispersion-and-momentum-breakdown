# Agent Task Message — 2026-11-19T00:51:59Z (next session)

## Initial task for next agent

Today is 2026-11-19, which is **before** the hard date gate **2026-11-30**. Read the durable handoff (`research_state/agent_handoff.md`, newest `## Session summary — 2026-11-19T00:51:59Z`) and this message, then complete the standing task:

1. **Hold the confirmatory H10 track for the date gate.** Do not re-run completed hypotheses, do not re-probe `probe_month=2026-11` before the gate, and do not add another verification-only checkpoint. The H10 fresh sealed block is immature (`n_formations=1`, `n_high=0`, `n_low=0`, `n_mid=1`, `confirmatory_claim_allowed=false`) and cannot be matured before that date.
2. **No genuinely new bounded no-cost gap remains before the gate.** H51-a (extension-panel normalization plan) is complete and committed: registry H51, `scripts/panel_normalization_plan.py`, `tests/test_panel_normalization_plan.py` (12 tests), artifact `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-PLAN-001/integrity_audit/panel_normalization_plan_20261118T231800Z.json` (file sha256 `dc8e100682cf3eab147787973536dd0de1517c740e5075a7c3f3db43796b9768`), verdict `PLAN_RECORDED`, 9 extension assets, 810 planned panel files, `confirmatory_claim_allowed=false`, `exploratory_only=true`. H51-b (wave-B acquisition of the H50-trimmed 166 files) has only a preregistration stub (`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-WAVEB-001/preregistrations/PANELACQ_WAVEB_001_v1.md`); it is optional, not required for the confirmatory gate, and unstarted (no script, test, integrity audit, or registry entry). If — and only if — a genuinely NEW-ID bounded no-cost step appears before the gate, preregister it under the next ID (H52) as `EXPLORATORY_ONLY` per adaptive research-gate policy v1, keep it read-only/planning-only unless it is a real free-data acquisition, and do not present it as outcomes or evidence of an edge. If none appears, hold and leave the state clean.
3. **Do not re-do** H39–H51, the F1GRID/F1COV/F1SENS/F1STAB audits, the forward-block audits, or the cutoff probes. Do not re-download the H49 wave-A files or re-derive the H50 trim and present them as new evidence. A repeated verification-only session is a loop and is not progress.

## Verified state (2026-11-19T00:51:59Z, this session)

- **HEAD at write:** working tree clean; all H51-a artifacts and durable-state updates committed (registry H51, contract pin 51, manifest H51 entry and session record, claim snapshot refreshed, session verification recorded). No frozen artifact/config/input/frontier/sealed-holdout modified; DISPERSION-001/002 unchanged.
- **Full suite green:** **1236 tests, OK, skipped=8, EXIT=0** (`python3 -m unittest discover -s tests`), claim re-recorded **1236/1236/0** by `python3 scripts/record_test_claim.py` (snapshot `research_state/verified_test_claim_claim_snapshot.json`, input fingerprint prefix `7979622d1222b1aa...`, 197 input files). `python3 -m compileall -q scripts tests` EXIT 0.
- **H51-a (complete):** `HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-PLAN-001`, EXPLORATORY_ONLY/source_coverage_normalization_plan, `PLAN_RECORDED`; 9 extension assets (7 wave-A fully served, 2 wave-B trimmed), 810 planned panel files (644 wave-A + 166 wave-B), admissible months per asset exactly matching H47/H50 served windows, point-in-time formation alignment, no backfill, strict DISP-003 schema, per-file sha256 provenance (H49 wave-A; H51-b placeholder for wave-B). All input hashes (H47/H49/H50/H41) and all four frozen DISP-003 hashes verified match. No panel bytes, no outcomes, no network, no confirmatory claim; does not validate/replace/unlock H1/H6/H7/H10 or the confirmatory expanding-universe arm; H10 gate unchanged.
- **Canonical/h10_fresh/grid/frontier (byte-unchanged, verified this session):** canonical forward block sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f` (`block_sealed=true`, `n_formations=1`, `n_high=0`, `n_low=0`, `n_mid=1`, `confirmatory_claim_allowed=false`, `evaluated_utc=2026-11-02T15:18:56Z`); grid config `1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176`; frontier sha256 `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e` (`historical_rank_coverage_state=NOT_PROVEN_COMPLETE`, `last_updated_utc=2026-11-06T12:27:02Z`, `expanding_universe_target_met=true`, `rank_frontier_exhausted=false`).
- **Registry:** `research_state/hypothesis_registry.json` `next_sequence_number` 51 (H1..H51 present). H10 fresh sealed block immature and date-gated to **2026-11-30**.
- **Posture:** **BLOCKED_BY_HARD_DATE_GATE** for the confirmatory H10 track. Exploratory chain H40→H50 complete plus H51-a recorded; both acquisition waves adjudicated (wave A acquired+verified, wave B trimmed to 166 servable files), ALPHA excluded.
- **Probe evidence (disk):** 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published; newest `cutoff_probe_20261113T091257Z.json`); 398 probe files total including 1 `daily_fundingRate_probe_*.json` that is not part of the 397 cutoff-probe census. Date gate respected — no `probe_month=2026-11` re-probe.

## Option A — at/after 2026-11-30 (primary, date-gated)

1. `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If `target_published=true`, refresh free public data only: `python3 scripts/refresh_free_data.py --price-end 2026-11-30 --cap-end 2026-11-30` (adjust only if protocol/source cutoffs require).
2. `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests` to completion.
3. Verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged vs `git show HEAD:artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`.
4. Run the fresh sealed H10 block only into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--forward-block-start 2026-09-30 --data-cutoff <new cutoff>`. Require `n_high > 0 AND n_low > 0` before any confirmatory claim; preserve prior artifacts unchanged. Note H36/H35: the first mature look M1 needs >=32 in-block daily formations and is not reachable at the 2026-11-30 vintage.
5. If tests/scripts change with a recordable claim, run `python3 scripts/record_test_claim.py`; update handoff, this task message, and a new session verification record with exact commands/outcomes.

## Option B — only if a genuinely new bounded no-cost exploratory task with a NEW hypothesis/ID/artifact appears before 2026-11-30

Preregister first, keep `EXPLORATORY_ONLY`, and follow adaptive research-gate policy v1. **Already consumed:** H40 (feasibility), H41 (plan), H42 (rank-breadth repro), H43 (probe), H46 (reconciliation), H47 (roster), H48 (acquisition queue), H49 (wave-A acquisition), H50 (wave-B window trim), H51 (extension-panel normalization plan). Re-probing the known ALPHA funding tail 2025-10..2026-10 is not a distinct attempt per policy v1 §2 unless it targets a different admissible source or route. Do not fabricate files and do not present a workflow pass as economic evidence.

## Fresh-runner prerequisite

Bare runner may lack `numpy`/`pandas`. Run `python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt` before the suite (without it 34 test modules error and the suite reports far fewer tests). `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-002/grid_result_ledger.json` is intentionally gitignored; the four ledger-pinning tests in `tests/test_f1_grid_vintage_trim.py` skip on a clean checkout by design.

## Durable-state rules

- Handoff top entry `## Session summary — <ts> (this session)` matching title timestamp; older entries `## Previous session — <ts>` unique and strictly descending.
- Do not hard-code the probe census; always recompute it from disk.
- Recompute probe counts from disk rather than trusting these quotes: 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`; 398 probe files total include 1 distinct `daily_fundingRate_probe_*.json` that is not part of the 397 cutoff-probe census.
- Keep literal `probe_month=2026-11` present whenever `2026-11` appears.
- Do not alter frontier, existing registry entries, frozen artifacts/configs/inputs, or the sealed holdout. Registering a new hypothesis (append-only, `next_sequence_number` bump, `tests/test_continuous_research_contract.py` pin bump) is allowed only under Option B.

## Hard constraints

Free public data only; historical research only; preserve DISPERSION-001/002 and frozen 003 artifacts; no look-ahead/fabrication; today's rank != historical truth; no paid services, secrets or trading.

## End-of-session requirement

Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID." Waiting for fixed calendar date **2026-11-30** is a date gate.