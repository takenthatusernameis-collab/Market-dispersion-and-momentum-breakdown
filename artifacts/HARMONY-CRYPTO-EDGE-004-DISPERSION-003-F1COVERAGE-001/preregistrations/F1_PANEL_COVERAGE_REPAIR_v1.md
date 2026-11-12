# Preregistration — F1 Panel-Coverage Repair (DISP-003-F1COVERAGE-001)

**Program:** HARMONY-CRYPTO-EDGE-004
**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001
**Hypothesis (registry):** H23
**Status:** EXPLORATORY_ONLY (in progress at creation)
**Created:** 2026-11-12T17:26:07Z
**Author:** automated research agent (this session)

## 1. Why this experiment exists (trigger)

`research_state/DISP_003_PANEL_COVERAGE_LINEAGE_AUDIT_20261112T162052Z.json`
(F1/F2) found that four of the 32 committed DISPERSION-003 panel symbols —
`1inch`, `aave`, `ach`, `agld` — have **no Binance klines or funding monthly
archives for 2025-01 .. 2026-09** (21 months x 2 series x 4 symbols = 168
zips). The same symbols resume in 2026-10 and their market-cap series is present
across the whole gap, so this is a raw-archive acquisition gap, not a delisting.
Because the canonical H004V106 forward block was estimated on 26-27 assets, this
is the attribution behind the reduced eligible-asset count.

The lineage audit explicitly recommends, as the next bounded no-cost step, that a
future session fetch only those 168 keyless zips into a **new** raw directory and
rebuild **new** panels, never overwriting the sealed inputs. This preregistration
executes that recommendation under a new experiment ID and new artifact paths.

## 2. Estimand (descriptive coverage only — NOT an outcome)

This experiment measures **input coverage**, not any return, spread, state
classification or statistical test. The estimands are:

1. **Coverage completeness.** After repair, each of the four symbols has a
   continuous Binance klines and funding series over 2023-01 .. 2026-10 with no
   interior month gap in 2025-01 .. 2026-09.
2. **Eligible-asset count delta.** For every date in the market-cap panel, the
   number of assets satisfying the canonical eligibility rule (non-null
   `CapMrktEstUSD` on the date AND a Binance kline observation on the date AND a
   Binance funding observation on the date) under the original panels versus the
   repaired panels.
3. **Canonical-block-window distribution.** The distribution of eligible-asset
   counts across the formation dates of the sealed canonical H004V106 block
   (2025-01-01 .. 2026-08-31) under original versus repaired panels.

No spread, state, p-value or economic claim is computed. This is EXPLORATORY_ONLY
descriptive evidence. It does **not** validate, replace, unlock or re-run any
frozen experiment, and it does not recompute any test statistic.

## 3. Method (frozen before any fetch or computation)

1. Read the on-disk raw-archive month set for the four symbols and identify the
   missing months in 2025-01 .. 2026-09 (expected: 21 per symbol per series).
2. Fetch only those missing keyless monthly zips from the free Binance Public
   Data Archive:
   - klines: `https://data.binance.vision/data/futures/um/monthly/klines/<SYM>/1d/<SYM>-1d-<YYYY-MM>.zip`
   - funding: `https://data.binance.vision/data/futures/um/monthly/fundingRate/<SYM>/<SYM>-fundingRate-<YYYY-MM>.zip`
   Write them into
   `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001/data/raw/binance/{klines,funding}/<SYM>/`.
   Record HTTP status, row count and SHA-256 for every zip. A 404 is recorded as
   `missing` (never synthesized); any non-404 error is recorded and retried with
   bounded backoff. Do not fetch months already present on disk.
3. Rebuild the four symbols' panels from the fetched zips into
   `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001/data/panels/`
   using the canonical headers and the same chronological, header-stripping
   logic as `scripts/rebuild_binance_panels.py`. Never write to the committed
   `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/`.
4. Recompute the eligibility map with the same rule as
   `scripts/run_dispersion003_grid.py::build_eligibility_map`
   (asset = `<SYMBOL without USDT>`.lower(); cap non-null on date AND kline date
   AND funding date), using the committed `marketcap_panel.csv` (read-only) plus
   the original panels and the repaired panels.
5. Emit a single artifact
   `integrity_audit/f1_panel_coverage_repair_<UTC>.json` recording: per-zip status
   and hash, rebuilt panel row counts and date ranges, original-versus-repaired
   eligible-asset counts per date (or the summary distribution), the
   canonical-block-window distribution, and explicit verification that the
   committed panels/raw zips/frozen artifacts are byte-unchanged.

## 4. Decision rule (predeclared)

- **PASS** if all 168 expected zips are fetched `ok` (or an already-present
  on-disk zip covers the month), all four panels rebuild with no interior
  2025-01..2026-09 gap, the repaired eligible-asset count on every date is
  `>=` the original count (coverage never decreases), and every committed input
  and frozen artifact hash is unchanged.
- **PARTIAL** if any month is `missing` (genuine 404): record the exact missing
  months, keep the achieved coverage, and do not synthesize or forward-fill.
- **FAIL** if the repair reduces coverage, alters any committed panel/raw zip, or
  cannot be reproduced.

In all branches the result is EXPLORATORY_ONLY. It cannot promote H1/H6/H7/H10 or
any other hypothesis, and it does not re-open the sealed canonical block.

## 5. Safeguards (never relaxed)

- No overwriting of `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/` or
  any frozen artifact; new ID and new paths only.
- Free public data only; no credentials, no paid source, no network endpoints
  other than `data.binance.vision`.
- No look-ahead, no forward-fill, no synthetic rows, no silent exclusions, no
  fabricated fills. Missing months are recorded as missing.
- Point-in-time cap only: today's rank is never backfilled as historical rank.
- No outcome, spread, state, cost, grid or inference computation is performed.
- This is a source-coverage repair, not a hypothesis test; the frozen 003 block,
  panels, findings and hashes stay byte-unchanged.

## 6. Expected output

- New raw zips under the new experiment's `data/raw/binance/`.
- Rebuilt panels for the four symbols under the new experiment's `data/panels/`.
- `integrity_audit/f1_panel_coverage_repair_<UTC>.json` with coverage deltas.
- `tests/test_f1_panel_coverage_repair.py` regression guard.
- Registry entry H23 (next_sequence_number 22 -> 23); handoff and task-message
  update.

## 7. Change log

- 2026-11-12T17:26:07Z — created before any fetch or computation. No grid,
  hypothesis conclusion, cost model, parameter or frozen artifact changed.