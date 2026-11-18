# Wave-A Panel Archive Acquisition — bounded, verified, keyless fetch of the H48 unconditional queue

**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-WAVEA-001
**Hypothesis ID:** H49 (allocated in this session)
**Status:** PREREGISTERED (before any file is fetched)
**Created:** 2026-11-18T21:20:00Z
**Type:** EXPLORATORY_ONLY — source-coverage acquisition (raw free public archive bytes + content-integrity evidence)

---

## 1. Purpose and trigger

H48 (PANELCOV-QUEUE-001) ended the exploratory coverage chain at a ready,
bounded acquisition queue: **wave A** = 7 assets (ALICE, ANKR, APE, API3, APT,
AR, ARPA) with all 644 required monthly archive files verified served (HTTP 200
in H43) and no window trim / no backfill needed; **wave B** = ARK + ASTR (184
planned files, 18 absent) requiring a separate window-trim decision; ALPHA
excluded (92 files) under the H47 no-backfill rule.

H48 stopped at planning. Nothing has ever downloaded a wave-A archive file, so
the committed evidence records only *availability*, never *content*. This study
executes the natural, already-bounded successor named by the H48 artifact and the
prior task message: a **NEW-ID bounded free-data acquisition of only the 644
wave-A files**. It is not a repeat of any inspected endpoint: no prior session
fetched these bytes or measured their integrity.

## 2. Inputs (read-only, pinned)

- **H41 acquisition plan** (920 `plan_entries`, authoritative archive URLs):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001/integrity_audit/H004V106_panel_acquisition_plan_20261116T085222Z.json`
  — file sha256 must equal the value pinned in the script
  (`H41_PLAN_SHA256`).
- **H43 archive probe** (920 `per_entry` with `http_status`):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PROBE-001/integrity_audit/H004V106_panel_archive_probe_20261116T142247Z.json`
- **H47 roster** (`included_assets`, canonical hash bound):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-NARROW-001/integrity_audit/panel_coverage_eligibility_roster_20261118T191152Z.json`,
  `roster_canonical_sha256` = `171cd174d527ff34c9ba0162f2b38c7e673f7c5b210daa118d8acdb99c067579`.
- **H48 queue** (wave labels and per-file counts; `queue_canonical_sha256` =
  `38c099db5c233222cc51f39348f06e933871337b807d4761512d2800ec2375c7`):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-QUEUE-001/integrity_audit/panel_coverage_acquisition_queue_20261118T201951Z.json`
- **H40 feasibility** (`study_months`, 46 months `2023-01` .. `2026-10`).

Frozen DISP-003 artifacts (canonical forward block, h10 fresh block, universe
frontier, grid v3 config) are only hashed before/after, never written.

## 3. Scope — exactly 644 files, no more, no less

For every H41 `plan_entry` whose `asset` is in the H48 wave-A set and whose
`month` is inside the 46 study months, fetch the archive at the plan's
`archive_url` and record the response. Pre-declared expected scope:

- assets: `alice`, `ankr`, `ape`, `api3`, `apt`, `ar`, `arpa` (7)
- kinds: `klines`, `funding` (2)
- months: the 46 study months
- files: 7 x 2 x 46 = **644**

**Exclusions, declared before fetching:**
- Wave B (ARK, ASTR) — 184 files: requires a separately preregistered window
  trim (H48). Not acquired here.
- ALPHA — 92 files: excluded by the H47 no-backfill rule. Not acquired here.
- Any month outside the H40 study window. Not acquired here.
- No `probe_month=2026-11` re-probe; that window remains date-gated to
  **2026-11-30**.

Only URLs that appear verbatim in the pinned H41 plan are fetched; the fetch
layer rejects any URL outside that allowlist.

## 4. Per-file recorded evidence (descriptive only)

`asset`, `symbol`, `kind`, `month`, `archive_url`, `http_status`,
`content_length_header`, `bytes_downloaded`, `sha256` of the downloaded bytes,
`cache_path`, `n_attempts`, `error`, and content-integrity fields obtained with
stdlib `zipfile`/`csv` over the downloaded bytes:

- `is_zip`, `n_members`, `csv_member`, `csv_header`, `n_csv_rows`,
  `first_timestamp`, `last_timestamp`, `content_ok`, `content_error`.

`content_ok` requires: a readable zip, exactly one `.csv` member, the
documented Binance header (`klines`: `open_time` first; `funding`: `calc_time`
first), at least one data row, and monotonically non-decreasing timestamps
across the member. Timestamps are recorded as raw archive values — no
interpretation, no return/spread/state computation.

## 5. Pre-declared decision rule (outcome-blind)

- `WAVEA_SCOPE_MISMATCH` — the derived wave-A file set does not equal the H48
  pinned wave-A set and count (7 assets / 644 files), or an expected file has no
  pinned plan URL.
- `WAVEA_ACQUISITION_INCOMPLETE` — any expected file has `http_status != 200`,
  a download error, no sha256, or `content_ok = false`.
- `WAVEA_ACQUISITION_COMPLETE` — all 644 expected files fetched with HTTP 200,
  a recorded sha256 and `content_ok = true`, and the frozen hashes are unchanged.

No threshold, ordering or label depends on any price, return, dispersion state or
other outcome. The rule reads archive availability and schema only.

## 6. Expected (pre-declared from H48 — not re-derived)

644 files, 7 wave-A assets, 0 wave-B and 0 ALPHA files acquired, verdict
`WAVEA_ACQUISITION_COMPLETE`, all four frozen hashes unchanged. Total byte size
is not pre-declared (H43 recorded per-file `content_length` only). This section
records the expectation so a contradicting result stays visible; section 5
decides the verdict.

## 7. Hard safeguards

- Free public keyless source only (`https://data.binance.vision`); no
  credentials, no paid service, no non-public endpoint.
- No look-ahead, no fabrication, no forward-fill: absent files stay absent and
  are reported as such. Bytes written are exactly the served bytes.
- No panel construction, no returns/spreads/states/p-values/costs/inference, no
  promotion, no trading.
- Raw archive bytes are cached outside version control
  (`data/panel_archive_wave_a/`, gitignored); only sha256 and descriptive
  integrity fields are committed.
- Frozen DISPERSION-001/002/003 artifacts, configs, ledgers and forward blocks
  are never modified; the confirmatory expanding-universe arm and the H10 fresh
  block are untouched.

## 8. Non-claims

- Does not construct a panel, estimate any effect, or make any confirmatory or
  economic claim.
- Does not validate, replace or unlock H1/H6/H7/H10 or any confirmatory track.
- Does not resolve wave B (ARK/ASTR) or ALPHA coverage; those remain blocked by
  their own declared decisions.
- The next authorized confirmatory action remains the H10 fresh-block maturity
  on/after **2026-11-30**.

## 9. Artifacts

- Script: `scripts/panel_wave_a_acquisition.py` (stdlib only, import-safe; pure
  selection/verification helpers; network and writes only under `--execute`).
- Test: `tests/test_panel_wave_a_acquisition.py` (hermetic selection/integrity/
  reconciliation fixtures + skip-guarded integration on the committed artifact).
- Output: `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-WAVEA-001/integrity_audit/panel_wave_a_acquisition_<computed_utc>.json`
- Cache: `data/panel_archive_wave_a/<archive_path>` (gitignored raw bytes).

## 10. Change log

- v1 (2026-11-18): initial preregistration, allocated before any fetch. Scope,
  rule, exclusions and expected counts fixed from H48/H47/H43/H41 evidence.
