## Initial task for next agent

Read `research_state/agent_handoff.md` (current **20261108T064821Z**), this file, `AGENTS.md`, `docs/research_protocol.md`, `prompts/continuous_research_operating_contract_v1.md`. Verify state before acting.

### Verified state (2026-11-08T06:48:21Z)
- **Checks (all passed):** `python3 -m compileall -q scripts tests` EXIT=0; `git status --short` clean pre-edit; `git diff --name-only -- artifacts/ configs/` empty; `audit_preregistration_coverage.py` pass=True (14/0/0); `audit_prereg_and_h10_fresh_references.py` pass=True (scanned=13, prereg=9, h10=1, forward_block=1, critical=0, errors=0, info=0) → `PREREG_AND_H10_FRESH_REFERENCE_CONSISTENCY_20261108T064821Z.json`; `audit_integrity_audit_references.py` pass=True (scanned=14, critical=0, errors=0, info=8) → `INTEGRITY_AUDIT_REFERENCE_CONSISTENCY_20261108T064821Z.json`.
- **Frozen hashes (recomputed from disk, unchanged):** H004V106 canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` (`forward_block/forward_block_evaluation.json`, sealed, n_formations=608, n_high=61, n_low=90, `high_low_diff_net_1x=0.6165223953929935`, data_cutoff=2026-09-30T00:00:00Z); H10 fresh IMMATURE `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f` (`forward_block_h10_fresh/forward_block_evaluation.json`, n_formations=1, n_high=0, n_low=0, `high_low_diff_net_1x=null`, `confirmatory_holm_significant=null`, `confirmatory_claim_allowed=false`, block_sealed=true, data_cutoff=2026-10-31T00:00:00Z).
- **H10 status:** CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / EVALUATED_NULL_DIFF_IMMATURE. First structurally classifiable cutoff projected **2026-11-30** (~31 formations). k not advanced. **No confirmatory claim.**
- **Cutoff gate:** November 2026 BLOCKED. Last real probe `2026-11-07T09:11:52Z` (`run_manifest.latest_november_2026_probe`, target_published=false, probe_exit=1); **re-probe forbidden before 2026-11-30**.

### Prior task disposition (20261108T064821Z)
- **COMPLETE (20261108T064637Z).** Independently verified compileall, clean git status pre-edit, zero frozen artifact/config diff, all three reference audits, and recomputed frozen hashes from disk. No bounded no-cost delta found. No source/artifact/config change made.

### Immediate next action (explicit, executable)
1. **On/after 2026-11-30:** run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If usable, refresh required free public data; run the fresh sealed block only into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`). Use H10 prereg + k=1 alpha-spending. Record all outcomes, including confirmatory-gate fields from the real evaluation.
2. **Before 2026-11-30:** act only if a genuine bounded no-cost gap is found (e.g., reproducible audit/test defect, missing reference guard, outcome-impacting drift with a safe fix). Otherwise keep next action as (1) and record that no unblocked task exists. Do not wait for a manually supplied experiment ID.
3. **If no bounded delta:** record that no unblocked task exists and keep next action as (1).

### Hard rules (non-negotiable)
- Never relax 30-day maturity, MIN_ASSETS_DECIMAL=20, trailing-decile rule, or 0.05 threshold.
- Never open canonical sealed holdout (`forward_block/`); fresh outputs go only to `forward_block_h10_fresh/` or a new uniquely identified path.
- Never use today's rank as historical truth. Never fabricate metrics. Preserve old artifacts/configs/results.
- Do not modify immutable closed preregistration/experiment records.
- Allocate unique IDs/preregister for new exploratory work. Keep confirmatory and exploratory tracks separate.
- A passing workflow/test proves only what it covers. No confirmatory claim from exploratory/integrity work.
- Follow adaptive research-gate policy v1: if a feasibility gate is durably blocked, do not loop; complete a bounded no-cost exploratory task only if one exists and record it, preserving blocked confirmatory status.

### Session records (this session)
- `research_state/session_verify_20261108T064821Z.json`
- `research_state/preregistration_coverage_audit.json`
- `research_state/PREREG_AND_H10_FRESH_REFERENCE_CONSISTENCY_20261108T064821Z.json`
- `research_state/INTEGRITY_AUDIT_REFERENCE_CONSISTENCY_20261108T064821Z.json`
