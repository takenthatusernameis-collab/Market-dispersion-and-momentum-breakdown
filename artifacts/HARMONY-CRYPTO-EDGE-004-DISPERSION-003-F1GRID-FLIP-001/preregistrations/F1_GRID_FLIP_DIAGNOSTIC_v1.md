# F1 Grid Holm-Status Flip Diagnostic — DISP-003 F1GRID-002 Sole Coverage-Sensitivity Flip

**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-FLIP-001
**Hypothesis ID:** H45 (allocated in this session)
**Status:** PREREGISTERED (before computation)
**Created:** 2026-11-17T07:36:00Z
**Type:** EXPLORATORY_ONLY — descriptive coverage-sensitivity diagnostic on already-inspected development data

---

## 1. Purpose and trigger

H44 (DISP-003-F1GRID-002) executed the ledger-vintage (as-of 2026-09-30) 216-cell
sensitivity contrast between arm A (committed panels trimmed to the frozen ledger
vintage) and arm B (the same panels with the four F1COVERAGE-001-repaired kline
panels substituted). Its committed `grid_summary.json` records
`aggregate_labels.HOLM_STATUS_CHANGE = True` and `holm_rejected_count` 0 (arm A)
vs 1 (arm B), i.e. exactly one of the 216 cells changes Holm rejection status
between the two arms.

No committed artifact characterises that single flip: which cell it is, how large
the point-estimate move is relative to the predeclared economic-significance
threshold, how many formation state-buckets changed, and whether the status change
is a marginal significance-threshold crossing or a material change in the effect.
This experiment fills that bounded, read-only gap. It is EXPLORATORY_ONLY
descriptive analysis of already-inspected development data; it does not promote,
confirm, or unlock any confirmatory track, and it does not re-open the sealed
forward block.

## 2. Inputs (read-only)

- **F1GRID-002 result ledger:** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-002/grid_result_ledger.json`
  (arms `A_ledger_vintage_committed` and `B_ledger_vintage_f1_repaired`, 216 cells each; read-only).
- **F1GRID-002 summary:** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-002/grid_summary.json`
  (cross-check of the flip set; read-only).
- **Economic-significance threshold:** `0.05` (the predeclared H10 net-1x economic
  threshold already recorded in `research_state/run_manifest.json`
  `h10_economic_significance_threshold_declaration_20261107T0628Z`; reused here as a
  descriptive scale, NOT as a promotion gate).

No network access, no market data fetched, no panels rebuilt.

## 3. Method (predeclared, deterministic)

`analyze_ledger(ledger)` is a pure function over the committed ledger dict:

1. For every `config_id` present in both arms, read `high_low_diff_net_1x`,
   `pvalue_bootstrap_two_sided`, `holm_rejected`, `n_formations`, `n_high`,
   `n_low`, `n_mid`.
2. A cell is a **flip cell** iff `holm_rejected` differs between arms.
3. For each flip cell compute:
   - `delta_net = B.high_low_diff_net_1x - A.high_low_diff_net_1x`
   - `delta_p = B.pvalue - A.pvalue`
   - `delta_n_high / delta_n_low / delta_n_mid`
   - `n_state_transfers = sum of positive (delta_n_high, delta_n_low, delta_n_mid)`
     (the number of formations that moved into a different state bucket; a single
     low->mid reclassification gives `delta_n_low=-1, delta_n_mid=+1,
     n_state_transfers=1`)
   - `relative_net_change = abs(delta_net) / max(abs(A.net), 1e-12)`
   - `classification`:
     - `SIGN_FLIP` if `sign(A.net) != sign(B.net)` and both are non-zero
     - `MATERIAL_POINT_ESTIMATE_CHANGE` if `abs(delta_net) >= 0.05`
     - `MARGINAL_POINT_ESTIMATE_CHANGE` otherwise
4. Emit the flip set, per-cell diagnostics, the economic threshold used, and an
   overall `verdict`.

## 4. Predeclared descriptive claims (no promotion)

- The number of flip cells `n_flips` is reported as observed; no threshold is
  placed on it.
- Each flip cell is labelled `MARGINAL_POINT_ESTIMATE_CHANGE`,
  `MATERIAL_POINT_ESTIMATE_CHANGE` or `SIGN_FLIP` by the rule above.
- `n_state_transfers` is reported so a reader can see whether the status change is
  attributable to a single formation reclassification.
- **No p-value promotion, no multiple-testing family claim, no economic claim.**
  The bootstrap p-values and Holm flags in the source ledger are descriptive
  contrasts on inspected development data, not confirmation.

## 5. Outputs

Under this experiment root only: `integrity_audit/f1_grid_flip_diagnostic_<computed_utc>.json`
carrying `experiment_id`, `audit_id`, `audited_artifact`, `computed_utc`,
`preregistration`, `method`, `economic_threshold`, `n_flips`, `flip_cells`,
`verdict`, `exploratory_only=true`, `promotion_allowed=false`.

## 6. Safeguards

- Read-only: the F1GRID-002 ledger/summary and every frozen DISP-003 artifact,
  panel, grid ledger and forward block are never modified.
- No sealed holdout opened; no 30-day maturity rule relaxed; no truncated outcomes.
- DISPERSION-001/002 and frozen DISPERSION-003 artifacts/configs/inputs untouched.
- The analysis reads committed artifacts only; it does not recompute the grid.

## 7. Next test (if pursued)

If the sole flip proves to be a marginal significance crossing with a negligible
point-estimate move, the correct conclusion is that the F1 coverage repair does not
materially change the family's economic conclusions; confirmation of any economic
claim still requires a genuinely fresh, mature sealed forward block under a new
experiment ID. Never treat this ledger-vintage development diagnostic as
confirmation.