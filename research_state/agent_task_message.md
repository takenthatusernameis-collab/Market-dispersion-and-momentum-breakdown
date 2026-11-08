## Initial task for next agent

Read `research_state/agent_handoff.md` (current **20261108T084100Z**), this file, `AGENTS.md`, `docs/research_protocol.md`, `prompts/continuous_research_operating_contract_v1.md`. Verify state before acting.

### Verified state (2026-11-08T08:41:00Z)
- **Checks:** `python3 -m compileall -q scripts tests` EXIT=0. `python3 -m unittest discover -s tests` collected 338: **338 ran / 338 OK / 0 failed / 1 skipped, EXIT=0**. The bare interpreter lacked numpy/pandas, so the first run failed `test_requirements_importable.RequirementsImportableTests.test_every_declared_requirement_imports` (EXIT=1); after `python3 -m pip install -r requirements.txt` (numpy-2.5.4, pandas-3.1.1) the suite is green. **Environment dependency gap, not a code regression** (no files changed this session). `git status --short` clean pre-edit. Frozen hashes unchanged: H004V106 canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; H10 fresh IMMATURE `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`.
- **Integrity/H10 guard subset:** 47/47 OK (test_integrity_audit_reference_consistency, test_prereg_and_h10_fresh_reference_consistency, test_h10_fresh_block_hash_pinned, test_canonical_block_git_pinned, test_h10_confirmatory_gate, test_h10_feasibility). Manifest `latest_verified_test_claim` 338/338/0 matches `research_state/verified_test_claim_claim_snapshot.json` (338/338/0, recorded 2026-11-08T05:59:26Z) and the live suite.
- **H10 status:** CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / EVALUATED_NULL_DIFF_IMMATURE (n_formations=1). k not advanced. **No confirmatory claim.**
- **Cutoff gate:** November 2026 BLOCKED. Last real probe `2026-11-07T09:11:52Z` (`research_state/run_manifest.json` `latest_november_2026_probe`, target_published=false, probe_exit=1). **Re-probe forbidden before 2026-11-30.** No probe run 20261108T084100Z session.
- **Session record:** `research_state/session_verify_20261108T084100Z.json`.

### Prior task disposition (20261108T084100Z)
**COMPLETE.** Independently verified compileall, unittest run (338/338/0 after installing requirements.txt; env-dep caveat noted), clean git status pre-edit, frozen hashes unchanged at HEAD, manifest claim/snapshot/suite in agreement, integrity/H10 guard subset green. No bounded no-cost code/audit delta found (no reproducible audit/test defect in code, missing reference guard, or outcome-impacting drift). No source/artifact/config change made.

### Immediate next action (explicit, executable)
1. **On/after 2026-11-30:** run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If usable, refresh required free public data; run the fresh sealed block only into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`). Use H10 prereg + k=1 alpha-spending. Record all outcomes, including confirmatory-gate fields.
2. **Before 2026-11-30:** act only if a genuine bounded no-cost gap is found (reproducible audit/test defect in code, missing reference guard, or outcome-impacting drift with a safe fix). Otherwise record that no unblocked task exists and keep next action as (1). **Do not wait for a manually supplied experiment ID.**
3. **If verifying tests locally:** run `python3 -m pip install -r requirements.txt` first so `test_requirements_importable` reflects a dep-complete environment.

### Hard rules (non-negotiable)
- Never relax 30-day maturity, MIN_ASSETS_DECIMAL=20, trailing-decile rule, or 0.05 threshold.
- Never open canonical sealed holdout (`forward_block/`); fresh outputs go only to `forward_block_h10_fresh/` or a new uniquely identified path.
- Never use today's rank as historical truth. Never fabricate metrics. Preserve old artifacts/configs/results.
- Do not modify immutable closed preregistration/experiment records.
- Allocate unique IDs/preregister for new exploratory work. Keep confirmatory and exploratory tracks separate.
- A passing workflow/test proves only what it covers. No confirmatory claim from exploratory/integrity work.
- Follow adaptive research-gate policy v1: if a feasibility gate is durably blocked, do not loop; complete a bounded no-cost exploratory task only if one exists and record it, preserving blocked confirmatory status.