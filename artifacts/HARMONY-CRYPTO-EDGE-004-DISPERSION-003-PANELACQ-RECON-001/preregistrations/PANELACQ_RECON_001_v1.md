# Panel-Acquisition Coverage Reconciliation — PANELACQ-PROBE-001 404 Gaps vs PANELCOV-FEAS-001 Feasibility

**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-RECON-001
**Hypothesis ID:** H46 (allocated in this session)
**Status:** PREREGISTERED (before computation)
**Created:** 2026-11-18T03:51:00Z
**Type:** EXPLORATORY_ONLY — descriptive source-coverage reconciliation on already-inspected committed artifacts

---

## 1. Purpose and trigger

Two committed exploratory artifacts stand in unresolved tension:

- **H40 (PANELCOV-FEAS-001)** concluded `PANEL_EXTENSION_FEASIBLE_IN_PRINCIPLE`.
  Its per-asset records assume the full `expected_zip_files_upper_bound` (92 =
  46 months x 2 kinds) is acquirable for every candidate asset, and its
  `interpretation` states it "does not claim per-symbol monthly archive
  publication."
- **H43 (PANELACQ-PROBE-001)** then empirically keyless-HEAD-probed all 920
  H41-planned monthly `(symbol, kind, month)` archive entries and found
  **889 served (HTTP 200), 31 absent (HTTP 404), 0 errors**. All 31 absences are
  concentrated in three of the ten priority gap-filler assets: ARK, ALPHA, ASTR.

No committed artifact reconciles the two: it does not distinguish which of the
31 absent files are **benign pre-listing gaps** (the archive serves nothing
before the contract existed, so the H40 "in principle" verdict is unaffected)
from **genuine mid-/trailing-series gaps** (a file that should exist inside the
asset's live window is absent, which would make the H41 acquisition plan
incomplete for that asset). The H41 plan itself carries
`provenance_status: PENDING_ACQUISITION` and `published_verified: null` for every
entry, so it cannot self-classify.

This experiment fills that bounded, read-only, no-cost gap. It is EXPLORATORY_ONLY
descriptive analysis of already-inspected committed artifacts; it performs no
network access, downloads no content, constructs no panels, computes no
returns/spreads/states/p-values/costs/inference, and does not promote, confirm,
or unlock any confirmatory track. It does not re-open the sealed forward block
or re-probe the date-gated `2026-11` cutoff month.

## 2. Inputs (read-only)

- **H41 acquisition plan:**
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001/integrity_audit/H004V106_panel_acquisition_plan_20261116T085222Z.json`
  (920 `plan_entries` with `symbol`, `kind`, `month`, `asset`; read-only).
- **H43 source-coverage probe:**
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PROBE-001/integrity_audit/H004V106_panel_archive_probe_20261116T142247Z.json`
  (920 `per_entry` records with `http_status`; read-only).
- **H40 feasibility study (context only, read-only):**
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-FEAS-001/integrity_audit/H004V106_panel_coverage_extension_feasibility_20261116T215857Z.json`
  (supplies each asset's `required_study_months` and `cap_first_in_window` /
  `cap_last_in_window`; read-only).

No market data fetched. No panels rebuilt. No sealed holdout opened.

## 3. Method (predeclared, deterministic)

`reconcile(plan_entries, probe_entries, feasibility_per_asset)` is a pure
function over the committed artifacts:

1. **Join integrity check.** Assert the plan and probe share an identical
   `(symbol, kind, month)` key set (920 each, zero plan-only, zero probe-only).
   A mismatch is a hard failure (`JOIN_MISMATCH`), not a silent drop.
2. **Absent-set extraction.** The absent set is every probe entry with
   `http_status != 200` (i.e. 404). Errors (`http_status` null with an `error`)
   are reported separately and never counted as absent-without-reason.
3. **Per-`(asset, kind)` window classification.** For each `(asset, kind)` group
   with at least one served file, let `first_served` / `last_served` be the min /
   max `month` among HTTP-200 entries. Classify each absent month `m` as:
   - `BEFORE_FIRST_SERVED` if `m < first_served` (pre-listing gap: the archive
     serves nothing earlier, so H40's "in principle" verdict is unaffected);
   - `AFTER_LAST_SERVED` if `m > last_served` (trailing gap: the series stops
     before the study-window end, so the asset's live window is truncated);
   - `INTERIOR` if `first_served <= m <= last_served` (mid-series gap: a hole
     inside the live window, the most serious case).
   A group with **zero** served files (all absent) is labelled
   `ENTIRELY_ABSENT` and is the strongest blocker signal.
4. **Aggregate roll-up.** Report, per asset: `n_404`, the classification
   breakdown, `n_served`, `first_served`, `last_served`, `required_study_months`
   count and `cap_first_in_window`. Report the overall reconciliation verdict
   from the predeclared rule in section 5.

The classification uses only month-string ordering (`YYYY-MM` sorts lexically),
which is exact for zero-padded year-month. It does not impute, fabricate, or
backfill any absent file.

## 4. Predeclared descriptive claims (no promotion)

- The absent set size and its classification split are reported exactly as
  observed; no threshold is placed on them.
- The reconciliation verdict is one of the labels in section 5.
- **No p-value, no multiple-testing family, no economic claim, no feasibility
  upgrade/downgrade is promoted.** The H40 "feasible in principle" verdict is
  neither overturned nor confirmed here; this audit only *locates* which absent
  files are benign (pre-listing) versus which would make a future acquisition
  incomplete (trailing/interior/entirely-absent), so a future bounded,
  preregistered acquisition step knows exactly which files it must resolve.

## 5. Predeclared verdict rule (outcome-blind)

- `RECONCILIATION_FULLY_BENIGN` — every absent file is `BEFORE_FIRST_SERVED`
  (all 404s are pre-listing; H40's in-principle verdict is untouched).
- `RECONCILIATION_HAS_COVERAGE_GAPS` — at least one absent file is
  `AFTER_LAST_SERVED`, `INTERIOR`, or in an `ENTIRELY_ABSENT` group (a genuine
  gap a future acquisition must resolve).
- `JOIN_MISMATCH` — the plan and probe key sets differ (input defect, not a
  coverage result).

## 6. Outputs

Under this experiment root only:
`integrity_audit/panel_archive_reconciliation_<computed_utc>.json` carrying
`experiment_id`, `audit_id`, `audited_artifacts`, `computed_utc`,
`preregistration`, `method`, `join_check`, `absent_summary`, `per_group`,
`per_asset`, `verdict`, `exploratory_only=true`, `promotion_allowed=false`,
`non_claims`.

## 7. Safeguards

- Read-only: the H41 plan, H43 probe, H40 feasibility study and every frozen
  DISP-003 artifact, panel, grid ledger and forward block are never modified.
- No sealed holdout opened; no 30-day maturity rule relaxed; no truncated
  outcomes; no fabricated files.
- Does not re-probe the date-gated `2026-11` cutoff month.
- DISPERSION-001/002 and frozen DISPERSION-003 artifacts/configs/inputs
  untouched.
- The analysis reads committed artifacts only; it does not recompute any grid or
  forward block.

## 8. Next test (if pursued)

If the verdict is `RECONCILIATION_HAS_COVERAGE_GAPS` (as the descriptive split
anticipates: trailing funding gaps for one asset, pre-listing gaps for the
others), a future bounded, preregistered acquisition step under a NEW experiment
ID may attempt to acquire the specific absent files that fall inside a live
window (never fabricating them), or explicitly narrow the eligible universe to
exclude assets whose required study months are not fully served. Confirmation of
any economic claim still requires a genuinely fresh, mature sealed forward block.
Never treat this development-data source-coverage reconciliation as confirmation.