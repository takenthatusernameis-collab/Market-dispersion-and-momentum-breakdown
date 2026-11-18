# Extension-Panel Normalization Plan — DISP-003 wave-A + wave-B into point-in-time aligned panel

**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-PLAN-001
**Hypothesis ID:** H51 (allocated in this session)
**Status:** PREREGISTERED (before any panel construction)
**Created:** 2026-11-18T23:12:00Z
**Type:** EXPLORATORY_ONLY — source-coverage normalization plan (planning only; no panel bytes, no outcomes)

---

## 1. Purpose and trigger

H49 (PANELACQ-WAVEA-001) acquired and content-verified the **wave-A raw archive bytes** for 7 fully served extension assets (ALICE, ANKR, APE, API3, APT, AR, ARPA) across all 46 study months (2023-01..2026-10): 644 files cached in `data/panel_archive_wave_a/` with per-file sha256 and content-integrity evidence committed in the H49 artifact.

H50 (PANELCOV-WAVEB-TRIM-001) registered the **window-trim decision** for wave B (ARK, ASTR): the verified served windows are ARK 2023-09..2026-10 (38 months / 76 files) and ASTR 2023-02..2026-10 (45 months / 90 files). The trimmed wave-B acquisition plan totals **166 planned = 166 servable, 0 absent**; 18 pre-listing placeholder files (ARK 2023-01..2023-08 both kinds, ASTR 2023-01 both kinds) are dropped with `all_dropped_before_first_served=true`, so the trim loses no served data. Acquisition of these 166 wave-B files is a separate, optional, later-authorized step (H51-b) and is NOT part of this plan.

This study produces the **normalization plan** — a NEW-ID, bounded, no-cost, EXPLORATORY_ONLY document declaring exactly how the H49 wave-A raw archives and the H50-trimmed wave-B file set would be normalized into a **DISP-003 extension panel** with:
- Point-in-time formation alignment (each asset enters the panel at its H47 verified `first` month per kind)
- No backfill before any asset's H47 verified window
- No fabrication of missing data; months outside served windows stay absent
- Strict schema matching the existing DISP-003 panels (`binance_klines_<SYMBOL>.csv`, `binance_funding_<SYMBOL>.csv`)
- Per-file sha256 provenance from H49 (wave-A) and future H51-b (wave-B)

No panel is constructed here. No returns, spreads, states, p-values, costs, or inference are computed. This is a plan artifact only; any panel construction would require a separately preregistered hypothesis.

---

## 2. Inputs (read-only, pinned)

- **H47 eligibility roster** (`roster_canonical_sha256` = `171cd174d527ff34c9ba0162f2b38c7e673f7c5b210daa118d8acdb99c067579`):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-NARROW-001/integrity_audit/panel_coverage_eligibility_roster_20261118T191152Z.json`
  — per-asset served windows (`first`/`last` month per kind with HTTP 200) and inclusion decisions.

- **H49 wave-A acquisition audit** (644 records, `records_canonical_sha256` = `f94072df03e2b15c950c244e6938d75048bc8f90fd616b20022848048ceb758d`):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-WAVEA-001/integrity_audit/panel_wave_a_acquisition_20261118T211130Z.json`
  — per-file `archive_url`, `sha256`, `cache_path`, `csv_header`, `n_csv_rows`, `first_timestamp`, `last_timestamp`, `content_ok`.

- **H50 wave-B trim audit** (`trim_canonical_sha256` = `b43f71bf239254152288b8eaf89a7748680117c7ecc10a16564c4a9b6a115a5d`):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-WAVEB-TRIM-001/integrity_audit/panel_wave_b_window_trim_20261118T221212Z.json`
  — per-asset `admissible_study_months`, `served_window`, `all_dropped_before_first_served=true`.

- **H41 acquisition plan** (920 `plan_entries`, authoritative archive URLs):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001/integrity_audit/H004V106_panel_acquisition_plan_20261116T085222Z.json`

- **DISP-003 panel manifest** (32 base assets, schema reference):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/binance_panel_manifest.json`

- **Frozen DISP-003 artifacts** (canonical forward block, h10 fresh block, universe frontier, grid v3 config) are only hashed before/after, never written.

---

## 3. Scope — exactly 9 extension assets, 46 study months, 2 kinds

| Asset | Wave | H47 Decision | Admissible Months (klines) | Admissible Months (funding) | Planned Files |
|-------|------|--------------|----------------------------|-----------------------------|---------------|
| ALICE | A    | INCLUDED_FULLY_SERVED | 2023-01..2026-10 (46) | 2023-01..2026-10 (46) | 92 |
| ANKR  | A    | INCLUDED_FULLY_SERVED | 2023-01..2026-10 (46) | 2023-01..2026-10 (46) | 92 |
| APE   | A    | INCLUDED_FULLY_SERVED | 2023-01..2026-10 (46) | 2023-01..2026-10 (46) | 92 |
| API3  | A    | INCLUDED_FULLY_SERVED | 2023-01..2026-10 (46) | 2023-01..2026-10 (46) | 92 |
| APT   | A    | INCLUDED_FULLY_SERVED | 2023-01..2026-10 (46) | 2023-01..2026-10 (46) | 92 |
| AR    | A    | INCLUDED_FULLY_SERVED | 2023-01..2026-10 (46) | 2023-01..2026-10 (46) | 92 |
| ARPA  | A    | INCLUDED_FULLY_SERVED | 2023-01..2026-10 (46) | 2023-01..2026-10 (46) | 92 |
| ARK   | B    | INCLUDED_PRELISTING_GAPS_ONLY | 2023-09..2026-10 (38) | 2023-09..2026-10 (38) | 76 |
| ASTR  | B    | INCLUDED_PRELISTING_GAPS_ONLY | 2023-02..2026-10 (45) | 2023-02..2026-10 (45) | 90 |

**Total extension panel files:** 92×7 + 76 + 90 = **644 + 166 = 810** (klines + funding per asset per admissible month)

**Exclusions, declared before planning:**
- ALPHA (92 files): excluded by H47 `EXCLUDED_UNSERVED_TIMELINE` (AFTER_LAST_SERVED funding gaps 2025-10..2026-10). Never included.
- Any month outside an asset's H47 verified served window per kind. Never backfilled.
- Wave-B files for months dropped by H50 (18 pre-listing files). Never fetched, never fabricated.
- No `probe_month=2026-11` re-probe; that window remains date-gated to **2026-11-30**.

---

## 4. Normalization procedure (deterministic, stdlib-only, reproducible)

### 4.1 Per-asset, per-kind panel assembly

For each of the 9 extension assets and each kind (`klines`, `funding`):

1. **Determine the admissible month list** from the H47 roster `served_window[kind].first` .. `served_window[kind].last`, intersected with the 46 H40 study months. This list is exactly the H50 `admissible_study_months` for wave-B assets and all 46 months for wave-A assets.

2. **For each admissible month**, locate the raw archive:
   - **Wave-A assets (7):** read from `data/panel_archive_wave_a/<archive_path>` where `<archive_path>` matches the H49 `cache_path` for that asset/kind/month. Verify the file's sha256 matches the H49 `sha256` record. Open the zip, extract the single CSV member, validate header matches the DISP-003 expected header (`open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore` for klines; `calc_time,funding_interval_hours,last_funding_rate` for funding), and append rows to the panel.
   - **Wave-B assets (2):** the H51-b acquisition (if/when authorized) will deposit files under `data/panel_archive_wave_b/<archive_path>` with the same structure. The plan references the H41 `archive_url` and expects the same per-file sha256/content-integrity evidence as H49.

3. **Concatenate monthly CSVs in chronological order** (by month, then by timestamp within month). The DISP-003 panels are already sorted by `open_time`/`calc_time`; the monthly zips from Binance are themselves time-ordered. Concatenation preserves global time order.

4. **No deduplication, no gap-filling, no forward-fill.** If a month is absent from the served window (per H47/H50), it is simply not in the admissible list and contributes no rows. The panel may have temporal gaps at the asset's pre-listing boundary; this is expected and documented.

5. **Write the panel CSV** to the extension panel directory with the DISP-003 naming convention: `binance_klines_<SYMBOL>.csv` and `binance_funding_<SYMBOL>.csv` where `<SYMBOL>` is the H47 `symbol` (e.g., `ALICEUSDT`, `ARKUSDT`).

### 4.2 Extension panel manifest

Produce a manifest JSON mirroring the structure of `binance_panel_manifest.json` but covering only the 9 extension assets:

```json
{
  "experiment_id": "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-PLAN-001",
  "base_manifest": "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/binance_panel_manifest.json",
  "extension_assets": 9,
  "symbol_map": { ... },
  "series": [
    { "asset": "alice", "symbol": "ALICEUSDT", "kind": "klines", "date_first": ..., "date_last": ..., "rows": ..., "admissible_months": [...], "provenance": "H49" },
    ...
  ],
  "provenance": {
    "wave_a_audit": "H49 artifact path + sha256",
    "wave_b_trim_audit": "H50 artifact path + sha256",
    "h47_roster_sha256": "171cd174...",
    "h41_plan_sha256": "39e740b6..."
  }
}
```

Each `series` entry records the asset, symbol, kind, first/last timestamp (from the concatenated panel), row count, the explicit list of `admissible_months`, and provenance tag (`H49` for wave-A, `H51-b` for wave-B once acquired).

### 4.3 Point-in-time formation alignment

The DISP-003 dispersion/momentum formation logic uses a **formation date** (e.g., 2026-09-30) and looks back over a formation window. For the extension panel to be compatible:

- An asset **must not contribute** to any formation dated before its `date_first` (per kind) in the extension panel.
- The formation code must be given the per-asset `date_first` (earliest available timestamp per kind) so it can enforce point-in-time alignment.
- This plan does not modify formation code; it documents the per-asset `date_first`/`date_last` bounds that any downstream formation consumer must respect.

### 4.4 No backfill, no fabrication

- Months before `served_window[kind].first` are **never** populated, even if the H41 plan has a URL for them (they returned HTTP 404 in H43/H47).
- Months after `served_window[kind].last` are **never** populated.
- No synthetic rows, no interpolation, no carry-forward. Absent months stay absent.

---

## 5. Pre-declared decision rule (outcome-blind)

- `PLAN_SCOPE_MISMATCH` — the derived extension asset set does not equal the 9 H47-included assets, or an asset's admissible months do not match the H47/H50 served windows, or a required H49/H50 input hash does not match its pinned value.
- `PLAN_RECORDED` — the plan declares exactly 810 panel files (9 assets × 2 kinds × admissible months), with per-file provenance, schema, concatenation order, manifest structure, and point-in-time bounds all fixed from H47/H49/H50/H41 evidence. No panel bytes are written; no outcomes computed.

No threshold, ordering, or label depends on any price, return, dispersion state, or other outcome. The rule reads served windows and provenance only.

---

## 6. Expected plan (pre-declared from H47/H49/H50 — not re-derived)

- 9 extension assets (7 wave-A fully served, 2 wave-B trimmed).
- 810 panel files total (644 wave-A + 166 wave-B).
- Per-asset admissible months exactly as in the H47 roster `served_window` intersected with study months.
- Wave-A provenance: H49 `records` (sha256 + cache_path per file).
- Wave-B provenance: H41 `plan_entries` for the 166 trimmed files; actual bytes/sha256 to come from H51-b if authorized.
- Extension panel manifest with per-series `date_first`, `date_last`, `rows`, `admissible_months`, `provenance`.
- All four frozen DISP-003 hashes unchanged.
- Verdict: `PLAN_RECORDED`.

---

## 7. Non-claims

- Does not construct a panel, estimate any effect, or make any confirmatory or economic claim.
- Does not validate, replace or unlock H1/H6/H7/H10 or any confirmatory track.
- Does not fetch any archive file; wave-B acquisition (H51-b) remains a separate later step.
- Does not alter the confirmatory expanding-universe arm or any frozen DISP-001/002/003 artifact, config, ledger or forward block.
- The next authorized confirmatory action remains the H10 fresh-block maturity on/after **2026-11-30**.

---

## 8. Artifacts

- **Script:** `scripts/panel_normalization_plan.py` (stdlib only, import-safe; pure plan-build helpers; writes only under `--out`).
- **Test:** `tests/test_panel_normalization_plan.py` (hermetic plan-structure fixtures + skip-guarded integration on the committed artifact).
- **Output:** `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-PLAN-001/integrity_audit/panel_normalization_plan_<computed_utc>.json`
- **No cache directory** (planning only; no raw bytes downloaded here).

---

## 9. Change log

- v1 (2026-11-18): initial preregistration, allocated before any computation. Scope, procedure, exclusions and expected counts fixed from H47/H49/H50/H41 evidence.