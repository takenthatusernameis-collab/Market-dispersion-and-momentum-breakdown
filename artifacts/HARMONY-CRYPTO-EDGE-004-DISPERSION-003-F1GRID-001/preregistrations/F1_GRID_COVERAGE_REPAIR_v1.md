# F1 Grid Coverage Repair — DISPERSION-003 Full Grid on Repaired Panels

**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-001
**Hypothesis ID:** H26 (to be allocated)
**Status:** PREREGISTERED (before computation)
**Created:** 2026-11-13T23:00:00Z
**Type:** EXPLORATORY_ONLY — candidate evaluation on development data

---

## 1. Purpose

The F1COVERAGE-001 repair (H23) re-acquired four symbols (1INCHUSDT, AAVEUSDT, ACHUSDT, AGLDUSDT) missing from the committed DISPERSION-003 Binance archive for 2025-01..2026-09. The repair raised the descriptive eligible-asset count on the canonical H004V106 formation dates from 26–27 to 29–31.

F1SENS-002 (H24) measured the point-estimate sensitivity of the frozen H004V106 anchor only: arm A (committed panels) high_low_diff_net_1x = +0.617 → arm B (four F1-repaired klines overriding) high_low_diff_net_1x = +0.540, delta = -0.077. The overlap-aware 95% CI on arm B includes zero.

F1STAB-003 (H25) confirmed that the H8 leave-one-month-out CLUSTER_DOMINATION and H19 median-date TEMPORAL-INSTABILITY warnings persist under the 29–31-asset repair.

**This experiment runs the complete 216-cell DISPERSION-003 sensitivity grid on the F1-repaired panel set** (original committed panels with the four F1-repaired kline panels substituted). This measures whether the full grid's sensitivity surface — every cell's formation count, state counts, high/low spreads, and Holm-adjusted inferences — changes when the four repaired assets are added. No p-value, multiple-testing family, or promotion is computed; this is descriptive sensitivity evidence only.

---

## 2. Methodology (locked before computation)

### 2.1 Inputs (read-only)
- **Committed panels:** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/` (32 assets, 64 CSVs)
- **F1-repaired kline panels:** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001/data/panels/binance_klines_{1INCHUSDT,AAVEUSDT,ACHUSDT,AGLDUSDT}.csv` (4 CSVs)
- **Marketcap panel:** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/marketcap_panel.csv` (unchanged)
- **Grid manifest:** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/grid_config_manifest.json` (216 cells, H004V001–H004V216)
- **Cost model:** BASE_COST_TURN = 0.0005, COST_STRESS = {1: 1x, 2: 2x, 3: 3x}
- **Gates:** MIN_ASSETS_DECILES = 20, MIN_ASSETS_MEDIAN = 4, HOLM_ALPHA = 0.05

### 2.2 Panel substitution rule
Arm A (baseline): committed panels exactly as-is.
Arm B (F1-repaired): committed panels with the four F1-repaired **kline** panels overriding the committed versions. Funding panels are NOT substituted (F1COVERAGE-001 only repaired klines; funding was already present).
All other inputs, parameters, costs, and rules are identical.

### 2.3 Evaluation
For each of the 216 cells in the grid manifest:
1. Load the panel set (Arm A or Arm B)
2. Build point-in-time eligibility maps for both universe arms (`legacy28_comparator` and `expanding_point_in_time`)
3. Run the formation loop (completed UTC daily bars only, trailing momentum → dispersion state → decile/median-split portfolio → forward spread → cost-adjusted net return)
4. Apply the trailing-window outer-deciles or median-split state rule per cell
5. Record terminal result: OK / BLOCKED / INVALID / FAILED / NOT_RUN with reason
6. Compute two-sided block-bootstrap p-value on high/low dispersion-state net-1x series (block_len=21, n_boot=1000)
7. Apply Holm step-down across all 216 cells for the registered 1x net endpoint

### 2.4 Outputs (per arm)
- Cell checkpoint ledger (incremental, resumable)
- Grid result ledger with all 216 cells
- Grid summary with primary anchors (H004V105 legacy, H004V106 expanding)
- Per-formation records for cells with status OK

### 2.5 Primary descriptive contrasts
For each cell that is OK in both arms:
- Δ n_formations, Δ n_high, Δ n_low, Δ n_mid
- Δ high_low_diff_net_1x, Δ spread_net_1x_mean, Δ spread_net_1x_median
- Δ eligible_assets_per_date (mean/min/max)
- Whether Holm rejection status changes

Aggregate summaries:
- Number of cells changing status (OK→BLOCKED, BLOCKED→OK, etc.)
- Distribution of Δ high_low_diff_net_1x across cells
- Whether the primary anchor H004V106 (expanding) and H004V105 (legacy) change Holm rejection status

---

## 3. Preregistered decision rules (descriptive only)

| Contrast | Label |
|----------|-------|
| Arm B high_low_diff_net_1x moves toward zero vs Arm A for >50% of OK cells | DIRECTIONAL_ATTENUATION |
| Arm B eligible-asset mean increases by ≥2 for >50% of formation dates | COVERAGE_EXPANSION |
| Any cell changes Holm rejection status (rejected↔not rejected) | HOLM_STATUS_CHANGE |
| Primary anchor H004V106 (expanding) changes Holm rejection status | ANCHOR_HOLM_CHANGE |
| Primary anchor H004V105 (legacy) changes Holm rejection status | COMPARATOR_HOLM_CHANGE |

No statistical inference, no promotion, no hypothesis conclusion. This is EXPLORATORY_ONLY development evidence on already-inspected data. The canonical DISPERSION-003 panels, raw archive, frozen forward blocks, and grid ledger are never modified.

---

## 4. Safeguards

- **No network:** reuses already-fetched F1 panels on disk.
- **Read-only verification:** SHA-256 of all committed panels and frozen artifacts verified unchanged before and after computation.
- **Fidelity anchor:** Arm A must reproduce the committed DISPERSION-003 grid ledger within 1e-9 on all fields for every cell. If fidelity fails, the script aborts and writes no comparison.
- **No frozen artifact modification:** the canonical grid_result_ledger.json, grid_summary.json, forward_block/, forward_block_h10_fresh/, DISPERSION-001/002, and defective archive are byte-verified unchanged.
- **No p-value promotion:** bootstrap p-values and Holm rejections are computed for descriptive contrast only; they do not validate or refute H1/H6/H7/H8/H9/H10.

---

## 5. Next test (if pursued)

If the grid sensitivity reveals material changes (e.g., ANCHOR_HOLM_CHANGE or widespread DIRECTIONAL_ATTENUATION), a confirmatory evaluation on a **genuinely fresh, mature sealed forward block** (formations after 2026-09-29) with complete multiple-testing correction would be required under a NEW experiment ID. Never treat this development-data sensitivity as confirmation.

---

## 6. Artifact paths

- **Experiment root:** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-001/`
- **Preregistration:** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-001/preregistrations/F1_GRID_COVERAGE_REPAIR_v1.md`
- **Script:** `scripts/run_f1_grid.py`
- **Outputs:** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-001/grid_checkpoints/`, `grid_result_ledger.json`, `grid_summary.json`
- **Test:** `tests/test_f1_grid_coverage_repair.py`

---

*End of preregistration. Computation must not begin until this document is committed.*