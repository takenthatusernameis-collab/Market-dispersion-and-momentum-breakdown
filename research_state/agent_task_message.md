# Agent Task Message — 2026-11-13T13:06:10Z (next session)

## Verified state (2026-11-13T13:06:10Z)
- **HEAD at verification start:** `4db0224f42a8d9c5fcdbb447ea5c81c3be588428` (`main`), working tree clean at start of verification.
- **Prior task complete:** read durable handoff and task message from 2026-11-13T13:05:00Z and re-verified its recorded action — record with verified evidence that no bounded no-cost H10 task is unblocked before 2026-11-30 (re-verified today). Today 2026-11-13 is before the 2026-11-30 date gate, so the H10 fresh sealed forward block is not runnable; no bounded no-cost H10 task is unblocked before the gate. State re-verified and durable docs refreshed.
- **Checks:** `python3 -m compileall -q scripts tests` EXIT 0. Targeted gate suites `python3 -m unittest tests.test_state_consistency tests.test_h10_gate_vs_november_probe tests.test_continuous_research_contract` — Ran 31 tests, OK. Full suite not run this session (prior session recorded 394 tests OK, skipped=2; numpy 2.5.4 / pandas 3.1.1).
- **Session verification record:** `research_state/session_verifications/session_verify_20261113T130610Z.json` (this session; latest; `probe_evidence` matches disk). Prior records retained as historical snapshots.
- **Probe evidence (recomputed from disk):** **397 real `cutoff_probe_*.json` files (0 MOCK): 270 `probe_month=2026-10` (49 published / 221 not) and 127 `probe_month=2026-11` (all `target_published=false`)**; newest `cutoff_probe_20261113T091257Z.json`.
- **H10 gate vs probe:** H10 cutoff gate **UNBLOCKED** by the published October 2026 archive. The `probe_month=2026-11` probe is **BLOCKED as a probe only** (month-not-yet-published); the probe BLOCKED verdict is never promoted into the H10 gate decision.
- **H10 fresh block (unchanged, IMMATURE):** sha256 `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`, `n_formations=1`, `n_high=0`, `n_low=0`, `n_mid=1`, `last_allowed_formation_date=2026-09-30`, `data_cutoff_utc=2026-10-31T00:00:00Z`, `sequential_look_number=1`, `sequential_look_mature=false`, `sequential_remaining_budget=0.025`, `block_sealed=true`. k not advanced.
- **Frozen hashes (unchanged):** canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`; `research_state/universe_frontier.json` `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e`.
- **Frontier/registry:** frontier `ACTIVE_INCOMPLETE`, cursor 6347, verified 220 / blocked 6127, not exhausted. Registry at H25 (`next_sequence_number=25`); `tests/test_continuous_research_contract.py` asserts this value.
- **No bounded no-cost H10 task unblocked before 2026-11-30** (today 2026-11-13). H25 (DISP-003-F1STAB-003) complete (F1_STABILITY_PRESERVED); no further development-data diagnostic preregistered.

## Initial task for next agent

### 0) Precondition — install dependencies
Before running the suite, install `requirements.txt` if numpy/pandas are missing:
`python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt`
This is free/local. Without it, missing-dependency failures are an environment condition, not a repo defect.

### 1) On/after 2026-11-30 — H10 fresh sealed forward block (date-gated, bounded, no-cost)
This is the next executable action (date-gated, not an experiment-ID wait). Do **not** re-probe `probe_month=2026-11` before 2026-11-30.

1. Run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`.
2. If `target_published=true`:
   - Refresh free public data only (Coin Metrics Community API + Binance Public Data Archive).
   - Install requirements if numpy/pandas are missing, then run `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests`.
   - Verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged.
   - Run the fresh sealed H10 block **only** into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--forward-block-start 2026-09-30 --data-cutoff <new cutoff> --look-number 1` (30-day maturity, `MIN_ASSETS_DECIMAL=20`, trailing-decile, 0.05 economic threshold, sequential `alpha_k = 0.05/(k*(k+1))` per H22/prereg sec 4.1).
3. Require `n_high > 0 AND n_low > 0` before any confirmatory claim. If immature, record the outcome and **do not advance k**.
4. If you change tests/scripts with a recordable claim, run `python3 scripts/record_test_claim.py` as appropriate, then update handoff, task message and a session verification record.
5. **Probe-evidence invariant:** if the session writes a probe, refresh the `probe_evidence` block in its session record using the canonical schema (`total_real_probes`, `probe_month_<month>` with `count`/`published`, `newest_probe`). Do not use `total_real_files`/`by_month` — `tests/test_state_consistency.py::test_latest_session_probe_evidence_matches_disk` only checks records carrying `total_real_probes`.

### 2) If 2026-11-30 has not arrived (or the probe remains blocked)
- Record "no bounded no-cost H10 task unblocked before 2026-11-30" with verified evidence in handoff/task message and a session verification record. Do not loop on known-failed probes or invent work.
- 30-day maturity and ">=30 prior in-block dispersions" trailing-decile rules are hard; no truncated outcome and no exploratory H10 relaxation admissible. The `MIN_STATE_FORMATIONS=5` confirmatory floor is separate and also unmet.
- Prefer a bounded, no-cost local task (tests/consistency checks) only if you first demonstrate a real gap; do not add duplicate audits.
- If you touch handoff/task message, keep the literal `probe_month=2026-11` label present whenever `2026-11` appears, and never assert the H10 cutoff gate as blocked; `tests/test_h10_gate_vs_november_probe.py` enforces both.
- Do not alter frontier, registry (except allocating a new hypothesis if you add an experiment), frozen 003 artifacts/configs/inputs or sealed holdout. `latest_november_2026_probe` pointer lag is guard-permitted; do not repoint by editing the frontier.
- Probe-count evidence: recompute counts from disk rather than copying a prior record's number (currently 397 real files, 270 `probe_month=2026-10` / 127 `probe_month=2026-11`).
- If you allocate a new hypothesis, bump `next_sequence_number` AND `tests/test_continuous_research_contract.py`'s hard-coded `self.assertEqual(registry["next_sequence_number"], N)` in the same change, or the suite fails.

## Hard constraints
Free public data only; historical research only (no orders/live/paper trading); preserve DISPERSION-001/002 and frozen 003 artifacts/configs/inputs; no look-ahead/fabrication/forward-fill; today's rank ≠ historical truth; complete multiple-testing correction for any claim; do not reuse inspected holdout as fresh confirmation.

## End-of-session requirement
Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID." Waiting for fixed calendar date 2026-11-30 is a date gate.
