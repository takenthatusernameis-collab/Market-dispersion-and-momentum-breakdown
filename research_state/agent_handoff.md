# Agent Handoff — HARMONY-CRYPTO-EDGE-004-DISPERSION-002

## Status
- Prior experiment HARMONY-CRYPTO-EDGE-004-DISPERSION-001: archived as complete (verified). No further work authorized on those artifacts.
- New experiment HARMONY-CRYPTO-EDGE-004-DISPERSION-002: initialized; grid manifest generated (108 configs H004F001..H004F108). Data panels populated; phases C-G executed; outputs generated.
- Config: configs/dispersion_momentum_followup_v1.json
- Artifacts: artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/ (experiment_setup.json, grid_config_manifest.json, phase outputs, formation_returns_conditioned.csv, expanding_rank_frontier.json)

## Controls
- free-data-only, point-in-time universe, no-lookahead, chronological OOS.

## Commit
- HEAD: c049cf9 (main).

## Validation
- Adapted tests for DISPERSION-002 (grid size 108, H004F series, anchor H004F033 matches manifest; data pipeline validates universe/conditioned formation/phase summaries). All tests pass (10 passed).

## Verification (agent: kilo-auto/free)
- Re-ran full test suite: `python -m pytest tests/ -v` -> 10 passed, 0 failed (0.35s).
- Confirmed artifact set present: experiment_setup.json, grid_config_manifest.json (108 configs H004F001..H004F108), phase_c_summary.json, phase_e_summary.json, phase_f_summary.json, expanding_rank_frontier.json, formation_returns_conditioned.csv (53 rows), data/panels/*.
- Confirmed config configs/dispersion_momentum_followup_v1.json matches manifest; anchor H004F033 resolves correctly.
- git status: clean except untracked tests/__pycache__/; HEAD 8f13fd8 on main.

## Task for next agent
DISPERSION-002 validation is complete and verified. No further test fixes needed.

If additional robustness checks or reporting are requested, build on the existing phase summaries and conditioned formation returns:
- artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/phase_c_summary.json (dispersion-conditioned momentum, high/mid/low states, block bootstrap CIs)
- artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/phase_e_summary.json (realistic costs, turnover, funding PnL, 1x/2x/3x net)
- artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/phase_f_summary.json (chronological OOS discovery/validation/final split, 60/20/20)
- artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/expanding_rank_frontier.json (rank-band diagnostics)
- artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/formation_returns_conditioned.csv (per-formation inputs)

Do not re-run or modify the grid manifest, config, or data pipeline unless a new experiment ID is issued. Preserve controls: free-data-only, point-in-time universe, no-lookahead, chronological OOS.

---

# Initial Task Message for Next Agent

**Experiment:** HARMONY-CRYPTO-EDGE-004-DISPERSION-002 (follow-up to DISPERSION-001, archived/complete)
**Your role:** Continue this research thread from the durable handoff.

## What is already done (do not redo)
- 108-config grid (H004F001..H004F108) generated and manifest-verified; config at `configs/dispersion_momentum_followup_v1.json`.
- Data panels populated; phases C (dispersion-conditioned), D (expanding rank frontier), E (realistic costs/turnover/funding), F (chronological OOS 60/20/20 split) executed; outputs in `artifacts/HARMONY-CRYPTO-EDGE-004-DISPRESSION-002/`.
- All 10 tests pass (`python -m pytest tests/ -v`). Validation is complete.

## Key findings so far
- Phase C (anchor H004F033): high-dispersion gross mean +0.1196 vs low-dispersion gross mean -0.0551; high-low diff +0.1747 (block-boot CI [0.1747, 0.1747]). Mid state ~ +0.0056. n_high=6, n_low=8, n_mid=39 of 53 formations.
- Phase E: net-of-cost means degrade by ~0.001 per leverage unit (1x/2x/3x); high state stays positive net even at 3x (+0.1166), low state goes more negative (-0.0581). Turnover = 2.0 per rebalance (full leg replacement), funding PnL included with historical sign approximation.
- Phase F (OOS): discovery arm (n=31) shows high-low diff +0.2877 (high +0.2078, low -0.0798); validation (n=11) diff +0.0079; final (n=11) diff -0.0050 with only 1 high / 1 low observation. Small tail samples limit OOS inference.
- Phase D: expanding rank frontier shows diff turns positive at the 1-20 and 1-28 bands (+0.104, +0.175) but is negative at 1-10 (-0.102) and 1-15 (-0.055).

## Your task (if pursuing further work)
1. Decide whether the dispersion-momentum effect is robust enough to report, or whether the thin OOS tail (n_high=1 in final/validation) means it should be flagged as underpowered.
2. Optionally: run additional robustness (e.g., alternative dispersion state rules, different lookback/forward horizons from the 108-config grid) or produce a consolidated report/summary of the experiment.
3. If you modify anything, keep the free-data-only, point-in-time, no-lookahead, chronological-OOS controls intact and do not touch the grid manifest/config unless issuing a new experiment ID.

## How to verify
- `python -m pytest tests/ -v` (should stay green)
- Inspect `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/` and `configs/dispersion_momentum_followup_v1.json`.

When done, update `research_state/agent_handoff.md` with your findings and the next agent's task message.
