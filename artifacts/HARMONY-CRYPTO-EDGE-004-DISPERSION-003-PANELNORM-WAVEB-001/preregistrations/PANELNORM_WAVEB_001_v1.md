# Wave-B Extension Panel Normalization — bounded, no-outcome source coverage

**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-WAVEB-001
**Hypothesis ID:** H53
**Status:** PREREGISTERED (before any panel byte is written)
**Created:** 2026-11-19T05:45:27Z
**Type:** EXPLORATORY_ONLY — source-coverage panel normalization (raw archive bytes → DISP-003-schema panel CSVs + integrity evidence; no outcomes)

---

## 1. Purpose and trigger

The exploratory source-coverage chain reaches:

- **H49 (H51-a plan)** declares the target panel schema, per-asset admissible months and per-file sha256 provenance for the 9 extension assets (810 planned panel files: 644 wave-A + 166 wave-B).
- **H52 (`WAVEB_ACQUISITION_COMPLETE`)** acquired and content-verified exactly the 166 trimmed wave-B archives (ARK 76 across 38 admissible months, ASTR 90 across 45) into the gitignored cache `data/panel_archive_wave_b/`.
- Wave-A raw bytes are **not** present in this checkout (`data/panel_archive_wave_a/` is empty), so only the wave-B half of the H51-a plan is realizable here.

This study executes the wave-B half: it normalizes exactly those 166 acquired archives into 4 committed DISP-003-schema panel CSVs and records per-file reconciliation. It is a NEW ID and a new endpoint: no panel byte has ever been constructed from any wave-B archive in this program.

## 2. Inputs (read-only, pinned before fetching/normalizing)

- **H52 wave-B acquisition audit** — file sha256 `fb2b7cf7642d616b51e303ffc37382dc2a79e355e4df11f150fffad19ac7c5ef`, `records_canonical_sha256` `887970ebbf3e06fadc1f7e265bd72e5de94aea605e3cba3a34938193562a335c`, verdict `WAVEB_ACQUISITION_COMPLETE`, 166 records. Authoritative source of each cached archive's path and sha256.
- **H51-a normalization plan** — file sha256 `dc8e100682cf3eab147787973536dd0de1517c740e5075a7c3f3db43796b9768`. Authoritative source of the per-asset `admissible_months`, the strict DISP-003 schema and the panel file naming.
- **H50 wave-B window trim** — file sha256 `5aed05f1615a3cc2983c6e1be86ef9f35306aed7cfab86aea9f1d8fab9f61e66`, `trim_canonical_sha256` `b43f71bf239254152288b8eaf89a7748680117c7ecc10a16564c4a9b6a115a5d`. Cross-check only.
- **Raw archive cache** `data/panel_archive_wave_b/` (166 zip files, gitignored; never modified, never re-downloaded).

Frozen DISP-003 artifacts (canonical forward block `7234fc4e...`, H10 fresh block `324ab1e6...`, universe frontier `9ba08f3f...`, grid v3 config `1ff4c1f2...`) are only hashed before/after, never written.

## 3. Scope — exactly 4 panels

| panel file | asset | kind | admissible months |
|---|---|---|---|
| `binance_klines_ARKUSDT.csv` | ark | klines 1d | 38 (read from H51-a plan) |
| `binance_funding_ARKUSDT.csv` | ark | funding | 38 |
| `binance_klines_ASTRUSDT.csv` | astr | klines 1d | 45 |
| `binance_funding_ASTRUSDT.csv` | astr | funding | 45 |

**Exclusions declared before computation:** wave A (7 assets, 644 files — bytes absent in this checkout), ALPHA (excluded under the H47 no-backfill rule), the 18 H50 `dropped_required_months` pre-listing months, and any month outside an asset's H50/H51-a admissible window.

**Schema (unchanged from DISPERSION-002 / DISP-003):**
- klines: `open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore`
- funding: `symbol,calc_time,funding_interval_hours,last_funding_rate` (symbol column prepended per row)

## 4. Controls

1. **Pinned digests first.** H52 audit file sha256, `records_canonical_sha256`, H51-a plan sha256 and H50 trim sha256 are verified before any panel byte is written. A mismatch aborts with no output.
2. **Per-file sha256 reconciliation.** Every one of the 166 cache files must hash to the sha256 recorded by H52; any mismatch is reported and fails completeness.
3. **Strict content re-validation.** Each archive must contain exactly one CSV member, carry the documented canonical header (klines first field `open_time`, funding first field `calc_time`), have at least one data row, and have non-decreasing integer timestamps. Malformed or missing files stay absent and are reported; nothing is interpolated, backfilled or forward-filled.
4. **Month discipline.** Each file may contribute only rows whose timestamp falls in `[month_start, next_month_start)` UTC; out-of-window rows are counted and a nonzero count fails completeness. The union of contributing months must equal the admissible months exactly.
5. **Row-accounting identity.** For each panel, `rows_written == sum(record n_csv_rows)` for the contributing files: no row is silently dropped or invented.
6. **No dedupe that hides defects.** Duplicate timestamps are counted and reported; a nonzero duplicate count fails completeness rather than being silently collapsed.
7. **No network.** This study performs no HTTP I/O. Bytes come only from the existing cache.
8. **Committed output is panel bytes + hashes only**; no `data/` cache is committed.

## 5. Pre-declared verdicts (outcome-blind)

- `PANELNORM_WAVEB_SCOPE_MISMATCH` — a pinned digest fails, the H52 verdict is not `WAVEB_ACQUISITION_COMPLETE`, the asset set is not exactly {`ark`,`astr`}, the derived month set differs from the H51-a plan, the expected panel count is not 4, or any planned month has no corresponding H52 record.
- `PANELNORM_WAVEB_INCOMPLETE` — scope is correct but any cache file fails sha256 reconciliation or content re-validation, any month is uncovered, any out-of-window row or duplicate timestamp occurs, or the row-accounting identity fails.
- `PANELNORM_WAVEB_COMPLETE` — all 166 files reconciled and re-validated, 4 panels written, months covered exactly, row identity holds, zero out-of-window rows, zero duplicate timestamps.

No threshold, ordering or label depends on any price, return, dispersion state or other outcome.

## 6. Expected result (pre-declared from H52/H51-a — not re-derived)

4 panels, 166/166 files reconciled, 0 missing, 0 out-of-window rows, 0 duplicate timestamps, ARK 38 + ASTR 45 admissible months covered exactly. This section records the expectation so a contradicting observation stays visible; section 5 decides the verdict.

## 7. Non-claims

- A normalized panel is not market evidence and is not an economic result.
- No returns, spreads, dispersion states, p-values, costs or inference are computed here; no multiple-testing correction is performed.
- No candidate is promoted; no confirmatory claim is made; the H10 confirmatory gate is unchanged and still date-gated to 2026-11-30.
- No frozen DISP-001/002/003 artifact, config, ledger, existing panel or forward block is modified; the sealed holdout is not opened.
- A green test suite proves only what the tests cover.

## 8. Verification plan

- Hermetic unit tests for selection, header/content validation, month-window accounting, duplicate detection, funding symbol prefixing, row-identity accounting and every verdict branch.
- Skip-guarded integration tests binding the committed panels to the committed audit artifact (panel sha256, row counts, month coverage).
- `python3 -m compileall -q scripts tests` and the full `python3 -m unittest discover -s tests` suite.
- Re-record the verified test claim, session verification record, registry H53 entry and the contract pin bump to 53.

## 9. Change log

- v1 (2026-11-19T05:45:27Z): initial preregistration. Consumes the H52 acquisition and H51-a plan unchanged; no outcome-informed choice; panel scope fixed at the wave-B admissible months before any panel byte is written.
