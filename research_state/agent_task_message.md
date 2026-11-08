## Initial task for next agent

Read `research_state/agent_handoff.md` (current **20261108T104200Z**), this file, `AGENTS.md`, `docs/research_protocol.md`, `prompts/continuous_research_operating_contract_v1.md`. Verify state before acting.

### Verified state (2026-11-08T10:42:00Z)
- **Checks:** `python3 -m compileall -q scripts tests` EXIT=0. `python3 -m pip install -q -r requirements.txt` then `python3 -m unittest discover -s tests` **338 run / 338 OK / 0 failed / 1 skipped, EXIT=0**. `git status --short` clean. Frozen hashes unchanged: H004V106 canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; H10 fresh IMMATURE `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`. HEAD `6de84495a3a1800d9a40c03d290da8167dce408f`.
- **H10 status:** CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / EVALUATED_NULL_DIFF_IMMATURE (n_formations=1). k not advanced. **No confirmatory claim.**
- **Cutoff gate:** November 2026 BLOCKED. Last real probe `2026-11-07T09:11:52Z`. **Re-probe forbidden before 2026-11-30.**

### Prior task disposition (20261108T104200Z)
**COMPLETE.** Independently verified compileall, full unittest (338/338/0 EXIT=0), clean git status, and frozen hashes unchanged. Bounded no-cost search found no reproducible code/audit defect, missing reference guard, or outcome-impacting drift. No source/artifact/config change made.

### Immediate next action (explicit, executable)
1. **On/after 2026-11-30:** run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If usable, refresh required free public data; run the fresh sealed block only into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`). Use H10 prereg + k=1 alpha-spending. Record all outcomes, including confirmatory-gate fields.
2. **Before 2026-11-30:** act only if a genuine bounded no-cost gap is found. Otherwise record that no unblocked task exists and keep next action as (1). **Do not wait for a manually supplied experiment ID.**
3. **If verifying tests locally:** run `python3 -m pip install -r requirements.txt` first.

### Hard rules (non-negotiable)
- Never relax 30-day maturity, MIN_ASSETS_DECIMAL=20, trailing-decile rule, or 0.05 threshold.
- Never open canonical sealed holdout (`forward_block/`); fresh outputs go only to `forward_block_h10_fresh/` or a new uniquely identified path.
- Never use today's rank as historical truth. Never fabricate metrics. Preserve old artifacts/configs/results.
- Do not modify immutable closed preregistration/experiment records.
- Allocate unique IDs/preregister for new exploratory work. Keep confirmatory and exploratory tracks separate.
- A passing workflow/test proves only what it covers. No confirmatory claim from exploratory/integrity work.
- Follow adaptive research-gate policy v1: if a feasibility gate is durably blocked, do not loop; complete a bounded no-cost exploratory task only if one exists and record it, preserving blocked confirmatory status.
