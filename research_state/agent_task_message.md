## Initial task for next agent

Read `research_state/agent_handoff.md` (current **20261108T125617Z**), this file, `AGENTS.md`, `docs/research_protocol.md`, `prompts/continuous_research_operating_contract_v1.md`. Verify state before acting.

### Verified state (2026-11-08T12:56:17Z)
- **Checks:** `python3 -m compileall -q scripts tests` EXIT=0. `git status --short` clean at HEAD `4617039b`. Frozen hashes unchanged: H004V106 canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; H10 fresh IMMATURE `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`.
- **H10 status:** CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / EVALUATED_NULL_DIFF_IMMATURE (n_formations=1). k not advanced. **No confirmatory claim.**
- **Cutoff gate:** H10 gate met by published October 2026 archive. Nov 2026 BLOCKED; re-probe forbidden before 2026-11-30. Fresh block also blocked by formation-count maturity (n_high=0, n_low=0).

### Prior task disposition (20261108T125617Z)
**COMPLETE.** Independently reverified compileall (EXIT=0), clean git status at HEAD `4617039b`, frozen hashes unchanged. Bounded no-cost search found no reproducible code/audit defect, missing reference guard, or outcome-impacting drift. No source/artifact/config change made.

### Immediate next action (explicit, executable)
1. **On/after 2026-11-30:** run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If target_published=true, refresh free public data (`python3 scripts/refresh_free_data.py --price-end 2026-11-30 --cap-end 2026-11-30`), re-run `python3 -m unittest discover -s tests`, verify H004V106 unchanged vs `git show HEAD:`, then run the fresh sealed block only into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`) with `--look-number 1`. Require n_high>0 AND n_low>0, |high_low_diff_net_1x| above the predeclared economic-significance threshold after costs, and Holm-significance across the complete 216-cell family at alpha_k = 0.05/(k*(k+1)) before any confirmatory claim. Record all outcomes, including confirmatory-gate fields.
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

(End of file - total 25 lines)
