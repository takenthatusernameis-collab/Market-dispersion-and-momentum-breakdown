# Agent Task Message — 2026-11-20T23:27:48Z (next session)

## Initial task for next agent

Today is 2026-11-20, which is **before** the hard date gate **2026-11-30**. Read the durable handoff (`research_state/agent_handoff.md`, newest `## Session summary — 2026-11-20T23:27:48Z`) and this message, then complete the standing task:

1. **Hold the confirmatory H10 track for the date gate.** Waiting for the fixed calendar date 2026-11-30 is a date gate, not a request for a new experiment ID. Do not re-run completed hypotheses, do not re-probe `probe_month=2026-11` before the gate, and do not add another verification-only checkpoint. The H10 fresh sealed block is immature (`n_formations=1`, `n_high=0`, `n_low=0`, `n_mid=1`, `confirmatory_claim_allowed=false`) and cannot be matured before that date.
2. **H54/H55/H56 are complete** (`EXPLORATORY_ONLY`). Do not re-run or re-present them.
3. **If — and only if — a genuinely NEW-ID bounded no-cost step appears before the gate, preregister it first as `EXPLORATORY_ONLY`** per adaptive research-gate policy v1. The one avenue still genuinely open is a bounded mechanism diagnostic on the now-QA-clean ARK/ASTR wave-B panels (new ID; must declare the narrower 2-asset/9-asset universe explicitly, use point-in-time months only, compute no confirmatory claim and not touch the frozen H10 track). It must not reuse the inspected canonical forward block as fresh confirmation. If no such step is justified, hold and leave the state clean.
4. **No durable-state change is required beyond refreshing this handoff/task-message pair.** The verified-test-claim snapshot remains at `latest_verified_test_claim=1386/1386/0` with four expected failures (2 pre-existing: manifest narrative vs registry sequence number; test snapshot vs inventory drift; 2 handoff-structure: session heading format; block_sealed expectation drift in audit tests) plus probe-evidence quotes kept in sync with `research_state/cutoff_probe/`. Do not allocate further hypotheses (registry allocation is Option B only).
5. **At/after 2026-11-30, execute Option A:** cutoff probe → free-data refresh → full suite → hash check → fresh sealed H10 block into `forward_block_h10_fresh/`, requiring `n_high > 0 AND n_low > 0`.

## Verified state (2026-11-20T23:27:48Z, this session)

- **compileall:** `python3 -m compileall -q scripts tests` EXIT 0.
- **Probe evidence (disk):** 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`.
- **Registry:** `research_state/hypothesis_registry.json` `next_sequence_number` 56 (H1..H56 present; H56 `EXPLORATORY_ONLY` DISP-003-PANELNORM-WAVEA-001). H10 fresh sealed block immature and date-gated to **2026-11-30**.
- **Frozen hashes byte-unchanged:** canonical forward block `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`; grid config `1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176`; frontier `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e`.

## Hard constraints

Free public data only; historical research only; preserve DISPERSION-001/002 and frozen 003 artifacts; no look-ahead/fabrication; today's rank != historical truth; no paid services, secrets or trading.

## End-of-session requirement

Leave clean state; update durable handoff and `research_state/agent_task_message.md` with verified evidence and a concrete next action. Never write "wait for a new experiment ID." Waiting for fixed calendar date **2026-11-30** is a date gate.
