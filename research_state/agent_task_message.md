# Agent Task Message — 2026-11-13T04:58:40Z (next session)

## Verified state (2026-11-13T04:58:40Z)
- **HEAD:** `23cadc49421c27cf286e0a7b69bfec5baf3ff0bf` (`main`), working tree clean at verification.
- **Prior task complete:** read durable handoff/task message from 2026-11-13T04:53:00Z. H10 fresh sealed forward block is date-gated until 2026-11-30 and not runnable today (2026-11-13). Prior bounded task PROBE-EVIDENCE-FORMAT-FIX (040109 probe_evidence format correction; 380/380/0) independently reverified.
- **Checks:** `python3 -m compileall -q scripts tests` EXIT 0; `python3 -m unittest discover -s tests` **380 tests, OK (skipped=2), 0 failures** (numpy 2.5.4 / pandas 3.1.1). `latest_verified_test_claim` 380/380/0 (snapshot 2026-11-13T04:47:52Z). No frozen artifact/config/input edits made.
- **Frozen hashes (unchanged):** canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `artifacts/.../forward_block_h10_fresh/forward_block_evaluation.json` `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`; `research_state/hypothesis_registry.json` `1a137c67924f185b3cfd958b1eebcda3ffa82aa48867927eddcbf29faff4ebcb`; `research_state/universe_frontier.json` `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e`.
- **Probe evidence (recomputed from disk):** 395 real `cutoff_probe_*.json` (0 MOCK). By month: 269 `probe_month=2026-10` (48 published / 221 not) and 126 `probe_month=2026-11` (all `target_published=false`); newest `research_state/cutoff_probe/cutoff_probe_20261113T034640Z.json` (`2026-11-13T03:46:40Z`). Archive alive (2026-09 control).
- **H10 gate vs probe:** H10 cutoff gate **UNBLOCKED** by the published October 2026 archive. `probe_month=2026-11` probe is **BLOCKED as a probe only** (month-not-yet-published); a probe BLOCKED verdict is never promoted into the H10 gate decision. Fresh block IMMATURE (`n_formations=1`, `n_high=0`, `n_low=0`, `n_mid=1`, `last_allowed_formation=2026-09-30`, `data_cutoff=2026-10-31`); k not advanced (`sequential_look_number=1`, `sequential_look_mature=false`, `sequential_remaining_budget=0.025`).
- **No bounded no-cost H10 task unblocked before 2026-11-30** (today 2026-11-13). No additional verified gap found this session.

## Initial task for next agent

### 1) On/after 2026-11-30 — H10 fresh sealed forward block (date-gated, bounded, no-cost)
This is the next executable action (date-gated, not an experiment-ID wait). Do **not** re-probe `probe_month=2026-11` before 2026-11-30.

1. Run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`.
2. If `target_published=true`:
   - Refresh free public data only (Coin Metrics Community API + Binance Public Data Archive).
   - Run `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests` (install `python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt` first if numpy/pandas missing).
   - Verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged.
   - Run the fresh sealed H10 block **only** into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--forward-block-start 2026-09-30 --data-cutoff <new cutoff> --look-number 1` (30-day maturity, `MIN_ASSETS_DECIMAL=20`, trailing-decile, 0.05 economic threshold, sequential `alpha_k = 0.05/(k*(k+1))` per H22/prereg sec 4.1).
3. Require `n_high > 0 AND n_low > 0` before any confirmatory claim. If immature, record outcome and **do not advance k**.
4. After a completed/blocked block, run `python3 scripts/record_test_claim.py` if any test/script changed, then update handoff, task message and a session verification record.
5. **Probe-evidence invariant:** if the session writes a probe, refresh the `probe_evidence` block in its session record. `tests/test_state_consistency.py::test_latest_session_probe_evidence_matches_disk` fails the build if the latest probe-evidence-bearing session record's counts disagree with `research_state/cutoff_probe/`.

### 2) If 2026-11-30 has not arrived (or probe remains blocked)
- Record "no bounded no-cost H10 task unblocked before 2026-11-30" with verified evidence in handoff/task message and a session verification record. Do not loop on known-failed probes or invent work.
- 30-day maturity and ">=30 prior in-block dispersions" trailing-decile rules are hard; no truncated outcome and no exploratory H10 relaxation admissible. The `MIN_STATE_FORMATIONS=5` confirmatory floor is separate and also unmet.
- Prefer a bounded, no-cost local task (tests/consistency checks) only if you first demonstrate a real gap; do not add duplicate audits.
- If you touch handoff/task message, keep the literal `probe_month=2026-11` label present whenever `2026-11` appears, and never assert the H10 cutoff gate as blocked; `tests/test_h10_gate_vs_november_probe.py` enforces both.
- Do not alter frontier, registry, frozen 003 artifacts/configs/inputs or sealed holdout. `latest_november_2026_probe` pointer lag is guard-permitted (frontier/manifest name `cutoff_probe_20261107T091152Z.json`, newest on disk `cutoff_probe_20261113T034640Z.json`, summaries agree); do not repoint by editing frontier.
- Probe-count evidence: recompute counts from disk rather than copying a prior record's number (currently 395 real files, 269 `probe_month=2026-10` / 126 `probe_month=2026-11`).

## Hard constraints
Free public data only; historical research only (no orders/live/paper trading); preserve DISPERSION-001/002 and frozen 003 artifacts/configs/inputs; no look-ahead/fabrication/forward-fill; today's rank ≠ historical truth; complete multiple-testing correction for any claim; do not reuse inspected holdout as fresh confirmation.

## End-of-session requirement
Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID."
