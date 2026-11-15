# Preregistration: H004V106 H10 Fresh Forward Block Integrity Audit

**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003
**Hypothesis ID:** H31
**Created:** 2026-11-15T07:30:00Z
**Status:** PREREGISTERED (before any computation)

## Objective
Perform a read-only internal-consistency audit of the committed H10 fresh sealed forward block artifact at `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json` (operative sha256 `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`). The audit verifies that the block's own summary fields, formation records, state counts, and input-file hashes are internally consistent with the on-disk panel data and with each other.

## Scope
- **Audited artifact:** `forward_block_h10_fresh/forward_block_evaluation.json` (sealed, IMMATURE block with `n_formations=1`, `n_high=0`, `n_low=0`, `n_mid=1`, formation date `2026-09-30`, `data_cutoff_utc=2026-10-31T00:00:00Z`)
- **Inputs:** Binance klines/funding panel CSVs under `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/`, `marketcap_panel.csv`, `grid_config_manifest.json`, `grid_result_ledger.json`
- **No frozen artifacts are modified.** This is an EXPLORATORY_ONLY integrity audit of already-inspected development evidence. It does NOT validate, refute, unlock, or promote H10 (which requires a mature fresh block with `n_high>0` AND `n_low>0`).

## Predeclared Decision Rules
1. **Input-hash reconciliation:** Recompute SHA-256 of every file listed in the block's `input_file_hashes` on disk. Report per-file match/mismatch. Mismatches are EXPECTED for panel files that have been appended since the block was sealed (October 2026 data). The block's own sha256 and its outcome fields must remain byte-unchanged.
2. **Formation record consistency:** The single formation record (`2026-09-30`, `n_assets=26`, `state=mid`, `dispersion=0.19716600141456223`, `spread_gross=-0.047729065266337745`, `spread_net_1x=-0.048729065266337745`) must match the recomputed values from the same pipeline (within 1e-9 tolerance for floats).
3. **Summary field consistency:** Top-level fields (`n_formations`, `n_high`, `n_low`, `n_mid`, `date_first`, `date_last`, `eligible_assets_per_date`, `data_cutoff_utc`, `last_allowed_formation_date`, `block_sealed`, `block_sealing_rule`, `sequential_look_number`, `sequential_alpha_k`, `sequential_cumulative_spend`, `sequential_remaining_budget`, `min_state_formations`, `state_count_floor_met`, `economic_significance_threshold`, `economic_significance_met`, `confirmatory_claim_allowed`, `min_completed_forward_horizon_days`) must be internally consistent with the formation records and with each other.
4. **Finite-value check:** The formation's `dispersion`, `spread_gross`, `spread_net_1x` must be finite (not NaN/inf).
5. **Cost treatment:** `spread_net_1x == spread_gross - COST_1X` (0.001) within 1e-12.
6. **State assignment consistency:** With `n_high=0` and `n_low=0`, `high_low_diff_net_1x` and `high_low_diff_gross` must be `null`. `high_gross_mean`, `low_gross_mean`, `high_net_1x_mean`, `low_net_1x_mean` must be `null`. The single formation's state `mid` must be consistent with the trailing-decile rule (requires ≥30 prior in-block dispersions; not met here).
7. **Overlap-aware uncertainty:** The `overlap_aware_uncertainty` section must have `status=IMMATURE`, `reason="need n_high>0 and n_low>0 for overlap-aware interval"`, `n_high=0`, `n_low=0`, `n_clusters_with_both_states=0`.

## Pass Criteria
All of the above checks pass (mismatches in input-hash reconciliation for panel files are explicitly NOT a failure criterion; they are documented expected signals).

## Artifacts Produced
- `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/H004V106_H10_fresh_forward_block_integrity_audit_<timestamp>.json`

## Interpretation
This audit describes internal consistency of the H10 fresh forward block (an already-inspected, IMMATURE development artifact). It cannot validate, replace, or unlock the confirmatory track (H1/H6/H7/H10). The H10 fresh block remains IMMATURE; the next authorized action is waiting for the November 2026 vintage to mature (`n_high>0` AND `n_low>0`).