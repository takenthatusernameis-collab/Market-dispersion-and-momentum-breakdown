# Preregistration — H10 Post-2026-11-30 Evaluation Sequence Design (DISP-003-H10-POST-2026-11-30)

**Program:** HARMONY-CRYPTO-EDGE-004
**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-H10-POST-2026-11-30
**Status:** EXPLORATORY_ONLY
**Created:** 2026-11-15T13:24:00Z
**Author:** automated research agent (this session)

## 1. Why this design artifact exists (gap)

H35 (`H004V106_H10_MATURITY_TIMELINE_AUDIT`) decomposes the H10 fresh block's maturity into ordered milestones (M1 first mature look, M2 magnitude estimable, M3 confirmatory claim) and derives the exact in-block formation-count requirements and earliest cutoffs from frozen implementation constants and merged-index geometry. H35 concludes M1 requires >=32 in-block daily formations (earliest cutoff estimate ~2026-12-01) and that the November 2026 vintage cutoff (2026-11-30) yields only 31 in-block / 1 classifiable formation, so M1 is impossible at that cutoff. H35 is a static geometry audit of the current immature block; it does not define *what sequence of evaluations* should run once the block matures, nor does it declare the look-counter progression, alpha-spending schedule per look, Holm family binding, or the expected-artifact contract for each look in the sequence.

This design artifact fills that gap: it is a planning-only, pre-computation specification of the evaluation sequence that should execute on/after the November 2026 vintage publishes (cutoff >= 2026-11-30), once the fresh sealed block contains enough formations for high/low classification. No outcomes, returns, spreads, p-values or inference are computed. No frozen artifact, panel, grid ledger, forward block, cost model or decision rule is modified.

## 2. Question and estimand

**Question:** Given the frozen H10 fresh block artifact (`forward_block_h10_fresh/forward_block_evaluation.json`, sha256 `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`) and the H10 preregistered decision rules (economic significance threshold 0.05, state-count floor n_high>=5 AND n_low>=5, sequential alpha rule alpha_k = 0.05/(k*(k+1)), Holm across the complete 216-cell family), what is the predeclared sequence of evaluations (look numbers k=1,2,...), the per-look alpha_k values, the cumulative alpha spend remaining after each look, the Holm-adjusted p-value comparison rule, and the artifact contract each evaluation must write, such that any confirmatory claim on a mature fresh block is fully predeclared and cannot be re-argued from the raw outcome?

**Estimand:** A deterministic, predeclared evaluation-sequence specification: ordered look numbers, per-look alpha levels, cumulative spend trajectory, Holm family binding, pass/fail decision rules per look, and the exact artifact fields each evaluation must emit. No market outcomes are estimated.

## 3. Evaluation sequence (predeclared, frozen before any mature outcome)

The fresh sealed block is re-evaluated each calendar month as the Binance archive publishes (November 2026, December 2026, ...), with data cutoff advancing to the latest published month-end. Each evaluation that produces an outcome (n_high>0 AND n_low>0, high_low_diff_net_1x non-null) advances the look counter k; an IMMATURE evaluation (n_high=0 or n_low=0, high_low_diff_net_1x=null) does not advance k and consumes no alpha budget.

- **Look k=1 (first mature evaluation):** alpha_1 = 0.05/(1*2) = 0.025. Cumulative spend = 0.025. Remaining budget = 0.025. Confirmatory claim requires BOTH (a) |high_low_diff_net_1x| >= ECONOMIC_SIGNIFICANCE_THRESHOLD (0.05) after costs AND (b) Holm-adjusted p-value across the complete 216-cell family <= alpha_1 (0.025). The Holm family is unchanged and always spans all 216 cells; alpha-spending only sets the per-look significance level.
- **Look k=2 (second mature evaluation, next calendar month if k=1 did not confirm):** alpha_2 = 0.05/(2*3) = 0.05/6 ≈ 0.008333. Cumulative spend = 0.025 + 0.05/6 ≈ 0.033333. Remaining budget = 0.05 - cumulative_spend ≈ 0.016667. Confirmatory claim requires BOTH (a) and (b) evaluated at alpha_2.
- **Look k>=3:** alpha_k = 0.05/(k*(k+1)). Cumulative spend = 0.05*(1 - 1/(k+1)). Series sums to 0.05 over k=1..inf. Each look's confirmatory claim is gated on its own alpha_k.
- **Immature evaluation (any look):** n_high=0 or n_low=0 or high_low_diff_net_1x=null → does not advance k, consumes no budget, artifact records overlap_aware_uncertainty.status=IMMATURE and confirmatory_claim_allowed=false.

## 4. Method (frozen before computation)

1. On/after 2026-11-30, probe the cutoff gate (`python3 scripts/probe_cutoff_gate.py --probe-month <month>`); require target_published=true before refreshing.
2. Refresh free public data (`python3 scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>`), free public data only.
3. Re-run the full test suite (`python3 -m unittest discover -s tests`); require all OK.
4. Verify the canonical H004V106 forward block is byte-unchanged vs `git show HEAD:` (sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`).
5. Run the fresh sealed block into `forward_block_h10_fresh/` (never `forward_block/`): `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new cutoff> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh --look-number <k>`. The no-op branch preserves evaluated_utc and all outcome fields when nothing changes.
6. Require n_high>0 AND n_low>0 before any confirmatory claim; if IMMATURE, record the blocker and do not advance k.
7. For each mature look: compare |high_low_diff_net_1x| to 0.05 (criterion 4a) and compare the Holm-adjusted p-value across the 216-cell family to alpha_k (criterion 4b). Confirmatory claim only if BOTH hold at the current look's alpha_k.
8. Record every look's result (PASS/FAIL per criterion, expected vs actual, k, alpha_k, cumulative_spend, remaining_budget, consumes_budget) in a timestamped artifact under integrity_audit/. Frozen hashes (canonical block, H10 fresh block, grid ledger, universe frontier, grid v3 config) must be unchanged.

All steps are pure functions of committed artifacts and constants plus read-only panel index reads. Stdlib-only, no network for computation, no market-data re-fetch, no outcome computation beyond the evaluator's own sealed-block output.

## 5. Decision rule (predeclared)

- Overall verdict PASS for a look: criterion 4a (|high_low_diff_net_1x| >= 0.05 after costs) AND criterion 4b (Holm-adjusted p-value <= alpha_k across the 216-cell family) both hold at the current look's alpha_k.
- Overall verdict FAIL for a look: either criterion deviates.
- IMMATURE evaluation: not PASS or FAIL; recorded as IMMATURE, k not advanced, no budget consumed.
- Result is EXPLORATORY_ONLY: a planning/design specification on already-inspected development evidence. It does NOT validate, replace or unlock H1/H6/H7/H10/H11, does not change the frozen H10 preregistration or the 2026-11-30 data-availability gate, and does not modify any frozen artifact, panel, grid ledger, forward block, cost model or decision rule.
- The 0.05 economic threshold is never lowered to manufacture a pass and is never re-derived from the fresh block's outcome; the canonical block is NOT an input to the fresh block's outcome.

## 6. Safeguards (not relaxed)

- Read-only; no writes to any frozen artifact/config/input/frontier/registry/sealed holdout.
- No look-ahead, no fabrication, no forward-fill, no outcome-informed parameters, no synthetic market data.
- The evaluation sequence is declared BEFORE any mature outcome exists, so it cannot be outcome-informed.
- The November 2026 vintage gate (cutoff >= 2026-11-30) is not relaxed; do not re-probe November 2026 before 2026-11-30.
- Do not relax 30-day maturity, MIN_ASSETS_DECILES=20, the trailing-decile state rule, the family alpha, the Holm family, or the state-count floor.

## 7. Expected output

- Preregistration record here (this file).
- Design artifact under `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/H004V106_H10_post_2026_11_30_evaluation_sequence_<timestamp>.json`.
- Registry entry H36 (next_sequence_number 35->36).
- Matching contract-test updates in tests/test_continuous_research_contract.py, tests/test_preregistration_completeness.py, tests/test_preregistration_coverage_audit.py, tests/test_integrity_audit_reference_consistency.py, scripts/audit_preregistration_coverage.py.
