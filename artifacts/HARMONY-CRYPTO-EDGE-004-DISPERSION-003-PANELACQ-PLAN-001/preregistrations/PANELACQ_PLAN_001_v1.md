# Preregistration: DISP-003-PANELACQ-PLAN-001 (H41)

- **Preregistration ID:** PANELACQ_PLAN_001_v1
- **Experiment / artifact family:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001
- **Hypothesis registry ID:** H41
- **Status:** EXPLORATORY_ONLY (design/planning only; not confirmatory)
- **Label:** `PANEL_ACQUISITION_PLAN_READY` / `PANEL_ACQUISITION_PLAN_LIMITED` (predeclared rule below)
- **Created (UTC):** 2026-11-16T08:50:17Z
- **Scope:** Bounded, keyless, free-public, committed-metadata-only acquisition/probe **plan** for a small deterministic PIT subset of H39/H40 union assets lacking committed Binance panels. No network access, no archive probing/downloading in this artifact, no panel construction/normalization, no outcome computation.

## 1. Question (prior, narrower than acquisition)
Given committed artifacts only — H40 feasibility audit (188/188 verified Binance USD-M symbol mapping, cap observations in 2023-01-01..2026-10-31, gap unfilled, 46 study months × 2 kinds), H39 rank-breadth audit, candidate validation, and frozen config/hashes — can we deterministically enumerate a **small explicit PIT subset** and a bounded, reproducible keyless Binance Public Data Archive URL/manifest plan (monthly klines + fundingRate zips, by symbol/month/kind) suitable for a separate future acquisition step, while recording safeguards and decision rules?

This does **not** ask whether acquired panels improve outcomes, nor does it claim archive publication for any symbol/month.

## 2. Inputs (committed, read-only)
- `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-FEAS-001/integrity_audit/H004V106_panel_coverage_extension_feasibility_20261116T081554Z.json` (H40; SHA256 verified against committed blob by audit)
- `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-FEAS-001/integrity_audit/H004V106_rank_breadth_feasibility_2026-11-16T06-57-08Z.json` (H39)
- `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/candidate_batch_validation.json`
- Frozen references (hash-checked, unchanged): canonical forward block, h10_fresh, grid_result_ledger, universe_frontier, grid v3 config (see script constants).

No market data fetched; no raw Binance archives read/written.

## 3. Deterministic subset selection (predeclared, outcome-blind)
From H40 `per_asset` where committed gap is unfilled and mapping/validation/cap criteria hold, select the first **10** assets by deterministic key:
1. `cap_obs_in_study_window` descending,
2. `cap_coverage_frac` descending,
3. `asset` ascending (lexicographic).

Rationale: highest PIT cap coverage within the declared study window maximizes planning value for any later bounded acquisition; no returns, ranks-as-history beyond committed PIT cap presence, or outcomes inspected. Selection is fixed by this rule over committed H40 content.

## 4. Bounded scope (planning only)
- Per selected asset: Binance USD-M symbol from committed validation/H40; kinds `klines` (daily) and `fundingRate` (monthly funding) as in committed source conventions; months limited to the asset’s `required_study_months` present in committed H40 record (study window 2023-01-01..2026-10-31).
- Total planned objects = sum over subset of `expected_zip_files_upper_bound` (months × kinds), recorded explicitly. No claim that every month is published/listed for every symbol.
- Output: deterministic manifest-like plan (URLs/paths template or explicit monthly entries derivable from symbol+month+kind, SHA256/provenance fields left null/`PENDING_ACQUISITION`) and a gap summary vs committed panels. This is metadata/planning, not acquired data.

## 5. Decision rule (predeclared)
- `PANEL_ACQUISITION_PLAN_READY` iff: subset size == 10; every subset asset has `in_candidate_validation==true`, `binance_exists==true`, `validation_status=="verified"`, non-empty `symbol`, `cap_obs_in_study_window >= 1`, `committed_kline_panel==false` and `committed_funding_panel==false`, a non-empty `required_study_months` list consistent with H40 bounds, and all frozen hash checks pass; and the plan enumerates exactly the bounded monthly (symbol, kind, month) entries implied by committed fields with no duplicates.
- Otherwise `PANEL_ACQUISITION_PLAN_LIMITED` with explicit failing conditions recorded.

## 6. Safeguards (hard constraints honored)
- **Free public data only; no network.** This artifact uses committed metadata only. Any future download/probe must be keyless, free-public (Binance Public Data Archive / permitted free endpoints), with per-file provenance and SHA256 recorded, and must not be performed here.
- **Historical/PIT discipline.** No today’s rank used as historical truth; no backfill. Subset is defined from committed PIT cap-observation presence and committed validation, not current market state.
- **No outcomes.** No returns, spreads, dispersion states, p-values, costs, funding attribution, or inference computed or implied.
- **Frozen artifacts untouched.** Canonical/confirmatory artifacts, configs, ledgers, frontier, and sealed holdout unchanged. Inspected forward block is not reused as fresh confirmation.
- **Track separation.** Result is `EXPLORATORY_ONLY`/planning evidence only; cannot validate, replace, or unlock H1/H6/H7/H10 or any confirmatory track. Does not promote or relax confirmatory gates.
- **No fabricated availability.** Plan entries are *requested/bounded targets*, not proof of publication; publication must be verified in a separate bounded acquisition step if pursued.

## 7. Required outputs
- Preregistration (this file).
- Read-only script: `scripts/panel_acquisition_plan.py` (import-safe pure helpers + CLI writing audit JSON).
- Deterministic audit artifact: `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001/integrity_audit/H004V106_panel_acquisition_plan_<ts>.json` containing subset, per-asset/month/kind plan entries (bounded), counts, decision, frozen hash verification, and explicit non-claims.
- Hermetic tests: `tests/test_panel_acquisition_plan.py` pinning decision rule, subset determinism, rebuild-vs-committed (excluding wall-clock/output path), and frozen hashes.

## 8. If pursued next (separate NEW ID/prereg, not this task)
A bounded keyless acquisition/probe pass for a declared subset/month range with recorded HTTP/keyless access provenance, SHA256 per archive, and PIT-aware panel normalization/manifesting — still exploratory until separately preregistered outcomes/gates are met. Must not compute outcomes or treat missing archives as permission to fabricate.

## 9. Non-claims
This preregistration/artifact does **not** claim: archive availability, data completeness, successful download, panel correctness, tradability, statistical significance, economic edge, or confirmatory evidence. A green script/test proves only what tests cover.
