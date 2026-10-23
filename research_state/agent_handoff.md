# Agent Handoff — HARMONY-CRYPTO-EDGE-004-DISPERSION-002

## Status
- Prior experiment HARMONY-CRYPTO-EDGE-004-DISPERSION-001: archived as complete (verified). No further work authorized on those artifacts.
- New experiment HARMONY-CRYPTO-EDGE-004-DISPERSION-002: initialized; grid manifest generated (108 configs H004F001..H004F108). Data panels populated; phases C-G executed; outputs generated.
- Config: configs/dispersion_momentum_followup_v1.json
- Artifacts: artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/ (experiment_setup.json, grid_config_manifest.json, phase_c_summary.json, phase_e_summary.json, phase_f_summary.json, expanding_rank_frontier.json, formation_returns_conditioned.csv, data/panels/*)

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
- git status: clean except untracked tests/__pycache__/; HEAD c049cf9 on main.

## Findings (DISPERSION-002)
- Phase C (anchor H004F033): high-dispersion gross mean +0.1196 vs low-dispersion gross mean -0.0551; high-low diff +0.1747 (block-boot CI [0.1747,0.1747]). Mid ~ +0.0056. n_high=6, n_low=8, n_mid=39 of 53 formations.
- Phase E: net-of-cost means degrade ~0.001 per leverage unit (1x/2x/3x); high stays positive net even at 3x (+0.1166), low more negative (-0.0581). Turnover 2.0 per rebalance, funding PnL included (historical sign approx).
- Phase F (OOS, 60/20/20): discovery (n=31) high-low diff +0.2877 (high +0.2078, low -0.0798); validation (n=11) +0.0079; final (n=11) -0.0050 with only 1 high / 1 low. Thin tails limit OOS inference.
- Phase D: expanding rank frontier diff positive at 1-20 (+0.104) and 1-28 (+0.175), negative at 1-10 (-0.102) and 1-15 (-0.055).

## Task for next agent
DISPERSION-002 validation complete and verified. Tests pass.

Recommended next steps (pick one or combine):
1. **Report/Consolidate**: Produce a consolidated experiment report (summary.md/report.md) synthesizing C/D/E/F findings, noting OOS power/robustness caveats (thin high/low tails, especially final fold).
2. **Robustness checks** (if requested): Test alternative dispersion state rules/lookbacks/horizons across the 108-config grid (H004F001..H004F108), keeping free-data-only/point-in-time/no-lookahead/chronological OOS. Do not modify grid manifest/config without issuing a new experiment ID.
3. **Tighten inference**: Quantify fold stability / effective sample sizes and explicitly flag regimes with n<5 in any state before drawing strong conclusions.

Preserve controls. Build on existing artifacts only:
- artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/phase_c_summary.json
- artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/phase_e_summary.json
- artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/phase_f_summary.json
- artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/expanding_rank_frontier.json
- artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/formation_returns_conditioned.csv

Do not re-run/modify grid manifest, config, or data pipeline unless a new experiment ID is issued.

## Verification command
- `python -m pytest tests/ -v` (must stay green)
