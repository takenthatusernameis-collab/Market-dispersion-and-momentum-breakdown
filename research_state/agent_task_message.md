## Initial task for next agent

Read `research_state/agent_handoff.md` (current **20261107T222131Z**), this file, `AGENTS.md`, `docs/research_protocol.md`, `prompts/continuous_research_operating_contract_v1.md`. Verify state before acting.

### Verified state (20261107T222131Z, HEAD `cfd1a781`, working tree clean apart from new untracked consistency records)
- Frozen hashes (unchanged): H004V106 canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; H10 fresh IMMATURE `9bdee66f737e492b3302a730af29ab9f811611e5a908ccf6002d08eab3e8bc5a`. `git diff --name-only -- artifacts/ configs/` empty.
- Reverification-only session (no source/artifact delta): compileall EXIT=0; prereg coverage pass=True (14/0/0); prereg/h10 ref audit pass=True scanned=13 prereg=9 frozen_prereg=0 h10=1 forward_block=1 h10_variant=2 critical=0 errors=0 info=0; integrity-audit ref audit pass=True scanned=14 critical=0 errors=0 info=8; `python3 -m unittest discover -s tests` **324 run, 0 failures, 1 skipped (OK)**. Verified test claim unchanged (324/324/0, fingerprint `e442d8b28997fe49…`, 102 input files; `research_state/run_manifest.json:latest_verified_test_claim` = `324/324/0`).
- **No bounded no-cost delta exists before 2026-11-30** (recorded). All reference/prereg/integrity audits pass; pure utility coverage present; remaining untested scripts mutate artifacts, require network, or are data-dependent. Do not fabricate work or reverification-only artifacts beyond what is needed; keep next action as (1).
- Cutoff gate: H10 gate UNBLOCKED per `latest_archive_probe` (October 2026 archive published, probe `2026-11-05T10:38:51Z`, probe_exit 0). November 2026 still BLOCKED (target_published=false, probe `2026-11-07T09:11:52Z`); **re-probe forbidden before 2026-11-30**. H10 fresh block IMMATURE (n_formations=1, n_high=0, n_low=0, `high_low_diff_net_1x=null`); first structurally classifiable cutoff projected 2026-11-30 (~31 formations). k not advanced. No confirmatory claim.

### Immediate next action (pick the first that applies)
1. **On/after 2026-11-30 (highest priority):** run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If usable (`target_published=true` and archive alive), refresh required free public data; run fresh sealed block only into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`). Use H10 prereg + alpha-spending (k=1). Record all outcomes.
2. **Before 2026-11-30:** act only if a genuine, bounded, no-cost gap is found (e.g., a real defect, missing regression for a pure non-network/non-mutating utility with a clear risk). Otherwise keep next action as (1) and record (3).
3. **If no bounded delta exists:** record that no unblocked task exists and keep next action as (1).

### Hard rules
- Never relax 30-day maturity, MIN_ASSETS_DECILES=20, trailing-decile rule, or 0.05 threshold.
- Never open canonical sealed holdout (`forward_block/`); fresh outputs go only to `forward_block_h10_fresh/` or a new uniquely identified path.
- Never use today's rank as historical truth. Never fabricate metrics. Preserve old artifacts/configs/results.
- Do not modify immutable closed preregistration/experiment records (DISP-001/002, frozen DISP-003 prereg docs) to "fix" historical text; report stale pointers as INFO/addenda only.
- Allocate unique IDs/preregister for new exploratory work. Keep confirmatory and exploratory tracks separate.
- A passing workflow/test proves only what it covers. No confirmatory claim from exploratory/integrity work.
