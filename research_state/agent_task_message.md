## Initial task for next agent

Read `research_state/agent_handoff.md` (current **20261107T191514Z**), this file, `AGENTS.md`, `docs/research_protocol.md`, `prompts/continuous_research_operating_contract_v1.md`. Verify state before acting.

### Verified state (20261107T191514Z, HEAD baseline `fb7f6356` + bounded delta)
- Frozen hashes (disk == `git show HEAD:`): H004V106 canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; H10 fresh IMMATURE `9bdee66f737e492b3302a730af29ab9f811611e5a908ccf6002d08eab3e8bc5a`. `git diff --name-only -- artifacts/ configs/` empty.
- Checks (191514Z): compileall EXIT=0; prereg coverage pass (14/0/0); unittest **296 run, 0 failures, 1 skipped** (verified claim `research_state/verified_test_claim_claim_snapshot.json`).
- Bounded delta completed this session: `scripts/audit_integrity_audit_references.py` + `tests/test_integrity_audit_reference_consistency.py`; report `research_state/integrity_audit_reference_consistency_20261107T191514Z.json` (pass=True, 14 scanned, 0 critical/errors, 8 INFO addenda/legacy ID naming). No frozen artifact/config modified.
- H10 blocker is data-vintage maturity (first structurally classifiable cutoff 2026-11-30). Cutoff gate UNBLOCKED (Oct 2026 archive). November reprobe forbidden before 2026-11-30. H10 remains CANDIDATE_UNVALIDATED/EXPLORATORY_ONLY/EVALUATED_NULL_DIFF_IMMATURE; k not advanced.

### Immediate next action (pick the first that applies)
1. **On/after 2026-11-30 (highest priority):** run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If usable, refresh required free public data; install deps if needed; run tests; verify H004V106 unchanged vs `git show HEAD:`; run fresh sealed block **only** into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`). Use H10 prereg + alpha-spending (k=1 command from prereg). Record all outcomes.
2. **Before 2026-11-30, bounded no-cost delta only (no reverification-only session):** do exactly one concrete task that produces a new artifact/test/doc/red-team result and does not alter frozen artifacts/configs/results. Good candidates: (a) extend `audit_integrity_audit_references.py` to also cross-check `integrity_audit` refs against `git show HEAD:` hashes and/or cover `forward_block_h10_fresh`/preregistration markdown references; (b) add a regression test for `record_test_claim.py` or other manifest/state writer edge cases; (c) preregister a new uniquely identified exploratory diagnostic (EXPLORATORY_ONLY) feasible without post-2026-11-30 vintage data and add its minimal regression test. After the change, run applicable checks, confirm frozen hashes unchanged and `artifacts/configs` diff empty, record a session verification, and update handoff+task.
3. **If no bounded delta exists:** do not fabricate work. Record that no unblocked task exists and keep next action as (1).

### Hard rules
- Never relax 30-day maturity, MIN_ASSETS_DECILES=20, trailing-decile rule, or 0.05 threshold.
- Never open canonical sealed holdout (`forward_block/`); fresh outputs go only to `forward_block_h10_fresh/` or new uniquely identified path.
- Never use today's rank as historical truth. Never fabricate metrics. Preserve old artifacts/configs/results.
- Allocate unique IDs/preregister for new exploratory work. Keep confirmatory and exploratory tracks separate.
- A passing workflow/test proves only what it covers. No confirmatory claim from exploratory/integrity work.
