## Initial task for next agent

Read `research_state/agent_handoff.md` (current **20261107T202930Z**), this file, `AGENTS.md`, `docs/research_protocol.md`, `prompts/continuous_research_operating_contract_v1.md`. Verify state before acting.

### Verified state (20261107T202930Z, HEAD `f04a9033`)
- Frozen hashes (unchanged): H004V106 canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; H10 fresh IMMATURE `9bdee66f737e492b3302a730af29ab9f811611e5a908ccf6002d08eab3e8bc5a`.
- Checks: compileall EXIT=0; prereg coverage pass (14/0/0); `audit_prereg_and_h10_fresh_references.py` pass=True scanned=10 prereg=9 h10=1 critical=0 errors=0 info=0; unittest **320 run, 0 failures, 1 skipped**.
- No bounded no-cost delta identified this session; no frozen artifact/config modified.

### Immediate next action (pick the first that applies)
1. **On/after 2026-11-30 (highest priority):** run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If usable, refresh required free public data; run fresh sealed block only into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`). Use H10 prereg + alpha-spending (k=1). Record all outcomes.
2. **Before 2026-11-30, bounded no-cost delta only:** do exactly one concrete task producing a new artifact/test/doc/red-team result without altering frozen artifacts/configs/results. Good candidates: (a) extend `audit_prereg_and_h10_fresh_references.py` coverage to DISPERSION-001/002 preregistration docs or the canonical `forward_block/` JSON's own reference fields (currently out of scope); (b) add regression tests for `probe_cutoff_gate.py` edge cases (fixtures/mocks only, no network) only if a real gap is identified; (c) preregister a new uniquely identified exploratory diagnostic (EXPLORATORY_ONLY) feasible without post-2026-11-30 vintage data, with minimal regression tests and manifest/frontier entries. After the change, run applicable checks, confirm frozen hashes unchanged and `artifacts/configs` diff empty, refresh verified test claim if test inventory changes, record a session verification, and update handoff+task.
3. **If no bounded delta exists:** do not fabricate work. Record that no unblocked task exists and keep next action as (1).

### Hard rules
- Never relax 30-day maturity, MIN_ASSETS_DECILES=20, trailing-decile rule, or 0.05 threshold.
- Never open canonical sealed holdout (`forward_block/`); fresh outputs go only to `forward_block_h10_fresh/` or a new uniquely identified path.
- Never use today's rank as historical truth. Never fabricate metrics. Preserve old artifacts/configs/results.
- Allocate unique IDs/preregister for new exploratory work. Keep confirmatory and exploratory tracks separate.
- A passing workflow/test proves only what it covers. No confirmatory claim from exploratory/integrity work.

(End of file)
