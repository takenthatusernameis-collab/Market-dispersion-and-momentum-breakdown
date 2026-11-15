# Preregistration — H004V106 Forward Block Independent Recomputation Audit (DISP-003-RECOMPUTE-001)

**Program:** HARMONY-CRYPTO-EDGE-004
**Experiment ID:** H004V106_FORWARD_BLOCK_INDEPENDENT_RECOMPUTATION_AUDIT
**Status:** EXPLORATORY_ONLY
**Created:** 2026-11-15T13:00:00Z
**Author:** automated research agent (this session)

## 1. Why this audit exists (gap)

The addendum `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/forward_block_independent_recomputation_20261028.json` records an independent recomputation of the sealed canonical forward block (`forward_block/forward_block_evaluation.json`, sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`, n_formations=608, high_low_diff_net_1x=+0.6165223953929935). Its conclusion states MATCH=True against the canonical values, but no committed artifact independently recomputes those metrics *from the canonical block's formations array* and compares them against the addendum's recorded numbers. Four test surfaces (`test_state_consistency.py`, `test_preregistration_completeness.py`, `test_preregistration_coverage_audit.py`, `scripts/audit_preregistration_coverage.py`) all treat it as an addendum with no hypothesis id, no preregistration, no script and no seam tests. This is a specific, not-yet-covered question: does the recorded addendum reproduce when the metrics are recomputed independently from the canonical block?

## 2. Question and estimand

**Question:** Given only the sealed canonical forward block (formed from point-in-time data, cutoff 2026-09-30, last formation 2026-08-31, 30-day completed horizons, no truncated outcomes), do its 608 formation records independently recompute to the same n_formations, state_counts, finite flags and metrics recorded in the addendum, within tolerance?

**Estimand:** A deterministic, consistency-only recomputation of each metric from the canonical block's `formations` array (mean, median, per-state means, high-low difference, finite checks) compared against the addendum's recorded values, within an absolute tolerance of 1e-9 for means and 1e-12 for the difference-of-means. No outcomes are produced beyond this consistency check; no market data is re-fetched; no sealed holdout is opened.

## 3. Method (frozen before computation)

1. Load the canonical forward block `forward_block_evaluation.json` and verify its recorded sha256 equals `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` (computed from the committed blob itself).
2. Verify `block_sealed=true`, `data_cutoff_utc=2026-09-30T00:00:00Z`, `date_last=2026-08-31`, `anchor_id=H004V106`, `n_formations=608`.
3. Recompute from the `formations` array (each record `{dispersion, formation_date, n_assets, spread_gross, spread_net_1x, state}`):
   - n_formations = len(formations); state_counts per state (high/mid/low).
   - spread_net_mean/median, spread_gross_mean/median.
   - high_net_mean (mean of spread_net_1x where state=="high"), low_net_mean (mean where state=="low").
   - high_low_diff_net = high_net_mean − low_net_mean; high_low_diff_gross analogously for spread_gross.
   - finite checks: all spread_net_1x and spread_gross finite.
4. Load the addendum `forward_block_independent_recomputation_20261028.json`.
5. Compare each recomputed metric against the addendum's recorded `metrics` and `state_counts`, using tolerance 1e-9 absolute for means and 1e-12 absolute for high_low_diff_net/gross; n_formations and state_counts must match exactly.
6. Record PASS/FAIL per check with exact expected vs actual values; overall verdict PASS iff every check matches.
7. No writes to any frozen artifact; read-only across the board; stdlib only; no network.

## 4. Decision rule (predeclared)

- Overall verdict PASS: every check matches within tolerance; n_formations and state_counts exact.
- Overall verdict FAIL: any check deviates beyond tolerance.
- Result is EXPLORATORY_ONLY/consistency_only: it neither validates nor replaces any confirmatory track, cannot produce a high_low_diff_net_1x claim for confirmation, does not change the frozen H10 preregistration or date gate, and does not modify any frozen artifact. It is a reproducibility cross-check of an existing addendum against its source block.

## 5. Safeguards (not relaxed)

- Read-only; no writes to any frozen artifact/config/input/frontier/registry/sealed holdout.
- No look-ahead, no fabrication, no forward-fill, no outcome-informed parameters, no synthetic market data.
- The canonical block is the *source of truth*; the addendum is what is being checked against it, not the other way around.
- Tolerances predeclared: 1e-9 absolute for means, 1e-12 absolute for differences of means; exact match for n_formations and state_counts.
- n_high=61, n_low=90 states are read from the block, never imposed; the small high-state sample is noted as a stability consideration but does not alter the consistency conclusion.

## 6. Expected output

- Audit artifact under `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/H004V106_forward_block_independent_recomputation_<timestamp>.json`
- Preregistration record here.
- Registry entry H37 (next_sequence_number 36->37).
- Hermetic seam tests covering all pure functions in the audit script.
