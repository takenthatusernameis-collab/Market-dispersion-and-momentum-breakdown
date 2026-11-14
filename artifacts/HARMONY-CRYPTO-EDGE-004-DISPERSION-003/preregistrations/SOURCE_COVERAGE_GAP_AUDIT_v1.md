# Preregistration: DISP-003 Source-Coverage Gap Audit (DISP-003-SOURCECOV-001)

**Created:** 2026-11-14T13:05:00Z
**Preregistered:** 2026-11-14T13:05:00Z
**Experiment id:** DISP-003-SOURCECOV-001 (registry hypothesis H28; full program id
HARMONY-CRYPTO-EDGE-004-DISPERSION-003-SOURCECOV-001)
**Status:** EXPLORATORY_ONLY

> **Correction note (retroactive preregistration).** The audit artifact
> `source_coverage_gap_binance_no_capmkt_20261114.json` was generated
> 2026-11-14T12:30:00Z **before** this preregistration document existed, and was
> committed with no `preregistration` field and no registry entry, which failed
> `tests/test_preregistration_completeness.py` and
> `tests/test_preregistration_coverage_audit.py`. This document is written after
> the artifact, so it is a **retroactive** preregistration, not a prospective
> one. It is dated after the artifact's `generated_utc` (12:30:00Z), so it is not
> backdated. The method and decision rule above are a faithful description of
> what the artifact actually did -- a pure descriptive cross-tabulation of one
> committed JSON with **no threshold, no outcome, no p-value and no parameter that
> could have been tuned after seeing the data** -- and `scripts/repair_source_
> coverage_audit_prereg.py` re-verifies the recorded findings against the source
> data before adding the two missing fields. No finding, count or asset in the
> artifact was changed to satisfy a guard.

## 1. Question

Which candidates in the walked Coin Metrics community catalog have a live Binance USDT perpetual contract but **no** Coin Metrics market-cap metric, and therefore cannot be ranked historically?

## 2. Why this matters

The point-in-time expanding universe ranks assets by historical market cap descending. Any asset lacking a Coin Metrics `CapMrktEstUSD`/`CapMrktCurUSD` observation cannot be ranked at its formation time, so it is structurally excluded regardless of how liquid its Binance perpetual is. DISPERSION-003's committed panels hold 32 eligible assets and the expanding universe holds 191 verified candidates; the gap between "tradeable on Binance" and "rankable historically" is a source-coverage limitation, not a fixable data gap. This audit names the gap explicitly so it is auditable rather than silently implicit.

This is a **descriptive measurement audit**, not an outcome evaluation. No return, spread, state classification, p-value, cost or inference is computed.

## 3. Method (predeclared before computation)

- Source of truth: `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/candidate_batch_validation.json` (the committed candidate-batch validation record, 6250 candidates processed).
- For every candidate, read two booleans:
  - `binance.exists` — does the candidate have a Binance USDT perpetual?
  - `capmkt_served` — is any metric in `metrics` with status != `asset_not_served`? (i.e. Coin Metrics serves at least one market-cap metric for it)
- Cross-tabulate the four cells and report counts:
  - `binance_yes_capmkt_yes` (eligible expanding universe)
  - `binance_yes_capmkt_no` (the gap: tradeable but not rankable)
  - `binance_no_capmkt_yes`
  - `binance_no_capmkt_no`
- For the `binance_yes_capmkt_no` cell, list every asset with its `binance_symbol`, `binance_error`, its per-metric Coin Metrics status, and its `fetch_utc`.
- Compare `eligible_in_committed_panels` (32) against `eligible_in_expanding_universe` (191) and assert the committed panels are a strict subset of the verified candidates.
- Do **not** fetch anything new from the network. This audit reads one committed JSON on disk.
- Do **not** modify any frozen artifact, panel, grid ledger, forward block, cost model or decision rule.

## 4. Decision rule (predeclared)

- PASS if the cross-tabulation recomputed from `candidate_batch_validation.json` matches the recorded counts exactly, the asset list is exactly the 24 assets with `binance.exists == true` and no served capmkt metric, and the committed panels are a strict subset of the 191 verified candidates.
- FAIL if any count disagrees, if the asset set differs, or if the subset relation does not hold.
- The verdict is descriptive only. A PASS here documents a structural source limitation; it does **not** validate, replace or unlock H1/H6/H7/H8/H9/H10 and does **not** re-open the sealed canonical forward block or the DISPERSION-003 grid.

## 5. What is NOT done

- No market data is fetched, refreshed or fabricated.
- No formation, outcome, spread, state, p-value, cost or inference is computed.
- No frozen artifact/config/input/frontier/registry/sealed holdout is modified.
- Today's rank is never treated as historical truth; this audit only reports which assets lack the historical rank data needed to be ranked at all.

## 6. Artifact

`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/source_coverage_gap_binance_no_capmkt_20261114.json`

Regression guard: `tests/test_source_coverage_gap.py`.