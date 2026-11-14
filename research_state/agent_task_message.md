# Agent Task Message — 2026-11-14T00:58:17Z (next session)

## Verified state (2026-11-14T00:58:17Z)
- **HEAD at verification:** `1317e879` (`main`). Working tree was not clean at verification start (this session modified audits/tests/durable state); verify after any checkpoint commits.
- **Prior task complete:** read durable handoff and task message and completed its recorded action — record with verified evidence that no bounded no-cost H10 task is unblocked before 2026-11-30. Today 2026-11-14 is before the 2026-11-30 date gate; the H10 fresh sealed forward block remains not runnable and no bounded no-cost H10 task is unblocked before the gate. State re-verified and durable docs refreshed; quoting `research_state/session_verifications/session_verify_20261114T005817Z.json` (latest) and prior `session_verify_20261114T000049Z.json`.
- **New task completed this session (bounded, no-cost, genuinely new):** demonstrated a coverage gap and extended `scripts/audit_prereg_and_h10_fresh_references.py` to scan `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-001/preregistrations/` by default as a DISP-003 frozen prereg record. `F1_GRID_COVERAGE_REPAIR_v1.md` is committed prereg evidence with artifact/script/test references but was outside default scan scope (only F1COVERAGE-001/F1SENS-002/F1STAB-003 were scanned). The audit now reports its two missing referenced paths (`scripts/run_f1_grid.py`, `tests/test_f1_grid_coverage_repair.py`) as INFO `frozen_record_stale_pointer` (never ERROR, prereg doc never modified). Regression guards updated in `tests/test_prereg_and_h10_fresh_reference_consistency.py` (F1GRID-001 included in default scope; missing paths inside frozen prereg records must be surfaced as INFO, not treated as ERROR). No frozen artifact/config/input/frontier/registry/sealed holdout modified; `probe_month=2026-11` not re-probed.
- **Checks:** requirements confirmed (numpy 2.5.4 / pandas 3.1.1). `python3 -m compileall -q scripts tests` EXIT 0. Full suite `python3 -m unittest discover -s tests` — Ran 412 tests, OK, skipped=2 (no `.py` added/removed; claim snapshot unchanged).
- **Probe evidence (recomputed from disk):** **397 real `cutoff_probe_*.json` files (0 MOCK): 270 `probe_month=2026-10` (49 published / 221 not) and 127 `probe_month=2026-11` (all `target_published=false`)**; newest `cutoff_probe_20261113T091257Z.json`.
- **H10 gate vs probe:** H10 cutoff gate **UNBLOCKED** by the published October 2026 archive. The `probe_month=2026-11` probe is **BLOCKED as a probe only** (month-not-yet-published); the probe BLOCKED verdict is never promoted into the H10 gate decision.
- **H10 fresh block (unchanged, IMMATURE):** sha256 `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`, `n_formations=1`, `n_high=0`, `n_low=0`, `n_mid=1`, `last_allowed_formation_date=2026-09-30`, `data_cutoff_utc=2026-10-31T00:00:00Z`, `sequential_look_number=1`, `sequential_look_mature=false`, `sequential_remaining_budget=0.025`, `block_sealed=true`. k not advanced.
- **Frozen hashes (unchanged):** canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`; frontier `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e`.
- **Read-only audits (pass):** `audit_prereg_and_h10_fresh_references.py` pass=True scanned=17 (prereg 9 + disp003_frozen_prereg 4 + h10_fresh 1 + canonical forward_block 1 + variant 2), critical=0 errors=0 info=2 -> `research_state/PREREG_AND_H10_FRESH_REFERENCE_CONSISTENCY_20261114T005552Z.json`. `audit_integrity_audit_references.py` pass=True scanned=19, info=13 -> `research_state/INTEGRITY_AUDIT_REFERENCE_CONSISTENCY_20261114T005817Z.json`. `audit_preregistration_coverage.py` pass=True audits=19, missing_prereq=0, uncovered_prereq=0.
- **No bounded no-cost H10 task unblocked before 2026-11-30** (today 2026-11-14). Block requires formations strictly after 2026-09-29, strict 30-day outcome maturity, and ≥30 prior in-block dispersions for the trailing-decile high/low rule; only post-2026-09-29 formations live in the unpublished November 2026 monthly archive (0/127 `probe_month=2026-11` published). 30-day maturity and truncated-outcome prohibition are hard safeguards; `MIN_STATE_FORMATIONS=5` is separate and unmet. This is **BLOCKED_BY_HARD_DATE_GATE**, not an experiment-ID wait.

## Initial task for next agent

### 0) Precondition — install dependencies
Before running the suite, install `requirements.txt` if numpy/pandas are missing:
`python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt`
This is free/local. Without it, missing-dependency failures are an environment condition, not a repo defect.

### 1) Date-gated work (today is before 2026-11-30)
**Do NOT merely repeat this re-verification.** Prior sessions have re-verified the same date gate many times without new evidence; that is a loop, not progress. Since H10 cannot advance before 2026-11-30, pick **ONE** bounded, no-cost, genuinely new task from the categories in `AGENTS.md` (tests, source-coverage improvement, evidence audit, candidate evaluation, red-team, design), preregister it before computing outcomes when required, and deliver the verifiable artifact/test. Demonstrate a real gap first. Do not add a duplicate of an existing audit/guard or re-add a structural handoff/root-`HANDOFF.md` consistency check without a new demonstrated gap.

**Concrete candidates to evaluate (pick one with demonstrated gap/value):**
- Audit-coverage follow-up: `audit_preregistration_coverage.py` and `audit_integrity_audit_references.py` cover F1COVERAGE-001/F1SENS-002/F1STAB-003 but not `F1GRID-001` (which has a committed preregistration but no committed `integrity_audit/` dir and no grid-run outputs on disk). If extending an audit, demonstrate the gap, choose a defensible frozen-record convention (and avoid inventing prereqs/experiments), and add regression guards without modifying frozen preregs/artifacts.
- Any other evidenced, bounded task that improves auditability, tests, or exploratory measurement on already-available data without touching frozen 003 artifacts/configs/inputs, sealed holdout, or frontier/registry fields (except allocating a new hypothesis only if you genuinely add an experiment and you update the contract test in the same change).

If you instead confirm the date gate only because no new task is identifiable, use: `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests`; recompute probe counts from `research_state/cutoff_probe/`; confirm frozen hashes unchanged (canonical `7234fc4e...`, h10_fresh `324ab1e6...`, frontier `9ba08f3f...`). Record "no bounded no-cost H10 task unblocked before 2026-11-30" with verified evidence in handoff, task message, and a new session verification record. Do **not** re-probe `probe_month=2026-11` before 2026-11-30.

- 30-day maturity and ">=30 prior in-block dispersions" trailing-decile rules are hard; no truncated outcome and no exploratory H10 relaxation admissible. `MIN_STATE_FORMATIONS=5` confirmatory floor is separate and unmet.
- If you add or remove a `.py` file under `tests/` or `scripts/`, run `python3 scripts/record_test_claim.py` in the same change.

### 2) On/after 2026-11-30 — H10 fresh sealed forward block (date-gated)
1. Run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`.
2. If `target_published=true`: refresh free public data only (Coin Metrics Community API + Binance Public Data Archive); install requirements if needed; run `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests`; verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged; run fresh sealed H10 block **only** into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--forward-block-start 2026-09-30 --data-cutoff <new cutoff> --look-number 1` (30-day maturity, `MIN_ASSETS_DECIMAL=20`, trailing-decile, 0.05 economic threshold, sequential `alpha_k = 0.05/(k*(k+1))`).
3. Require `n_high > 0 AND n_low > 0` before any confirmatory claim. If immature, record outcome and **do not advance k**.
4. If tests/scripts change with a recordable claim, run `python3 scripts/record_test_claim.py` as appropriate; update handoff, task message, and a session verification record.
5. **Probe-evidence invariant:** if the session writes a probe, refresh `probe_evidence` in its session record using canonical schema (`total_real_probes`, `probe_month_<month>` with `count`/`published`, `newest_probe`).

### 3) Durable-state rules
- **Handoff shape:** top entry must be `## Session summary — <ts> (this session)` matching the title timestamp; every older entry `## Previous session — <ts>` with unique timestamps in strictly descending order; quote the newest `session_verifications/session_verify_*.json` on disk.
- Keep the literal `probe_month=2026-11` label present whenever `2026-11` appears, and never assert the H10 cutoff gate as blocked; `tests/test_h10_gate_vs_november_probe.py` enforces both.
- Do not alter frontier, registry (except allocating a new hypothesis if adding an experiment), frozen 003 artifacts/configs/inputs, or sealed holdout. `latest_november_2026_probe` pointer lag is guard-permitted.
- Recompute probe counts from disk (currently 397 real cutoff_probe files, 270 `probe_month=2026-10` / 127 `probe_month=2026-11`).
- If you allocate a new hypothesis, bump `next_sequence_number` AND `tests/test_continuous_research_contract.py` in the same change.

## Hard constraints
Free public data only; historical research only (no orders/live/paper trading); preserve DISPERSION-001/002 and frozen 003 artifacts/configs/inputs; no look-ahead/fabrication/forward-fill; today's rank ≠ historical truth; complete multiple-testing correction for any claim; do not reuse inspected holdout as fresh confirmation.

## End-of-session requirement
Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID." Waiting for fixed calendar date 2026-11-30 is a date gate.

(End of file)
