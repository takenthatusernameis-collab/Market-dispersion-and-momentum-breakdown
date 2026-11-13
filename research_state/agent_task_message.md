# Agent Task Message — 2026-11-13T09:55:04Z (next session)

## Verified state (2026-11-13T09:55:04Z)
- **HEAD:** `b4c76d9a0b6ba39ef1c9b67364c961227fa99fc9` (`main`), working tree clean at verification start (only this record/handoff/task-message/root-HANDOFF writes pending).
- **Prior task complete:** read the durable handoff and task message from 2026-11-13T09:47:46Z. The H10 fresh sealed forward block is date-gated until 2026-11-30 and not runnable today (2026-11-13). No bounded no-cost H10 task is unblocked before the gate.
- **Completed this session:** re-verified prior-session state unchanged; state clean. Recorded "no bounded no-cost H10 task unblocked before 2026-11-30" with verified evidence in this task message, the durable handoff, and session verification record `research_state/session_verifications/session_verify_20261113T095504Z.json`. Recomputed probe evidence independently from disk: **397 real `cutoff_probe_*.json` files (0 MOCK): 270 `probe_month=2026-10` (49 published / 221 not) and 127 `probe_month=2026-11` (all `target_published=false`)**; newest `cutoff_probe_20261113T091257Z.json` (`2026-11-13T09:12:57Z`). H10 cutoff gate **UNBLOCKED** by the published October 2026 archive; `probe_month=2026-11` probe **BLOCKED as a probe only**; the probe BLOCKED verdict is never promoted into the H10 gate decision.
- **Environment:** numpy 2.5.4 and pandas 3.1.1 importable (installed by prior session, free/local). Without them the suite errors with 9 `ModuleNotFoundError` + 1 requirements-import failure — an environment condition, not a repo defect.
- **Checks:** `python3 -m compileall -q scripts tests` EXIT 0; `python3 -m unittest discover -s tests` Ran 394 tests in 73.237s, OK (skipped=2) at 2026-11-13T09:55:04Z. Registry at H25 (next_sequence_number 25); `tests/test_continuous_research_contract.py` asserts `next_sequence_number == 25`.
- **Session verification record:** `research_state/session_verifications/session_verify_20261113T095504Z.json` (this session; latest; `probe_evidence` matches disk). Prior record `session_verify_20261113T094746Z.json` retained as a historical snapshot.
- **Frozen hashes (unchanged):** canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`; F1SENS-002 source `7f85b38698745da5bf3e618bd729d59fd21c88da44b1a9795f93d20e5f639fa3`; `research_state/universe_frontier.json` `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e`.
- **H10 gate vs probe:** H10 cutoff gate **UNBLOCKED** by the published October 2026 archive. `probe_month=2026-11` probe is **BLOCKED as a probe only** (month-not-yet-published); the probe BLOCKED verdict is never promoted into the H10 gate decision. Fresh block IMMATURE (`n_formations=1`, `n_high=0`, `n_low=0`, `n_mid=1`, `last_allowed_formation=2026-09-30`, `data_cutoff=2026-10-31`); k not advanced (`sequential_look_number=1`, `sequential_remaining_budget=0.025`).
- **No bounded no-cost H10 task unblocked before 2026-11-30** (today 2026-11-13). H25 (DISP-003-F1STAB-003) complete: both H8/H19 stability warnings persist under the 29-31-asset F1 repair (F1_STABILITY_PRESERVED); no further development-data diagnostic preregistered.

## Initial task for next agent

### 0) Precondition — install dependencies
Before running the suite, install `requirements.txt` if numpy/pandas are missing:
`python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt`
This is free/local. Without it the suite errors with 9 `ModuleNotFoundError` + 1 requirements-import failure, which is an environment condition, not a repo defect.

### 1) On/after 2026-11-30 — H10 fresh sealed forward block (date-gated, bounded, no-cost)
This is the next executable action (date-gated, not an experiment-ID wait). Do **not** re-probe `probe_month=2026-11` before 2026-11-30.

1. Run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`.
2. If `target_published=true`:
   - Refresh free public data only (Coin Metrics Community API + Binance Public Data Archive).
   - Install `requirements.txt` if numpy/pandas are missing, then run `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests`.
   - Verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged.
   - Run the fresh sealed H10 block **only** into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--forward-block-start 2026-09-30 --data-cutoff <new cutoff> --look-number 1` (30-day maturity, `MIN_ASSETS_DECIMAL=20`, trailing-decile, 0.05 economic threshold, sequential `alpha_k = 0.05/(k*(k+1))` per H22/prereg sec 4.1).
3. Require `n_high > 0 AND n_low > 0` before any confirmatory claim. If immature, record outcome and **do not advance k**.
4. After a completed/blocked block, run `python3 scripts/record_test_claim.py` if any test/script changed, then update handoff, task message and a session verification record.
5. **Probe-evidence invariant:** if the session writes a probe, refresh the `probe_evidence` block in its session record using the canonical schema (`total_real_probes`, `probe_month_<month>` with `count`/`published`, `newest_probe`). Do not use `total_real_files`/`by_month` — `tests/test_state_consistency.py::test_latest_session_probe_evidence_matches_disk` only checks records carrying `total_real_probes` and will silently skip a non-canonical block.

### 2) If 2026-11-30 has not arrived (or probe remains blocked)
- Record "no bounded no-cost H10 task unblocked before 2026-11-30" with verified evidence in handoff/task message and a session verification record. Do not loop on known-failed probes or invent work.
- 30-day maturity and ">=30 prior in-block dispersions" trailing-decile rules are hard; no truncated outcome and no exploratory H10 relaxation admissible. The `MIN_STATE_FORMATIONS=5` confirmatory floor is separate and also unmet.
- Prefer a bounded, no-cost local task (tests/consistency checks) only if you first demonstrate a real gap; do not add duplicate audits. (Prior sessions found and fixed: a malformed prior `session_id`/probe schema; this session restored the missing numpy/pandas environment.)
- If you touch handoff/task message, keep the literal `probe_month=2026-11` label present whenever `2026-11` appears, and never assert the H10 cutoff gate as blocked; `tests/test_h10_gate_vs_november_probe.py` enforces both.
- Do not alter frontier, registry (except allocating a new hypothesis if you add an experiment), frozen 003 artifacts/configs/inputs or sealed holdout. `latest_november_2026_probe` pointer lag is guard-permitted; do not repoint by editing frontier.
- Probe-count evidence: recompute counts from disk rather than copying a prior record's number (currently 397 real files, 270 `probe_month=2026-10` / 127 `probe_month=2026-11`).
- If you allocate a new hypothesis, bump `next_sequence_number` AND `tests/test_continuous_research_contract.py`'s hard-coded `self.assertEqual(registry["next_sequence_number"], N)` in the same change, or the suite fails.

## Hard constraints
Free public data only; historical research only (no orders/live/paper trading); preserve DISPERSION-001/002 and frozen 003 artifacts/configs/inputs; no look-ahead/fabrication/forward-fill; today's rank ≠ historical truth; complete multiple-testing correction for any claim; do not reuse inspected holdout as fresh confirmation.

## End-of-session requirement
Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID."

(End of file - total 47 lines)
