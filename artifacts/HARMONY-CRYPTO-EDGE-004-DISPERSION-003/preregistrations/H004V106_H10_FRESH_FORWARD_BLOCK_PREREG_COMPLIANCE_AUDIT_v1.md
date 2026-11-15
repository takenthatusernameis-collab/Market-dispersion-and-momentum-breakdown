# Preregistration — H10 Fresh Forward Block Preregistration Compliance Audit (DISP-003-H10-PRECOMP)

**Program:** HARMONY-CRYPTO-EDGE-004
**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-H10-PRECOMP
**Status:** EXPLORATORY_ONLY
**Created:** 2026-11-15T10:47:00Z
**Author:** automated research agent (this session)

## 1. Why this audit exists (gap)

The H10 fresh forward block artifact (`forward_block_h10_fresh/forward_block_evaluation.json`, sha256 `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`) was evaluated on 2026-11-02 and repaired on 2026-11-07 to add confirmatory gate fields. The prior audit H31 (`H004V106_H10_FRESH_FORWARD_BLOCK_INTEGRITY_AUDIT`) verified internal consistency of the single formation record but did NOT verify that the artifact's confirmatory gate fields, decision logic, and sequential look tracking correctly implement the preregistered decision rules from `preregistrations/H10_FRESH_FORWARD_BLOCK_v1.md` (sections 4, 4.1, 4.2). This is a specific, not-yet-covered verification gap.

## 2. Question and scope

**Question:** Does the committed H10 fresh forward block artifact correctly encode the preregistered confirmatory decision rules (economic significance threshold, state count floors, alpha-spending rule, look counter semantics, confirmatory claim logic) as declared in H10_FRESH_FORWARD_BLOCK_v1.md?

**Scope:** Read-only verification of the committed artifact against the preregistration text. No new data, no re-evaluation, no outcome computation. The artifact is EXPLORATORY_ONLY development evidence (evaluated 2026-11-02, already inspected); this audit cannot validate, replace or unlock any confirmatory track.

## 3. Method (frozen before computation)

1. Load the committed H10 fresh forward block artifact: `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json`
2. Load the preregistration: `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H10_FRESH_FORWARD_BLOCK_v1.md`
3. Verify the following preregistered decision rules are correctly reflected in the artifact:

### 3.1 Economic significance threshold (section 4.2)
- `economic_significance_threshold` == 0.05
- `economic_significance_met` == false (since |high_low_diff_net_1x| is null)
- `high_low_diff_net_1x_abs` == null (since high_low_diff_net_1x is null)
- Endpoint is net-of-cost: confirm `spread_net_1x = spread_gross - 0.001` for the single formation

### 3.2 State count floor (section 4.2)
- `min_state_formations` == 5
- `state_count_floor_met` == false (n_high=0, n_low=0)
- Confirm `n_high >= 5 AND n_low >= 5` is required for a magnitude claim

### 3.3 Confirmatory claim logic (section 4)
- `confirmatory_claim_allowed` == false (immature block)
- `confirmatory_holm_significant` == null
- `confirmatory_note` contains the three gates: economic threshold, state count floor, Holm at alpha_k
- A confirmatory claim requires ALL three true; never promoted from raw p-values or return alone

### 3.4 Sequential alpha-spending rule (section 4.1)
- `sequential_alpha_rule` == "alpha_k = 0.05 / (k * (k + 1))"
- `sequential_family_alpha` == 0.05
- `sequential_look_number` == 1
- `sequential_alpha_k` == 0.025 (alpha_1 = 0.05 / (1 * 2))
- `sequential_cumulative_spend` == 0.025
- `sequential_remaining_budget` == 0.025
- `sequential_look_consumes_budget` == false (immature evaluation consumes no budget)
- `sequential_look_mature` == false
- `sequential_look_note` explains look counter semantics correctly

### 3.5 Block maturity and sealing
- `block_sealed` == true
- `block_sealing_rule` correctly describes 30-day maturity exclusion
- `n_formations` == 1, `n_high` == 0, `n_low` == 0, `n_mid` == 1
- `high_low_diff_net_1x` == null
- `overlap_aware_uncertainty.status` == "IMMATURE"
- `overlap_aware_uncertainty.reason` == "need n_high>0 and n_low>0 for overlap-aware interval"

### 3.6 Frozen hash verification
- Canonical H004V106 forward block sha256 == `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`
- H10 fresh block sha256 == `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`
- Grid result ledger sha256 == `0184f2d3e5d63dc6fb23a45f0ddfb226a195324d153615588c6c1363a74ce04c`
- Universe frontier sha256 == `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e`

4. All checks are pure functions, stdlib-only, no network, no market data.
5. Record PASS/FAIL per check with exact expected vs actual values.
6. Overall verdict: PASS if all predeclared checks pass; FAIL otherwise.

## 4. Decision rule (predeclared)

- Overall verdict PASS: every check in section 3 matches exactly.
- Overall verdict FAIL: any check deviates.
- Result is EXPLORATORY_ONLY: this is a compliance diagnostic on already-inspected development evidence. It does NOT validate, replace or unlock H1/H6/H7/H10/H11 and does not change any economic conclusion. No frozen artifact, panel, grid ledger, forward block, cost model or decision rule is modified.

## 5. Safeguards (not relaxed)

- Read-only; no writes to any frozen artifact/config/input/frontier/registry/sealed holdout.
- No look-ahead, no fabrication, no outcome-informed parameters.
- The H10 fresh block remains IMMATURE (n_high=0, n_low=0) and awaits the November 2026 data vintage for maturity.

## 6. Expected output

- Audit artifact under `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/H004V106_H10_fresh_forward_block_prereg_compliance_audit_<timestamp>.json`
- Preregistration record here.
- Registry entry H34 (next_sequence_number 33->34).
- Hermetic seam tests covering all pure functions in the audit script.