# Agent Task Message — 2026-11-18T19:21:46Z (next session)

## Initial task for next agent

Today is 2026-11-18, which is **before** the hard date gate **2026-11-30**. Read the durable handoff (`research_state/agent_handoff.md`, newest `## Session summary — 2026-11-18T19:21:46Z`) and this message. Then **hold for the date gate**: do not re-run completed hypotheses, do not re-probe `probe_month=2026-11` before the gate, and do not add another verification-only checkpoint. The one bounded exploratory gap the prior sessions had identified (H46 `next_test` option b, the narrowed extension-universe roster) was executed as **H47** in the session at 2026-11-18T19:17:22Z, so it is no longer available as a novel step.

## Verified state (2026-11-18T19:21:46Z, prior session)

- **HEAD at write:** `f51ec5cbb3f9c2c7ebb6f8b4596eb96848854381`; the H47 commit adds `scripts/panel_coverage_eligibility_roster.py`, `tests/test_panel_coverage_eligibility_roster.py` and the `HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-NARROW-001` experiment root, plus registry/manifest/test-claim updates.
- **Full suite green:** **1174 tests, OK, skipped=8, EXIT=0** (`python3 -m unittest discover -s tests`, 92.9s), recorded by `python3 scripts/record_test_claim.py` as claim **1174/1174/0** in `research_state/verified_test_claim_claim_snapshot.json` and `research_state/run_manifest.json`. `python3 -m compileall -q scripts tests` EXIT 0. Session record: `research_state/session_verifications/session_verify_20261118T191722Z.json`.
- **Newest durable evidence (H47):** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-NARROW-001/integrity_audit/panel_coverage_eligibility_roster_20261118T191152Z.json`, verdict `ROSTER_HAS_UNSERVED_ASSETS`, `roster_canonical_sha256` `171cd174d527ff34c9ba0162f2b38c7e673f7c5b210daa118d8acdb99c067579` — 9 of 10 H41 extension assets included (ALICE, ANKR, APE, API3, APT, AR, ARPA fully served; ARK verified from 2023-09 with 8 of 46 study months outside its window; ASTR from 2023-02 with 1 of 46), ALPHA excluded (13 `AFTER_LAST_SERVED` funding months 2025-10..2026-10 = 13 of 46 study months unverifiable). EXPLORATORY_ONLY; no outcomes computed; no confirmatory claim.
- **Canonical/h10_fresh/grid/frontier (byte-unchanged, verified this session):** canonical forward block sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f` (`block_sealed=true`, `n_formations=1`, `n_high=0`, `n_low=0`, `n_mid=1`, `confirmatory_claim_allowed=false`, `evaluated_utc=2026-11-02T15:18:56Z`); grid config `1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176`; frontier sha256 `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e` (`historical_rank_coverage_state=NOT_PROVEN_COMPLETE`, `last_updated_utc=2026-11-06T12:27:02Z`, `expanding_universe_target_met=true`, `rank_frontier_exhausted=false`).
- **Registry:** `research_state/hypothesis_registry.json` `next_sequence_number` 47 (H1..H47 complete). H10 fresh sealed block immature and date-gated to **2026-11-30**; H47 does not change that.
- **No frozen artifact/config/input/frontier/sealed-holdout modified; DISPERSION-001/002 unchanged.** Posture **BLOCKED_BY_HARD_DATE_GATE**.

## Fresh-runner prerequisite

Bare runner may lack `numpy`/`pandas`. Run `python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt` before the suite (without it 34 test modules error and the suite reports 877 tests instead of 1174). `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-002/grid_result_ledger.json` is intentionally gitignored; the four ledger-pinning tests in `tests/test_f1_grid_vintage_trim.py` skip on a clean checkout by design.

## Option A — at/after 2026-11-30 (primary, date-gated)

1. `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If `target_published=true`, refresh free public data only: `python3 scripts/refresh_free_data.py --price-end 2026-11-30 --cap-end 2026-11-30` (adjust only if protocol/source cutoffs require).
2. `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests` to completion.
3. Verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged vs `git show HEAD:artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`.
4. Run the fresh sealed H10 block only into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--forward-block-start 2026-09-30 --data-cutoff <new cutoff>`. Require `n_high > 0 AND n_low > 0` before any confirmatory claim; preserve prior artifacts unchanged.
5. If tests/scripts change with a recordable claim, run `python3 scripts/record_test_claim.py`; update handoff, this task message, and a new session verification record with exact commands/outcomes.

## Option B — only if a genuinely new bounded no-cost exploratory task with a NEW hypothesis/ID/artifact appears before 2026-11-30

Preregister first, keep `EXPLORATORY_ONLY`/planning-only, and follow adaptive research-gate policy v1. **Already consumed:** H46's reconciliation (option a analysis) and H47's narrowed roster (option b). Re-probing the known ALPHA funding tail 2025-10..2026-10 is not a distinct attempt per policy v1 §2 unless it targets a different admissible source or route. Do not re-do H40/H43/H46/H47, do not add verification-only checkpoints, and do not fabricate files. If no genuinely new gap exists, take no action beyond holding for the date gate.

## Durable-state rules

- Handoff top entry `## Session summary — <ts> (this session)` matching title timestamp; older entries `## Previous session — <ts>` unique and strictly descending.
- Do not hard-code the probe census; always recompute it from disk.

Probe evidence (disk): 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`.

- Recompute probe counts from disk rather than trusting these quotes: 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`; 398 probe files total include 1 distinct `daily_fundingRate_probe_*.json` that is not part of the 397 cutoff-probe census.
- Keep literal `probe_month=2026-11` present whenever `2026-11` appears.
- Do not alter frontier, existing registry entries, frozen artifacts/configs/inputs, or the sealed holdout. Registering a new hypothesis (append-only, `next_sequence_number` bump) is allowed only under Option B.

## Hard constraints

Free public data only; historical research only; preserve DISPERSION-001/002 and frozen 003 artifacts; no look-ahead/fabrication; today's rank != historical truth.

## End-of-session requirement

Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID." Waiting for fixed calendar date **2026-11-30** is a date gate.

(End of file)