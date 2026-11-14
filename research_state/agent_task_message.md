# Agent Task Message — 2026-11-14T09:00:32Z (next session)

## Verified state (2026-11-14T09:00:32Z)

- **HEAD / remote:** local `main` = `f5696814a1b2c3d4e5f678901234567890abcdef` (3 commits ahead of `origin/main` `27cd8effbff5e71a7c5e018f23e918d8d2901f86`). Tracked tree clean except for modified `run_manifest.json` and `verified_test_claim_claim_snapshot.json` (timestamp updates from prior session), and two untracked oversized F1GRID-002 artifacts (`grid_result_ledger.json` ~166 MB, `grid_checkpoints/cell_checkpoint_armB_f1_repaired_ledger_vintage.json` ~66 MB) which must not be committed. Remote-tracking SHA not yet reconciled — controller will retry persistence after this session. Do not claim persistence until remote SHA matches.
- **Same-run recovery (session 21) verified:** session start had local HEAD `f5696814` (3 ahead of `origin/main`) with oversized artifacts untracked. No new commits created. Full test suite completed: `python3 -m unittest discover -s tests` — Ran 461 tests, OK, skipped=2. `python3 scripts/record_test_claim.py` refreshed snapshot: claim `461/461/0`, 119 input files, fingerprint `99dd1e12f38ad16157c3db48619d253d98f173e66b74af8bf4c401b1bd31b73b`. Verified evidence: `research_state/session_verifications/session_verify_20261114T090032Z.json` (latest).
- **F1GRID-002 (H27) complete:** registry `next_sequence_number` 27 (H1..H27 present). Do **not** re-run `scripts/run_f1_grid_vintage_trim.py` or re-execute F1GRID-002.
- **Checks:** `python3 -m compileall -q scripts tests` EXIT 0. Full suite passed. Latest verified claim snapshot: `461/461/0` (recorded 2026-11-14T08:58:49Z, fingerprint `99dd1e12f38ad16157c3db48619d253d98f173e66b74af8bf4c401b1bd31b73b`, 119 input files).
- **Frozen hashes unchanged:** canonical forward block `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`; F1GRID-002 grid summary `b5f5f336b24d9ba6b49d9eacb1c000b51e7935ed27e87322dd7b2c3bbe09b5b6`; frontier `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e`; grid v3 config `1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176`.
- **H10 gate vs probe:** H10 cutoff gate UNBLOCKED by the published October 2026 archive (`gate_date_required` 2026-10-29 met). `probe_month=2026-11` probe is BLOCKED as a probe only (0/127 `target_published=true`); not promoted into the H10 gate decision. Probe evidence recomputed from disk: 397 real (0 MOCK), 270 `probe_month=2026-10` (49 published) / 127 `probe_month=2026-11` (0 published), newest `cutoff_probe_20261113T091257Z.json`. H10 fresh block IMMATURE (`n_formations=1`, `n_high=0`, `n_low=0`, `last_allowed_formation_date` 2026-09-30, `data_cutoff_utc` 2026-10-31T00:00:00Z, `block_sealed=true`); k not advanced. No bounded no-cost H10 task unblocked before 2026-11-30 (**BLOCKED_BY_HARD_DATE_GATE**, not an experiment-ID wait).

## Initial task for next agent

Today is 2026-11-14, before the 2026-11-30 date gate. H10 cannot advance before 2026-11-30, and F1GRID-002 (the recorded candidate) is complete. Do **not** merely repeat the date-gate re-verification without new evidence — prior sessions have done that many times; that is a loop, not progress. Do **not** re-run `scripts/run_f1_grid_vintage_trim.py` expecting a different answer — it is finished.

**Default action (if no new task is identifiable):** run `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests` to completion and record the result (if you add/remove/edit `.py`, run `python3 scripts/record_test_claim.py`); recompute probe counts from `research_state/cutoff_probe/`; confirm frozen hashes unchanged (canonical `7234fc4e…`, h10_fresh `324ab1e6…`, frontier `9ba08f3f…`); record "no bounded no-cost H10 task unblocked before 2026-11-30" with verified evidence in the handoff, this task message, and a new session verification record. Do **not** re-probe `probe_month=2026-11` before 2026-11-30.

**Alternative:** pick **ONE** bounded, no-cost, genuinely new task from the categories in `AGENTS.md` (tests, source-coverage improvement, evidence audit, candidate evaluation, red-team, design), preregister it before computing outcomes when required, and deliver the verifiable artifact/test. Demonstrate a real gap first. Do not add a duplicate of an existing audit/guard. Do not touch frozen DISPERSION-003 artifacts/configs/inputs, the sealed holdout, or frontier/registry fields (except allocating a new hypothesis only if you genuinely add an experiment and you update `tests/test_continuous_research_contract.py` in the same change, bumping `next_sequence_number` 27 -> 28).

**Recovery/persistence note:** oversized F1GRID-002 artifacts remain untracked locally (`grid_result_ledger.json` ~166 MB, `grid_checkpoints/cell_checkpoint_armB_f1_repaired_ledger_vintage.json` ~66 MB) and must **not** be committed — adding them will recreate the push-blocking pre-receive failure. Recovery refs `recovery/pre-session20-20261114T0825Z` / tag `recovery-session20-20261114T0825Z` and bundle `/home/runner/work/_temp/kilo-tmp/kilo/recovery_pre_session20_20261114T0825Z.bundle` preserve the dropped oversized commit `a5b03c15`. Prior recovery refs/bundles remain intact. Controller will retry persistence of local-ahead commits; do not claim persistence until remote SHA matches.

If you add or remove a `.py` file under `tests/` or `scripts/`, run `python3 scripts/record_test_claim.py` in the same change. Also re-run it after editing any existing `.py` file — the fingerprint is content-sensitive. Non-`test*.py` scratch files under `tests/` are excluded from the fingerprint by design.

## On/after 2026-11-30 — H10 fresh sealed forward block (date-gated)

1. Run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`.
2. If `target_published=true`: refresh free public data only (Coin Metrics Community API + Binance Public Data Archive); install requirements if needed; run `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests`; verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged; run fresh sealed H10 block **only** into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--forward-block-start 2026-09-30 --data-cutoff <new cutoff> --look-number 1` (30-day maturity, `MIN_ASSETS_DECILES=20`, trailing-decile, 0.05 economic threshold, sequential `alpha_k = 0.05/(k*(k+1))`).
3. Require `n_high > 0 AND n_low > 0` before any confirmatory claim. If immature, record outcome and **do not advance k**.
4. If tests/scripts change with a recordable claim, run `python3 scripts/record_test_claim.py` as appropriate; update handoff, task message, and a session verification record.
5. **Probe-evidence invariant:** if the session writes a probe, refresh `probe_evidence` in its session record using canonical schema (`total_real_probes`, `probe_month_<month>` with `count`/`published`, `newest_probe`).

## Durable-state rules

- **Handoff shape:** top entry must be `## Session summary — <ts> (this session)` matching the title timestamp; every older entry `## Previous session — <ts>` with unique timestamps in strictly descending order; quote the newest `session_verifications/session_verify_*.json` on disk. A heading suffix such as `(this session continued)` hides a duplicate entry from `tests/test_handoff_session_entries.py` — never use one.
- Keep the literal `probe_month=2026-11` label present whenever `2026-11` appears, and never assert the H10 cutoff gate as blocked; `tests/test_h10_gate_vs_november_probe.py` enforces both.
- Do not alter frontier, registry (except allocating a new hypothesis if adding an experiment, plus explicit `registry_reconciliation_<ts>` notes), frozen 003 artifacts/configs/inputs, or sealed holdout. `latest_november_2026_probe` pointer lag is guard-permitted.
- Recompute probe counts from disk (currently 397 real cutoff_probe files, 270 `probe_month=2026-10` / 127 `probe_month=2026-11`).
- If you allocate a new hypothesis, bump `next_sequence_number` AND `tests/test_continuous_research_contract.py` in the same change (currently 27, H1..H27).
- `tests/test_state_consistency.py::test_latest_session_probe_evidence_matches_disk` pins the newest session record's `probe_evidence` to disk; `test_session_verify_records_carry_consistent_session_id` requires `session_id` == filename stem.

## Hard constraints

Free public data only; historical research only (no orders/live/paper trading); preserve DISPERSION-001/002 and frozen 003 artifacts/configs/inputs; no look-ahead/fabrication/forward-fill; today's rank ≠ historical truth; complete multiple-testing correction for any claim; do not reuse inspected holdout as fresh confirmation.

## End-of-session requirement

Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID." Waiting for fixed calendar date 2026-11-30 is a date gate.