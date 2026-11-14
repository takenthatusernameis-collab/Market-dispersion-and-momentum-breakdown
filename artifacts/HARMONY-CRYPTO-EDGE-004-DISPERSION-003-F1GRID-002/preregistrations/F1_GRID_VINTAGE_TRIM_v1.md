# F1 Grid Vintage-Trim Sensitivity — DISP-003 Full Grid on F1-Repaired Panels, Ledger-Vintage Arm A

**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-002
**Hypothesis ID:** H27 (allocated in this session)
**Status:** PREREGISTERED (before computation)
**Created:** 2026-11-14T04:46:00Z
**Type:** EXPLORATORY_ONLY — descriptive candidate evaluation on development data

---

## 1. Purpose and trigger

DISP-003-F1GRID-001 (H26) attempted the full 216-cell F1 coverage-repair sensitivity contrast but aborted at its preregistered fidelity anchor: arm A on the *current* committed panels (kline/funding vintage ending 2026-10-31) cannot reproduce the frozen DISPERSION-003 `grid_result_ledger.json` (evaluated 2026-10-24T10:46:28Z, vintage ending 2026-09-30) within 1e-9. The same formation dates carry different forward windows across vintages (documented in `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-001/integrity_audit/f1_grid_execution_state_audit_2026-11-14T043410Z.json`, verdict `BLOCKED_FIDELITY_ANCHOR_UNSATISFIABLE`). No comparison was written and nothing was promoted.

This experiment implements path (a) of that audit's `next_test`: preregister a NEW EXPLORATORY_ONLY arm that trims the panel inputs to the frozen ledger's as-of date for **both** arms so that arm A reproduces the committed DISPERSION-003 grid ledger within 1e-9, then reports the arm B (F1-repaired kline panels) contrast on that **same vintage**.

## 2. Vintage trim (frozen, predeclared)

- **Trim date (inclusive):** `2026-09-30` (calendar date, UTC). All panel rows with a date/open-time/funding-calc-time strictly after 2026-09-30 23:59:59Z are excluded for both arms.
- **Rationale:** this matches the frozen ledger's panel vintage (committed marketcap/klines/funding as of end-September 2026) so arm A is an estimand-compatible reproduction of the committed grid ledger. The trim is applied to price, funding and marketcap inputs symmetrically.
- **Label:** results are **ledger-vintage (as-of 2026-09-30) EXPLORATORY_ONLY** development evidence. They are NOT comparable to the F1GRID-001 arm A checkpoint (current vintage), NOT a re-run of the frozen ledger, and NOT fresh confirmation. The current-vintage panels remain unchanged.

## 3. Inputs (read-only)

- **Committed panels:** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/` (read-only)
- **F1-repaired kline panels:** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001/data/panels/binance_klines_{1INCHUSDT,AAVEUSDT,ACHUSDT,AGLDUSDT}.csv` (read-only)
- **Grid manifest:** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/grid_config_manifest.json` (216 cells)
- **Committed grid ledger (fidelity target):** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/grid_result_ledger.json` (read-only)
- **Engine:** unmodified `scripts/run_dispersion003_grid.py` (same parameters/costs/gates: BASE_COST_TURN 0.0005, HOLM_ALPHA 0.05, MIN_ASSETS_DECILES 20, MIN_ASSETS_MEDIAN 4)

## 4. Arms and substitution rule

- **Arm A (ledger-vintage, committed panels):** committed panels trimmed to <= 2026-09-30. Fidelity anchor: must reproduce the committed DISPERSION-003 grid ledger within 1e-9 on every comparable cell/field (excluding `evaluated_utc`) **before** any arm B comparison is written. On fidelity failure the script aborts and writes no comparison.
- **Arm B (ledger-vintage, F1-repaired klines):** same as arm A with only the four F1-repaired **kline** panels overriding the committed versions in memory. Funding panels are NOT substituted (F1COVERAGE-001 repaired klines only). All other inputs/parameters/costs/rules identical.

## 5. Evaluation and outputs

For each of 216 manifest cells in each arm: formation loop (completed UTC daily bars only, trailing momentum -> dispersion state -> portfolio -> forward spread -> cost-adjusted net), terminal status OK/BLOCKED/INVALID/FAILED/NOT_RUN, two-sided block-bootstrap p-value on high/low net-1x series (block_len=21, n_boot=1000), Holm step-down across all 216 cells per arm for the registered 1x net endpoint.

Outputs (under this experiment root only, never in the committed DISP-003 tree): `grid_checkpoints/`, `grid_result_ledger.json`, `grid_summary.json`, `integrity_audit/`.

## 6. Preregistered descriptive contrasts (no promotion)

For cells OK in both arms: Δ n_formations, Δ n_high/n_low/n_mid, Δ high_low_diff_net_1x, Δ spread means/medians, Δ eligible assets, Holm-rejection changes. Labels: DIRECTIONAL_ATTENUATION, COVERAGE_EXPANSION, HOLM_STATUS_CHANGE, ANCHOR_HOLM_CHANGE (H004V106), COMPARATOR_HOLM_CHANGE (H004V105).

No statistical inference, no promotion, no hypothesis conclusion. EXPLORATORY_ONLY on already-inspected development data. Bootstrap p-values/Holm are descriptive contrast only — not a confirmation family.

## 7. Safeguards

- No network; no new market data fetched.
- Read-only: committed panels, F1COVERAGE-001 panels, grid manifest, committed ledger and all frozen DISP-003 artifacts are never modified.
- Arm A fidelity to committed ledger is a hard gate (1e-9). Single-cell pre-check: H004V002 at formation 2026-09-29 must yield `spread_gross` 0.0 and match the ledger.
- No sealed holdout opened; 30-day outcome maturity rule unchanged; no truncated outcomes.
- DISPERSION-001/002 and frozen DISPERSION-003 artifacts/configs/inputs untouched.

## 8. Next test (if pursued)

If material grid changes appear, confirmation requires a genuinely fresh, mature sealed forward block (formations after 2026-09-29) with complete multiple-testing correction under a NEW experiment ID. Never treat this ledger-vintage development sensitivity as confirmation.
