# Panel-Coverage Eligibility Roster — narrowing the planned extension universe to served assets

**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-NARROW-001
**Hypothesis ID:** H47 (allocated in this session)
**Status:** PREREGISTERED (before computation)
**Created:** 2026-11-18T19:20:00Z
**Type:** EXPLORATORY_ONLY — descriptive source-coverage adjudication on already-inspected committed artifacts

---

## 1. Purpose and trigger

H46 (PANELACQ-RECON-001) joined the H41 acquisition plan and the H43 archive probe
and classified the 31 missing archive files. It closed with two explicit
next-test options and no operational artifact:

> a future bounded step may (a) acquire only the specific absent files ... or
> (b) **explicitly narrow the eligible expanding universe to exclude assets
> whose required study months are not fully served**.

H46 remains a per-file description. Nothing in the durable state converts it into
an **asset-level inclusion decision**, and nothing records the *verified served
window* per asset and kind. Without that, any future panel step still has to
assume the H40 `expected_zip_files_upper_bound` is acquirable, which H43/H46
already disproved for one asset.

This experiment performs option (b) as a bounded, read-only, no-cost,
stdlib-only adjudication. It is EXPLORATORY_ONLY source-coverage work: no
network, no downloads, no panels, no returns/spreads/states/p-values/costs/
inference, no promotion, no sealed holdout opened, and it does not re-probe the
date-gated `2026-11` cutoff month.

## 2. Inputs (read-only)

- **H41 acquisition plan** (920 `plan_entries` with `asset`, `symbol`, `kind`,
  `month`):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001/integrity_audit/H004V106_panel_acquisition_plan_20261116T085222Z.json`
- **H43 archive probe** (920 `per_entry` with `http_status`, `error`):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PROBE-001/integrity_audit/H004V106_panel_archive_probe_20261116T142247Z.json`
- **H40 feasibility** (`per_asset[].required_study_months`, context only):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-FEAS-001/integrity_audit/H004V106_panel_coverage_extension_feasibility_20261116T215857Z.json`

All three are existing committed artifacts and are read-only here.

## 3. Estimand

For each of the ten H41 extension assets, the roster reports:

1. `served_window` per kind = `[min month served HTTP 200, max month served HTTP 200]`
   inside the planned months (the only interval with verified archive coverage).
2. Every absent planned file, classified against that asset-kind window as
   `BEFORE_FIRST_SERVED`, `AFTER_LAST_SERVED`, `INTERIOR`, `ENTIRELY_ABSENT`,
   `ERROR` (probe error, no clean status) or `UNPROBED` (plan key missing from
   the probe).
3. An asset inclusion decision (section 4).
4. For included assets, `n_required_months_outside_verified_window`: the number
   of H40 `required_study_months` that fall outside the verified window of at
   least one required kind — i.e. the concentration of study months for which
   this asset could contribute **no** verified price/funding observation.

No returns, states, spreads, p-values, costs or inference are computed. The
roster is a data-availability contract, not an economic result.

## 4. Pre-declared decision rule (outcome-blind)

Per asset, in this priority order:

1. `EXCLUDED_UNPROBED` — at least one planned `(kind, month)` has no probe record.
2. `EXCLUDED_PROBE_ERROR` — at least one probe record carries `error` and no
   `http_status == 200`.
3. `EXCLUDED_UNSERVED_TIMELINE` — at least one gap is `AFTER_LAST_SERVED`,
   `INTERIOR` or `ENTIRELY_ABSENT` (a hole inside the asset's live window).
4. `INCLUDED_PRELISTING_GAPS_ONLY` — every gap is `BEFORE_FIRST_SERVED` (the
   contract did not exist yet; the asset is included only inside its verified
   window).
5. `INCLUDED_FULLY_SERVED` — no gaps at all.

Roster verdict:

- `ROSTER_JOIN_MISMATCH` if any plan key is missing from the probe;
- else `ROSTER_HAS_UNSERVED_ASSETS` if at least one asset is excluded;
- else `ROSTER_ALL_ASSETS_FULLY_SERVED`.

`BEFORE_FIRST_SERVED` gaps are not exclusionary because a pre-listing month has
no market to observe; that is the same benign treatment H46 recorded. Any
`AFTER_LAST_SERVED` / `INTERIOR` / `ENTIRELY_ABSENT` gap is exclusionary because
including such an asset would silently drop required in-window observations.

## 5. Expected (pre-declared, from H46 — not re-derived)

H46 already recorded 31 absences: ARK 16 and ASTR 2 `BEFORE_FIRST_SERVED`, ALPHA
13 `AFTER_LAST_SERVED` (funding stops 2025-09 while klines run to 2026-10). The
expected roster is therefore 9 included (7 fully served + 2 pre-listing-only) and
1 excluded (ALPHA), verdict `ROSTER_HAS_UNSERVED_ASSETS`. This section records the
expectation so a contradicting result is visible rather than silently absorbed;
the rule above, not this expectation, decides the verdict.

## 6. Non-claims

- Does not acquire, fabricate or forward-fill any missing archive file.
- Does not construct a panel, compute returns/spreads/states/p-values/costs, or
  promote any candidate.
- Does not alter the confirmatory expanding-universe arm, the frozen
  DISPERSION-001/002/003 artifacts, the canonical forward block
  (`7234fc4e...`), the H10 fresh sealed block (`324ab1e6...`), the grid v3
  config (`1ff4c1f2...`) or the universe frontier (`9ba08f3f...`).
- Cannot validate, replace or unlock H1/H6/H7/H10 or any confirmatory track.
- The next authorized confirmatory action remains H10 fresh-block maturity
  on/after 2026-11-30.

## 7. Artifacts

- Script: `scripts/panel_coverage_eligibility_roster.py` (stdlib only, import-safe,
  `--out` writes only on explicit invocation).
- Test: `tests/test_panel_coverage_eligibility_roster.py` (hermetic synthetic
  fixtures for every rule branch + skip-guarded integration on committed inputs).
- Output: `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-NARROW-001/integrity_audit/panel_coverage_eligibility_roster_<computed_utc>.json`
