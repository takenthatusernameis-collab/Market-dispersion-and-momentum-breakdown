# Agent Task Message — 2026-11-21T05:49:39Z (next session)

## Initial task for next agent

Today is 2026-11-21, which is **before** the hard date gate **2026-11-30**. Read the durable handoff (`research_state/agent_handoff.md`, newest `## Session summary — 2026-11-21T05:49:39Z`) and this message, then complete the standing task:

1. **Hold the confirmatory H10 track for the date gate.** Waiting for the fixed calendar date 2026-11-30 is a date gate, not a request for a new experiment ID. Do not re-run completed hypotheses, do not re-probe `probe_month=2026-11` before the gate, and do not add another verification-only checkpoint. The H10 fresh sealed block is immature (`n_formations=1`, `n_high=0`, `n_low=0`, `n_mid=1`, `confirmatory_claim_allowed=false`) and cannot be matured before that date. Per the frontier `next_action`, November 2026 (cutoff 2026-11-30) is the FIRST vintage that structurally could classify high/low at ~31 formations, so the wait is correct and the only path for the registered H10 config.

2. **H54/H55/H56 are complete** (`EXPLORATORY_ONLY`). Do not re-run or re-present them. **H55 (`BREADTH-ARITY-001`) already CLOSED the 2-asset ARK/ASTR mechanism route by construction** — min_breadth_outer_deciles=20 (empty tails below 20 assets), the 2-asset dispersion statistic is sign-invariant (cannot pick a long/short leg), and the wave-B-only months carry breadth 2. Do not re-attempt a 2-asset diagnostic.

3. **If — and only if — a genuinely NEW-ID bounded no-cost step appears before the gate, preregister it first as `EXPLORATORY_ONLY`** per adaptive research-gate policy v1. Per H55 and H39, the binding requirement for any fresh mechanism test is **>=20 concurrently priced point-in-time eligible assets in a fresh period**, and a full H3 rank-band OUTCOME study needs committed Binance price/funding panels for the 188 cap-ranked candidate-arm assets that currently have cap history but NO committed price panels (H39 = RANK_BREADTH_MEASURABLE but price-panel-limited). That 188-asset refresh is unbounded and not justified before the gate. A 2-asset/9-asset panel cannot identify the dispersion-conditioning mechanism and must not reuse the inspected canonical forward block as fresh confirmation. If no bounded step is justified, hold and leave the state clean.

4. **No durable-state change is required beyond refreshing this handoff/task-message pair.** Do NOT allocate a new hypothesis (registry `next_sequence_number` must stay 56). The verified-test-claim snapshot is `latest_verified_test_claim=1386/1386/0` (full suite green: 1386 tests, 0 failures, skipped=8, EXIT=0) with input fingerprint `e928e71cd166a6056c3e315fdcea8a83cdd1d5f9289d5dc4fcca15351daee68c` (206 files). Probe-evidence quotes are kept in sync with `research_state/cutoff_probe/`.

5. **At/after 2026-11-30, execute Option A:** cutoff probe -> free-data refresh -> full suite -> hash check -> fresh sealed H10 block into `forward_block_h10_fresh/`, requiring `n_high > 0 AND n_low > 0`.

## Verified state (2026-11-21T05:49:39Z, this session)

- **compileall:** `python3 -m compileall -q scripts tests` EXIT 0.
- **Guard tests:** `tests.test_handoff_session_entries tests.test_task_message_probe_evidence tests.test_continuous_research_contract` (16 tests) EXIT 0 OK.
- **Git:** working tree clean (git porcelain empty), on `main`. All four frozen hashes byte-unchanged vs HEAD.
- **Registry:** `research_state/hypothesis_registry.json` `next_sequence_number` 56 (H1..H56 present; H10 `CANDIDATE_UNVALIDATED`, H56 `EXPLORATORY_ONLY` DISP-003-PANELNORM-WAVEA-001). H10 fresh sealed block immature and date-gated to **2026-11-30**.
- **Full suite (prior session, still valid):** `python3 -m unittest discover -s tests` **1386 tests, 0 failures, skipped=8, EXIT=0** after installing declared free deps (numpy 2.5.5, pandas 3.1.1). Verified-test-claim snapshot `latest_verified_test_claim=1386/1386/0` with input fingerprint `e928e71cd166a6056c3e315fdcea8a83cdd1d5f9289d5dc4fcca15351daee68c` (206 files).
- **Probe evidence (disk):** 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`.
- **Recompute probe counts from disk:** 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`.
- **Frozen hashes byte-unchanged (git-clean vs HEAD):** canonical forward block `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f` (sealed, `n_formations=1`, `n_high=0`, `n_low=0`, `n_mid=1`, `confirmatory_claim_allowed=false`); grid config `1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176`; frontier `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e`.
- **Newest session verification record on disk:** `research_state/session_verifications/session_verify_20261121T000747Z.json` (2026-11-21). This session did not add a new verification record.

## Hard constraints

Free public data only; historical research only; preserve DISPERSION-001/002 and frozen 003 artifacts; no look-ahead/fabrication; today's rank != historical truth; no paid services, secrets or trading.

## End-of-session requirement

Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID." Waiting for fixed calendar date **2026-11-30** is a date gate.
