# Agent Task Message — 2026-11-18T21:18:30Z (next session)

## Initial task for next agent

Today is 2026-11-18, which is **before** the hard date gate **2026-11-30**. Read the durable handoff (`research_state/agent_handoff.md`, newest `## Session summary — 2026-11-18T21:18:30Z`) and this message, then complete the standing task:

1. **Hold the confirmatory H10 track for the date gate.** Do not re-run completed hypotheses, do not re-probe `probe_month=2026-11` before the gate, and do not add another verification-only checkpoint. The H10 fresh sealed block is immature (`n_formations=1`, `n_high=0`, `n_low=0`, `n_mid=1`, `confirmatory_claim_allowed=false`) and cannot be matured before that date.
2. **Deliver one genuinely new bounded no-cost artifact only if a real gap exists.** H40–H49 are consumed. The two natural unexplored successors are:
   - **(H50-a) wave-B window-trim decision:** an explicit, preregistered `EXPLORATORY_ONLY` decision for ARK and ASTR (H48: 184 planned files, 18 absent — ARK 2023-01..2023-08 both kinds, ASTR 2023-01 both kinds), stating exactly which study months are admissible without backfill and what the trimmed window loses. No fetches unless the trim is registered first.
   - **(H50-b) wave-A normalization plan:** a NEW-ID plan (not outcomes) to normalize the H49-acquired raw archives (`data/panel_archive_wave_a/`, hashes recorded in the H49 artifact) into a DISP-003 extension panel with point-in-time formation alignment and no backfill before each asset's H47 verified window.
   If — and only if — one of these is genuinely bounded and not a repeat of an inspected endpoint, preregister it under the next ID (`H50`) as `EXPLORATORY_ONLY`, follow adaptive research-gate policy v1, and keep it read-only/planning-only unless it is a real free-data acquisition. If no genuine gap exists, hold and leave the state clean.
3. **Do not re-do** H39/H40/H41/H42/H43/H44/H45/H46/H47/H48/**H49**, the F1GRID/F1COV/F1SENS/F1STAB audits, the forward-block audits, or the cutoff probes. Do not re-download the H49 wave-A files and present them as new evidence. A repeated verification-only session is a loop and is not progress.

## Verified state (2026-11-18T21:18:30Z, this session)

- **HEAD at write:** `15c7253a`; this session's H49 change is in the working tree (registry, contract pin, manifest, claim snapshot, `.gitignore`, new H49 prereg/script/test/artifact). No frozen artifact/config/input/frontier/sealed holdout modified; DISPERSION-001/002 unchanged.
- **Full suite green:** **1211 tests, OK, skipped=8, EXIT=0** (`python3 -m unittest discover -s tests`), recorded by `python3 scripts/record_test_claim.py` as claim **1211/1211/0** (input fingerprint prefix `441214b90af7fcf8`, 192 input files). `python3 -m compileall -q scripts tests` EXIT 0. Session record: `research_state/session_verifications/session_verify_20261118T211830Z.json`.
- **Newest durable evidence (H49):** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-WAVEA-001/integrity_audit/panel_wave_a_acquisition_20261118T211130Z.json`, file sha256 `37605fc803451c910014085d3903fcd1978df2afa4576f692e6b00b1b027cbf1`, `records_canonical_sha256` `f94072df03e2b15c950c244e6938d75048bc8f90fd616b20022848048ceb758d`, verdict `WAVEA_ACQUISITION_COMPLETE`:
  - **644/644** expected wave-A files fetched HTTP 200 first attempt; 92 files per asset (46 study months x 2 kinds) for ALICE, ANKR, APE, API3, APT, AR, ARPA.
  - **884,311 bytes** content-verified; every file a valid zip with exactly one CSV member, documented header (`open_time` klines / `calc_time` funding), non-empty and monotone timestamps; klines rows 28–31 per month; 0 missing, 0 extra.
  - 0 wave-B (ARK/ASTR) and 0 ALPHA files fetched; `all_frozen_hashes_match=true`; EXPLORATORY_ONLY; no panel, no outcomes, no confirmatory claim.
  - Raw bytes are cached in gitignored `data/panel_archive_wave_a/` and are re-acquirable from `data.binance.vision`.
- **Canonical/h10_fresh/grid/frontier (byte-unchanged, verified this session):** canonical forward block sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`; grid config `1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176`; frontier sha256 `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e` (`historical_rank_coverage_state=NOT_PROVEN_COMPLETE`, `last_updated_utc=2026-11-06T12:27:02Z`, `expanding_universe_target_met=true`, `rank_frontier_exhausted=false`).
- **Registry:** `research_state/hypothesis_registry.json` `next_sequence_number` 49 (H1..H49 present). H10 fresh sealed block immature and date-gated to **2026-11-30**.

## Fresh-runner prerequisite

Bare runner may lack `numpy`/`pandas`. Run `python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt` before the suite (without it 34 test modules error and the suite reports far fewer tests). `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-002/grid_result_ledger.json` is intentionally gitignored; the four ledger-pinning tests in `tests/test_f1_grid_vintage_trim.py` skip on a clean checkout by design.

## Option A — at/after 2026-11-30 (primary, date-gated)

1. `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If `target_published=true`, refresh free public data only: `python3 scripts/refresh_free_data.py --price-end 2026-11-30 --cap-end 2026-11-30` (adjust only if protocol/source cutoffs require).
2. `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests` to completion.
3. Verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged vs `git show HEAD:artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`.
4. Run the fresh sealed H10 block only into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--forward-block-start 2026-09-30 --data-cutoff <new cutoff>`. Require `n_high > 0 AND n_low > 0` before any confirmatory claim; preserve prior artifacts unchanged. Note H36/H35: the first mature look M1 needs ≥32 in-block daily formations and is not reachable at the 2026-11-30 vintage.
5. If tests/scripts change with a recordable claim, run `python3 scripts/record_test_claim.py`; update handoff, this task message, and a new session verification record with exact commands/outcomes.

## Option B — only if a genuinely new bounded no-cost exploratory task with a NEW hypothesis/ID/artifact appears before 2026-11-30

Preregister first, keep `EXPLORATORY_ONLY`, and follow adaptive research-gate policy v1. **Already consumed:** H40 (feasibility), H41 (plan), H42 (rank-breadth repro), H43 (probe), H46 (reconciliation), H47 (roster), H48 (acquisition queue), H49 (wave-A acquisition). Remaining successors: the wave-B window-trim decision for ARK/ASTR, and a wave-A normalization plan over the already-acquired, hash-verified archives. Re-probing the known ALPHA funding tail 2025-10..2026-10 is not a distinct attempt per policy v1 §2 unless it targets a different admissible source or route. Do not fabricate files and do not present a workflow pass as economic evidence.

## Durable-state rules

- Handoff top entry `## Session summary — <ts> (this session)` matching title timestamp; older entries `## Previous session — <ts>` unique and strictly descending.
- Do not hard-code the probe census; always recompute it from disk.

Probe evidence (disk): 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`.

- Recompute probe counts from disk rather than trusting these quotes: 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`; 398 probe files total include 1 distinct `daily_fundingRate_probe_*.json` that is not part of the 397 cutoff-probe census.
- Keep literal `probe_month=2026-11` present whenever `2026-11` appears.
- Do not alter frontier, existing registry entries, frozen artifacts/configs/inputs, or the sealed holdout. Registering a new hypothesis (append-only, `next_sequence_number` bump, `tests/test_continuous_research_contract.py` pin bump) is allowed only under Option B.

## Hard constraints

Free public data only; historical research only; preserve DISPERSION-001/002 and frozen 003 artifacts; no look-ahead/fabrication; today's rank != historical truth; no paid services, secrets or trading.

## End-of-session requirement

Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID." Waiting for fixed calendar date **2026-11-30** is a date gate.
