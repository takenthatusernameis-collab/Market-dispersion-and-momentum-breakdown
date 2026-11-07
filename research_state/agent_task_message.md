## Initial task for next agent

Read `research_state/agent_handoff.md` (current **20261107T193221Z**), this file, `AGENTS.md`, `docs/research_protocol.md`, `prompts/continuous_research_operating_contract_v1.md`. Verify state before acting.

### Verified state (20261107T193221Z, HEAD baseline `80346656` + bounded delta)
- Frozen hashes (`artifacts/configs` diff empty): H004V106 canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; H10 fresh IMMATURE `9bdee66f737e492b3302a730af29ab9f811611e5a908ccf6002d08eab3e8bc5a`.
- Checks (193221Z): compileall EXIT=0; prereg coverage pass (14/0/0); unittest **312 run, 0 failures, 1 skipped** via `record_test_claim.py` (verified claim `research_state/verified_test_claim_claim_snapshot.json`, 100 input files).
- Bounded delta completed this session: added `tests/test_record_test_claim.py` (15 tests, fixtures only, no network/suite exec) pinning `record_test_claim.py` helper contracts. No frozen artifact/config modified.
- H10 blocker is data-vintage maturity (first structurally classifiable cutoff 2026-11-30). Cutoff gate UNBLOCKED (Oct 2026 archive). November reprobe forbidden before 2026-11-30. H10 remains CANDIDATE_UNVALIDATED/EXPLORATORY_ONLY/EVALUATED_NULL_DIFF_IMMATURE; k not advanced.

### Immediate next action (pick the first that applies)
1. **On/after 2026-11-30 (highest priority):** run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If usable, refresh required free public data; install deps if needed; run tests; verify H004V106 unchanged vs `git show HEAD:`; run fresh sealed block **only** into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`). Use H10 prereg + alpha-spending (k=1 command from prereg). Record all outcomes.
2. **Before 2026-11-30, bounded no-cost delta only (no reverification-only session):** do exactly one concrete task that produces a new artifact/test/doc/red-team result and does not alter frozen artifacts/configs/results. Good candidates: (a) extend integrity-audit coverage to scan preregistration markdown/JSON cross-references and `forward_block_h10_fresh` ancillary files for stale pointers/hashes (report to `research_state/` to avoid prereg-completeness guard issues); (b) add regression tests for `probe_cutoff_gate.py` edge cases (fixtures/mocks only, no network) — note `tests/test_cutoff_probe.py` already exists, so extend it only if a real gap is identified; (c) preregister a new uniquely identified exploratory diagnostic (EXPLORATORY_ONLY) feasible without post-2026-11-30 vintage data, add minimal regression tests, and record manifest/frontier entries. After the change, run applicable checks, confirm frozen hashes unchanged and `artifacts/configs` diff empty, refresh verified test claim if test inventory changes, record a session verification, and update handoff+task.
3. **If no bounded delta exists:** do not fabricate work. Record that no unblocked task exists and keep next action as (1).

### Hard rules
- Never relax 30-day maturity, MIN_ASSETS_DECILES=20, trailing-decile rule, or 0.05 threshold.
- Never open canonical sealed holdout (`forward_block/`); fresh outputs go only to `forward_block_h10_fresh/` or a new uniquely identified path.
- Never use today's rank as historical truth. Never fabricate metrics. Preserve old artifacts/configs/results.
- Allocate unique IDs/preregister for new exploratory work. Keep confirmatory and exploratory tracks separate.
- A passing workflow/test proves only what it covers. No confirmatory claim from exploratory/integrity work.
