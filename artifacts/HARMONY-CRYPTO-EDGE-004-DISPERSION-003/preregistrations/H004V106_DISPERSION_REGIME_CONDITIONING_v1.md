# Preregistration — H004V106 Dispersion-Regime Conditioning (DISP-003-REGIME-001)

- **Program**: HARMONY-CRYPTO-EDGE-004 DISPERSION-003
- **Experiment ID**: HARMONY-CRYPTO-EDGE-004-DISPERSION-003-REGIME-001
- **Preregistered:** 2026-10-26T01:05:19Z (commit 1a6b8fd; see correction note below)
- **Status**: EXPLORATORY_ONLY (development data only; no fresh holdout; cannot validate/refute H1/H6/H7/H8)
- **Correction note (2026-10-30T17:15Z):** The declared `Preregistered` time
(2026-10-26T01:15:00Z) is 9 minutes 41 seconds **after** the document's
commit time (commit 1a6b8fd, 2026-10-26T01:05:19Z), so it cannot be the
file's true creation time. It is corrected above to the commit time, the
earliest verifiable repository timestamp. This is a **prospective**
preregistration: it was authored before the audit artifact it describes
(`integrity_audit/H004V106_dispersion_regime_conditioning_20261028.json`,
computed 2026-10-28T16:21:40Z) was run, so the pre-declared decision rule
predates the computation. The only defect was the backdated header
timestamp; the audit artifact, script (`scripts/dispersion_regime_conditioning.py`)
and test (`tests/test_dispersion_regime_conditioning.py`) were NOT
regenerated or altered to fit this document, and the audit's decision rule
is unchanged.
- **Trigger**: H8 (DISP-003-STATEAUDIT-001) `next_test`: "If the mechanism is cluster-driven, test whether it survives (a) a rolling/adaptive shorter dispersion reference window and (b) conditioning on the 2025-10 dispersion regime, each under a NEW preregistered experiment ID on development data only."

## Motivation
The canonical H004V106 forward block's +0.617 high-minus-low estimate is CLUSTER_DOMINATED by the 2025-10 calendar month (31 of 61 high formations; dispersion ~5x the rest of the block). Before concluding the dispersion-state mechanism is non-representative, we test whether the *level* of dispersion itself predicts the spread, i.e. whether the high/low state label is merely a coarse proxy for a continuous dispersion-spread relationship.

## Data
Read-only canonical sealed forward block:
`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`
608 formations, 2025-01-01..2026-08-31, cutoff 2026-09-30. No frozen artifact modified.

## Predeclared analyses (all descriptive/exploratory; no inference claims)

### A. Continuous dispersion-spread association
- Compute Pearson and Spearman correlation between `dispersion` and `spread_net_1x` over all 608 formations.
- Repeat with 2025-10 excluded (n=577).
- Predeclared interpretation rule: if |r| >= 0.30 after excluding 2025-10, label CONTINUOUS_ASSOCIATION_PRESENT; else WEAK_CONTINUOUS_ASSOCIATION.

### B. Dispersion-regime split (H8 next_test (b))
- Split formations into two regimes by the full-block median of `dispersion`.
- Within each regime compute: n, n_high, n_low, mean spread_net_1x, and high-minus-low diff (where high/low states exist).
- Predeclared interpretation rule: if the high-minus-low diff has the same sign in both regimes and both regimes contain >= 10 high AND >= 10 low formations, label REGIME_ROBUST; else REGIME_SPARSE / SIGN_FLIP.

### C. 2025-10 conditioning
- Compute the high-minus-low diff with 2025-10 formations *included* vs *excluded*.
- Predeclared interpretation rule: report the delta fraction vs baseline (+0.6165) descriptively; no label change (this reproduces H8's leave-one-out finding and is recorded only to anchor the conditioning analysis).

### D. Dispersion quantile-bucket profile
- Bucket formations by decile of `dispersion` (full block).
- Per bucket: n, n_high, n_low, mean spread_net_1x.
- Predeclared interpretation rule: report descriptively; look for monotonicity of mean spread across dispersion deciles.

## Decision rules (predeclared, no post-hoc tuning)
- All four analyses are EXPLORATORY_ONLY. No result here can promote a hypothesis, unlock the confirmatory track, or be cited as independent confirmation.
- A genuinely fresh sealed forward block with formations after 2026-09-29 remains required for any confirmatory claim.

## Exclusions
- None. All 608 formations are used; no outcome-informed exclusions.