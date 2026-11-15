# Preregistration — H10 Fresh Forward Block Maturity-Timeline Milestone Audit (DISP-003-H10-MATURITY)

**Program:** HARMONY-CRYPTO-EDGE-004
**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-H10-MATURITY
**Status:** EXPLORATORY_ONLY
**Created:** 2026-11-15T12:30:00Z
**Author:** automated research agent (this session)

## 1. Why this audit exists (gap)

The H10 fresh sealed forward block (`forward_block_h10_fresh/forward_block_evaluation.json`, sha256 `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`) is IMMATURE (`n_formations=1`, `n_high=0`, `n_low=0`, `last_allowed_formation_date=2026-09-30`). Two prior audits cover adjacent ground: H31 (`H004V106_H10_FRESH_FORWARD_BLOCK_INTEGRITY_AUDIT`) recomputed the single formation's metrics, and H34 (`H004V106_H10_FRESH_FORWARD_BLOCK_PREREG_COMPLIANCE_AUDIT`) verified the artifact encodes the preregistered decision rules. Neither decomposes *when* the block can first satisfy each maturity condition, and the durable handoff repeatedly states only a coarse "H10 cannot advance before 2026-11-30" date gate. No committed artifact derives the exact maturity predicate or the earliest calendar cutoff from the frozen implementation constants. This is a specific, not-yet-covered question.

## 2. Question and estimand

**Question:** Given the frozen implementation constants (`MIN_PRIOR_DISPERSIONS=30`, `MIN_STATE_FORMATIONS=5`, `ECONOMIC_SIGNIFICANCE_THRESHOLD=0.05`, `COST_1X=0.001`, `forward_horizon_days=30`) and the committed merged daily panel index, (a) how many in-block daily formations are required for each maturity milestone, (b) what is the earliest calendar data cutoff at which the first mature look (M1) becomes possible, and (c) does the November 2026 vintage (cutoff 2026-11-30) suffice for M1?

**Estimand:** A deterministic decomposition of the H10 fresh-block maturity into three ordered milestones, each with its exact formation-count requirement and earliest-cutoff derivation, plus confirmation that the current alpha-spending budget is unconsumed. No outcomes, returns, spreads, p-values or inference are computed.

## 3. Milestones (derived from the frozen implementation)

The frozen state rule `assign_trailing_decile_states` (scripts/eval_forward_block.py) classifies a formation as high/low only when at least `MIN_PRIOR_DISPERSIONS` strictly prior in-block dispersions exist; otherwise it is `mid`. The formation loop seals the block to `last_allowed = cutoff_index - forward_horizon_days` (merged-index positions), and formations occur on essentially every merged-index date (the canonical block holds 608 daily formations from 2025-01-01 to 2026-08-31).

- **M1 — first mature look (`n_high>0 AND n_low>0`; advances the look counter k):** the first classifiable formation is the `(MIN_PRIOR_DISPERSIONS+1)`-th in-block formation; a mature look additionally needs one high and one low, i.e. at least two classifiable formations. **Necessary condition:** `in_block_formations >= MIN_PRIOR_DISPERSIONS + 2 = 32`. With `in_block = cutoff_index - horizon - block_start_index + 1`, this requires `cutoff_index >= block_start_index + MIN_PRIOR_DISPERSIONS + horizon + 1` (an index offset of 61 positions from the block start 2026-09-30).
- **M2 — magnitude estimable (`n_high >= MIN_STATE_FORMATIONS AND n_low >= MIN_STATE_FORMATIONS`):** a *descriptive* order-of-magnitude estimate only. Under outer-decile classification roughly 10% of classifiable formations fall in each tail, so ~`MIN_STATE_FORMATIONS/0.1` classifiable formations are needed for each tail, i.e. ~80 in-block formations total. The exact count is data-dependent (depends on the realized dispersion sequence) and cannot be fixed before the dispersions are observed; the hard necessary lower bound is `MIN_PRIOR_DISPERSIONS + 2*MIN_STATE_FORMATIONS = 40` (loose, since high+low cannot both reach the floor with only a few classifiable formations).
- **M3 — confirmatory claim:** M2 AND `|high_low_diff_net_1x| >= ECONOMIC_SIGNIFICANCE_THRESHOLD` AND Holm-significance across the complete 216-cell family at the per-look `alpha_k`. Not reachable until M2.

## 4. Method (frozen before computation)

1. Load the committed H10 fresh block artifact and the merged daily panel index (from the committed Binance kline panels; the block start 2026-09-30 and the last observed date 2026-10-31 are read from the panel, not assumed).
2. Verify the current block state matches the artifact (`n_formations=1`, `n_high=0`, `n_low=0`, `block_sealed=true`, `sequential_look_mature=false`, `sequential_look_consumes_budget=false`, `economic_significance_met=false`, `state_count_floor_met=false`, `confirmatory_claim_allowed=false`).
3. Compute, from the frozen constants and the merged-index geometry, the in-block formation count at the current cutoff and at the November-vintage cutoff (2026-11-30), the classifiable count at each, the M1 necessary formation count, the M1 cutoff index offset, and the earliest M1 calendar-cutoff estimate.
4. Confirm the alpha-spending budget is unconsumed: `sequential_look_number=1`, `alpha_k=0.025`, `cumulative_spend=0.025`, `remaining_budget=0.025`, `consumes_budget=false`.
5. Verify the frozen hashes (canonical forward block, H10 fresh block, grid result ledger, universe frontier, grid v3 config) are unchanged.
6. Record PASS/FAIL per check with exact expected vs actual values; overall verdict PASS iff every check matches.

All checks are pure functions of the committed artifact and constants (plus a read of the committed kline panel index for the cadence check). Stdlib-only, no network, no market-data re-fetch, no outcome computation.

## 5. Decision rule (predeclared)

- Overall verdict PASS: every check in section 4 matches exactly.
- Overall verdict FAIL: any check deviates.
- Result is EXPLORATORY_ONLY: a planning/diagnostic on already-inspected development evidence. It does NOT validate, replace or unlock H1/H6/H7/H10/H11, does not change the frozen H10 preregistration or the 2026-11-30 data-availability gate, and does not modify any frozen artifact, panel, grid ledger, forward block, cost model or decision rule.

## 6. Safeguards (not relaxed)

- Read-only; no writes to any frozen artifact/config/input/frontier/registry/sealed holdout.
- No look-ahead, no fabrication, no forward-fill, no outcome-informed parameters, no synthetic market data.
- The M2/M3 formation counts are labelled approximate where they depend on unrealized dispersions; only M1's necessary formation count and index offset are exact.
- The November-vintage sufficiency conclusion is derived from the observed merged-index geometry (31 dates in 2026-09-30..2026-10-31 with the 2026-10-28 archive gap) and the daily cadence; it is a necessary-condition statement, not a guarantee that M1 fires exactly at the earliest cutoff.

## 7. Expected output

- Audit artifact under `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/H004V106_H10_maturity_timeline_<timestamp>.json`
- Preregistration record here.
- Registry entry H35 (next_sequence_number 34->35).
- Hermetic seam tests covering all pure functions in the audit script.