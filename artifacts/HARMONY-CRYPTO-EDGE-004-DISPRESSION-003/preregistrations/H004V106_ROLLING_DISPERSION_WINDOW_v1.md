# Preregistration — H004V106 Rolling Dispersion-Window Robustness (DISP-003-REGIME-002)

- **Program**: HARMONY-CRYPTO-EDGE-004 DISPERSION-003
- **Experiment ID**: HARMONY-CRYPTO-EDGE-004-DISPERSION-003-REGIME-002
- **Preregistered**: 2026-10-28T17:00Z
- **Status**: EXPLORATORY_ONLY (development data only; no fresh holdout; cannot validate/refute H1/H6/H7/H8)
- **Trigger**: H8 (DISP-003-STATEAUDIT-001) `next_test`: "If the mechanism is cluster-driven, test whether it survives (a) a rolling/adaptive shorter dispersion reference window and (b) conditioning on the 2025-10 dispersion regime, each under a NEW preregistered experiment ID on development data only." Branch (b) was executed as REGIME-001 (2026-10-28T16:21:40Z). This preregistration covers branch (a), the only remaining unexecuted branch of H8's next_test.

## Motivation
The canonical H004V106 forward block's +0.617 high-minus-low estimate is CLUSTER_DOMINATED by the 2025-10 calendar month (31 of 61 high formations). The anchor's dispersion-state rule uses a 365-day trailing reference window to set the outer-decile thresholds. If the positive mean is an artifact of that long window averaging over the 2025-10 extreme, shortening the reference window should make the estimate unstable (sign flip or collapse). If the mechanism is robust, the sign should survive across windows. This is a predeclared sensitivity test of the *state construction*, not a parameter search for a winner.

## Data
Read-only canonical sealed forward block:
`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`
608 formations, 2025-01-01..2026-08-31, cutoff 2026-09-30. The per-formation `dispersion` and `spread_net_1x` values are frozen and untouched. Only the state-label assignment is recomputed with shorter trailing windows. No frozen artifact is modified.

## Predeclared analyses (all descriptive/exploratory; no inference claims)

The anchor state rule (from `scripts/eval_forward_block.py`) assigns state by comparing each formation's `dispersion` against the 10th/90th percentiles of the trailing dispersion series up to (but not including) the current formation, capped at `dispersion_window_days` observations. Here we re-run that assignment with a fixed set of reference windows and compare.

### Windows
W in {30, 90, 180, 270, 365} days. W=365 reproduces the anchor exactly and serves as the internal control.

### Per-window metrics
For each W, using only formations whose state is high or low (mid excluded, matching the anchor's high-minus-low estimand):
- n_high, n_low
- mean spread_net_1x for high and low states
- high_low_diff_net_1x = mean_high - mean_low
- 2025-10 leave-one-out: high_low_diff_net_1x recomputed with 2025-10 formations excluded, and the delta fraction vs the full-window estimate.

### Per-window label (predeclared, no post-hoc tuning)
- If n_high < 5 OR n_low < 5: `SPARSE`.
- Else if high_low_diff_net_1x > 0: `SIGN_POSITIVE`.
- Else if high_low_diff_net_1x < 0: `SIGN_NEGATIVE`.
- Else: `SIGN_ZERO`.

### Overall robustness label (predeclared)
- `ROLLING_ROBUST` if: every window with adequate sample (n_high>=5 and n_low>=5) is `SIGN_POSITIVE`, AND for every such window the 2025-10 leave-one-out delta fraction is within [-0.50, +0.50] of the full-window estimate.
- `ROLLING_FRAGILE` otherwise (sign instability, zero/crossing estimate, or 2025-10 sensitivity beyond 50% in any adequate window).

## Decision rules (predeclared, no post-hoc tuning)
- All analyses are EXPLORATORY_ONLY. No result here can promote a hypothesis, unlock the confirmatory track, or be cited as independent confirmation.
- A genuinely fresh sealed forward block with formations after 2026-09-29 remains required for any confirmatory claim.
- The W=365 row must reproduce the canonical +0.6165223953929935 exactly; if it does not, the script has a bug and the run is invalid.

## Exclusions
- None. All 608 formations are used; no outcome-informed exclusions.
- Formations with fewer than 30 prior dispersion observations cannot be assigned a state under W=30; those formations are simply mid (excluded from the high-minus-low estimand) in that window only, exactly as the anchor handles short histories. This is a data-availability property, not an exclusion chosen to improve results.