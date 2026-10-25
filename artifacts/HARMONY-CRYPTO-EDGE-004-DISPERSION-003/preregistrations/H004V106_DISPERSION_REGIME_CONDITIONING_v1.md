# Preregistration — H9: Dispersion Regime Conditioning (DISP-003-REGIME-001)
Experiment ID: HARMONY-CRYPTO-EDGE-004-DISPRESSION-003-REGIME-001
Status: EXPLORATORY_ONLY
Date: 2026-10-25T21:15Z

## 1. Motivation (evidence that motivates this test)
The canonical H004V106 sealed forward block (608 formations, 2025-01-01..2026-08-31,
cutoff 2026-09-30) shows high_low_diff_net_1x = +0.6165, but the state-representativeness
audit (DISP-003-STATEAUDIT-001, H8) labels it CLUSTER_DOMINATED: the entire positive
estimate is carried by the 31 formations in calendar month 2025-10 (mean +1.046),
which are the ONLY high-state formations in that month, and dropping 2025-10 moves the
estimate to +0.093. High states occur in only 7 of 20 calendar months and none after
2025-11.

This is a measurement-feasibility finding on already-inspected development evidence.
It does NOT validate or refute H1/H6/H7 and does NOT unlock the confirmatory track.

## 2. Question
Is the positive high-minus-low spread concentrated in a *dispersion regime* (i.e. a
range of absolute dispersion levels) rather than in a calendar month? If the effect is
genuinely regime-driven, conditioning on dispersion level should show a consistent
pattern; if it is calendar-cluster noise, the pattern should collapse once 2025-10 is
removed.

## 3. Estimand and population
- Population: the 608 completed formations in the canonical sealed forward block
  (read-only; no frozen artifact modified).
- Sub-populations: terciles of the formation-level `dispersion` field, computed from
  the FULL 608-formation distribution (fixed, precomputed thresholds), NOT split
  within each month.
- Outcome: spread_net_1x per formation; contrast high vs low state within each
  dispersion tercile.

## 4. Predeclared decision rule (fixed before computation)
- Compute n_high, n_low, high_mean, low_mean, high_minus_low diff, and the
  spread_net_1x mean for each dispersion tercile, BOTH on the full block AND on the
  block with 2025-10 removed.
- Label REGIME_CONSISTENT if: (a) high states appear in >=2 terciles, and (b) the
  high-minus-low diff has the same sign in >=2 terciles that contain both high and
  low states, and (c) the sign is preserved after removing 2025-10.
- Otherwise label REGIME_INCONSISTENT.
- In ALL branches the status is EXPLORATORY_ONLY. No statistical significance test is
  performed; this is a descriptive/feasibility diagnostic.

## 5. Hard safeguards
- No look-ahead: dispersion tercile thresholds are computed from the formation-level
  dispersion field only; the outcome field is never used to define the regime.
- No forward-fill, no invented observations, no truncation.
- The canonical forward block is read-only; byte-identical after this run.
- No new market data fetched; no paid sources.
- This is exploratory diagnostic evidence on development data. It cannot serve as
  independent confirmation and cannot promote any hypothesis.

## 6. Output
New artifact: artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/
             H004V106_dispersion_regime_conditioning_20261025.json
New test: tests/test_dispersion_regime_conditioning.py