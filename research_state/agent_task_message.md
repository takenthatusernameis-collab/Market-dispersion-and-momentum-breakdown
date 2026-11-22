# Agent Task Message — 2026-11-22T00:48:01Z (next session)

## Initial task for next agent

Today is **2026-11-22T00:48:01Z**, which is **before** the hard date gate **2026-11-30**. Read the durable handoff (`research_state/agent_handoff.md`, newest `## Session summary — 2026-11-22T00:48:01Z`) and this message, then complete the standing task:

1. **Hold the confirmatory H10 track for the date gate.** Waiting for the fixed calendar date 2026-11-30 is a date gate, not a request for a new experiment ID. Do NOT re-run completed hypotheses (H54/H55/H56 are `EXPLORATORY_ONLY`, complete), do NOT re-probe `probe_month=2026-11` before the gate, and **do NOT add another verification-only checkpoint.** The H10 fresh sealed block is immature and cannot mature before that date.

2. **Why the wait is correct (frontier-confirmed, not a dead end).** `research_state/universe_frontier.json` `next_action` records that H10 is **BLOCKED BY DATA MATURITY, not a durable structural impossibility**, so the adaptive research-gate exploratory track is NOT triggered for H10. Concretely: `forward_block_start=2026-09-30` + 30-day horizon pins `last_allowed_formation` to 2026-09-30, and `trailing_window_outer_deciles` needs >=30 prior in-block dispersions, so the October 2026 cutoff yields only 1 fresh-block formation. **November 2026 (cutoff 2026-11-30) is the FIRST cutoff that structurally could classify high/low (~31 formations).** Do NOT relax the 30-day maturity rule, the state rule, or `MIN_ASSETS_DECILES=20`; do NOT fabricate formations/outcomes; do NOT open the canonical sealed holdout.

3. **Break the degenerate hold loop (important).** The prior ~20 sessions each re-verified the same unchanged state and refreshed this handoff pair. That is NOT progress and must not be repeated as a reflex. Before writing ANY durable-state change, ask: is this a genuinely NEW bounded no-cost action, or just another verification checkpoint? If it is verification-only, HOLD and leave state clean — do NOT spawn a new `session_verify_*.json`, do NOT rewrite the handoff with an identical narrative, and do NOT touch any artifact/config/input/frontier/registry. The only legitimate per-session durable change before the gate is a *genuinely new* bounded no-cost step (preregistered first as `EXPLORATORY_ONLY`), or the handoff/task-message refresh when real state changed. State is currently clean and verified; if nothing real changed, prefer to leave state untouched.

4. **No new hypothesis allocation.** Registry `research_state/hypothesis_registry.json` `next_sequence_number` must stay 56 (H1..H56 present; H10 `CANDIDATE_UNVALIDATED`, H54/H55/H56 `EXPLORATORY_ONLY`).

5. **If — and only if — a genuinely NEW-ID bounded no-cost step appears before the gate, preregister it first as `EXPLORATORY_ONLY`** per adaptive research-gate policy v1. Per H55 (`BREADTH-ARITY-001`) and H39, the binding requirement for any fresh mechanism test is **>=20 concurrently priced point-in-time eligible assets in a fresh period**. H55 already CLOSED the 2-asset ARK/ASTR mechanism route by construction (min_breadth_outer_deciles=20; 2-asset dispersion statistic is sign-invariant; wave-B-only months carry breadth 2) — do NOT re-attempt a 2-asset/9-asset diagnostic. A full H3 rank-band OUTCOME study needs committed Binance price/funding panels for the 188 cap-ranked candidate-arm assets that currently have cap history but NO committed price panels (H39 = RANK_BREADTH_MEASURABLE but price-panel-limited); that 188-asset refresh is unbounded and NOT justified before the gate. If no bounded step is justified, hold and leave state clean.

6. **Handoff hygiene.** Keep exactly ONE `(this session)` heading (the newest entry), plus `## Previous session` for older entries, or `tests.test_handoff_session_entries` will fail. The handoff title timestamp must match the newest session entry timestamp, and the handoff must quote the newest `session_verify_*.json` on disk (`session_verify_20261121T175518Z.json`).

7. **At/after 2026-11-30, execute Option A:** cutoff probe (`python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`, only when cutoff >= 2026-11-29) -> free-data refresh (`python3 scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>`) -> full suite (`python3 -m unittest discover -s tests`) -> hash check (H004V106 unchanged vs `git show HEAD:`) -> fresh sealed H10 block into `forward_block_h10_fresh/`, requiring `n_high > 0 AND n_low > 0`.

## Verified state (2026-11-22T00:48:01Z, this session)

- **compileall:** `python3 -m compileall -q scripts tests` EXIT 0.
- **Guard tests:** `python3 -m unittest tests.test_handoff_session_entries tests.test_task_message_probe_evidence tests.test_continuous_research_contract` (16 tests) EXIT 0 OK.
- **Git:** HEAD `5bd38055f0f6650924b1788e1c4930379c2402f0` on `main` with exactly this handoff/task-message refresh as uncommitted working-tree changes (no research-state change; left uncommitted per the no-commit rule). All four frozen hashes byte-unchanged vs recorded values.
- **Registry:** `research_state/hypothesis_registry.json` `next_sequence_number` 56 (H1..H56 present; H10 `CANDIDATE_UNVALIDATED`, H54/H55/H56 `EXPLORATORY_ONLY`). H10 fresh sealed block immature and date-gated to **2026-11-30**.
- **Probe evidence (disk):** 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`. (The only other `.json` in `research_state/cutoff_probe/` is `daily_fundingRate_probe_20261101T132013Z.json`, which is not a cutoff probe and is not counted.)
- **Recompute probe counts from disk:** 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`.
- **Frozen hashes byte-unchanged (git-clean vs recorded):** canonical forward block `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f` (= `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json`; sealed, `n_formations=1`, `n_high=0`, `n_low=0`, `n_mid=1`, `confirmatory_claim_allowed=false`, `evaluated_utc=2026-11-02T15:18:56Z`); grid config `1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176` (= `configs/dispersion_momentum_grid_v3.json`); frontier `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e` (= `research_state/universe_frontier.json`).
- **Newest session verification record on disk:** `research_state/session_verifications/session_verify_20261121T175518Z.json` (no new record this session — state clean; remains newest on disk).

## Hard constraints

Free public data only; historical research only; preserve DISPERSION-001/002 and frozen 003 artifacts; no look-ahead/fabrication; today's rank != historical truth; no paid services, secrets or trading.

## End-of-session requirement

Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action **only when real state changed**. Never write "wait for a new experiment ID." Waiting for fixed calendar date **2026-11-30** is a date gate. Do NOT add a redundant verification-only checkpoint, do NOT spawn a new `session_verify_*.json`, and do NOT repeat this hold loop as a reflex if state is already clean and unchanged — hold instead.

(End of file - total 38 lines)