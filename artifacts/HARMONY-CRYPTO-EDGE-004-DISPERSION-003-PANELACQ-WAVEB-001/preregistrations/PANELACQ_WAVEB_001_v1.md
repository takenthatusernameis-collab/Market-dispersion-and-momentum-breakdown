# Wave-B (ARK/ASTR) Panel Archive Acquisition — bounded, keyless, no-outcome source coverage

**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-WAVEB-001
**Hypothesis ID:** H51 (allocated from the registry in this session)
**Status:** PREREGISTERED (before any fetch or computation)
**Created:** 2026-11-18T22:25:05Z
**Type:** EXPLORATORY_ONLY — source-coverage acquisition (raw archive bytes + per-file integrity evidence; no panel, no outcomes)

---

## 1. Purpose and trigger

The exploratory source-coverage chain H40 → H41 → H43 → H46 → H47 → H48 → H49 → H50 ends with:

- **wave A** (ALICE, ANKR, APE, API3, APT, AR, ARPA): 644 planned files, all served, acquired and content-verified under H49 (`WAVEA_ACQUISITION_COMPLETE`).
- **wave B** (ARK, ASTR): 184 planned files of which 18 are verified `BEFORE_FIRST_SERVED` HTTP 404 pre-listing placeholders. H50 (`TRIM_DECISION_RECORDED`) declared the admissible windows: ARK served `2023-09..2026-10` (38 admissible study months, 76 planned files), ASTR served `2023-02..2026-10` (45 months, 90 files); trimmed wave B = **166 planned = 166 servable, 0 absent**, and `all_dropped_before_first_served = true`, so the trim loses no served data.
- **ALPHA**: excluded under the H47 no-backfill rule.

H49 left wave B unacquired and H50 only *decided* the window. This study executes the H50 decision: a NEW-ID, bounded, no-cost acquisition of exactly the 166 trimmed wave-B files, recording a per-file sha256 and stdlib content-integrity evidence. It is not a repeat of an inspected endpoint: no wave-B byte has ever been fetched in this program.

After this study the full extension universe (9 included assets: 7 wave A + ARK + ASTR) has acquired, content-verified raw archives. Normalization into a DISP-003 extension panel remains a separate later step requiring its own NEW-ID preregistration.

## 2. Inputs (read-only, pinned before fetching)

- **H41 acquisition plan** (920 `plan_entries`, authoritative archive URLs), file sha256 pinned `39e740b65fbe65541aa42f55b0e231469c49dda7e04d9e22e04eae3ac9ce441b`.
- **H43 archive probe** (920 `per_entry`, `http_status`), file sha256 pinned `69b6e632b5d6b01ecaf9c7f625eeb8e4ad5bcd1f8d1e2ec6b946efb62dd40974`.
- **H47 eligibility roster** (`roster_canonical_sha256` `171cd174d527ff34c9ba0162f2b38c7e673f7c5b210daa118d8acdb99c067579`).
- **H48 acquisition queue** (`queue_canonical_sha256` `38c099db5c233222cc51f39348f06e933871337b807d4761512d2800ec2375c7`).
- **H50 wave-B window trim** (file sha256 `5aed05f1615a3cc2983c6e1be86ef9f35306aed7cfab86aea9f1d8fab9f61e66`, `trim_canonical_sha256` `b43f71bf239254152288b8eaf89a7748680117c7ecc10a16564c4a9b6a115a5d`): source of each asset's `admissible_study_months` and `dropped_required_months`.
- **H40 feasibility** (`study_months`, 46 months `2023-01`..`2026-10`) as context.

Frozen DISP-003 artifacts (canonical forward block `7234fc4e...`, H10 fresh block `324ab1e6...`, universe frontier `9ba08f3f...`, grid v3 config `1ff4c1f2...`) are only hashed before/after, never written.

## 3. Scope — wave B (ark, astr) trimmed months only

- assets: `ark`, `astr` (2)
- kinds: `klines`, `funding` (2)
- months per asset: exactly the H50 `admissible_study_months` (read from the artifact, not hard-coded)
- expected files: **166** (ARK 76 = 38 × 2, ASTR 90 = 45 × 2)

**Exclusions declared before computation:**
- Wave A (7 assets, 644 files): acquired as H49; not re-fetched.
- ALPHA (92 files): excluded under the H47 no-backfill rule; never fetched.
- The 18 H50 `dropped_required_months` files (ARK `2023-01..2023-08`, ASTR `2023-01`): **never fetched**; these months are removed from the selection set and a scope check fails the run if any appears.
- Any month outside the H50 admissible windows or outside the 46 H40 study months.
- No `probe_month=2026-11` re-probe; that window remains date-gated to **2026-11-30**.
- No panel construction, no returns/spreads/states/p-values/costs/inference, no promotion, no sealed holdout access.

## 4. Acquisition controls

1. **Strict allowlist.** A URL is fetched only if it appears verbatim in the pinned H41 plan for a selected `(asset, kind, month)` and starts with the documented free archive base `https://data.binance.vision/data/futures/um/`. Any other URL is refused and recorded.
2. **Bounded retries.** At most 3 attempts per file, 20 s per request timeout, 8 workers.
3. **Per-file evidence.** For every response: HTTP status, content-length header, sha256 of the received bytes, byte count, and stdlib `zipfile`/`csv` content checks — exactly one CSV member, documented first header field (`open_time` for klines, `calc_time` for funding), at least one data row, integer timestamps monotonically non-decreasing.
4. **No fabrication.** Absent or malformed files stay absent/malformed and are reported; nothing is interpolated, backfilled or forward-filled.
5. **Raw-byte cache outside version control.** Bytes are written only under the gitignored `data/panel_archive_wave_b/`; the committed artifact carries hashes and content evidence only.
6. **Scope guard before any network I/O.** All pinned digests and the derived 166/76/90 counts must match, or the run aborts with no fetch.

## 5. Pre-declared verdicts (outcome-blind)

- `WAVEB_SCOPE_MISMATCH` — a pinned input digest fails, the derived wave-B asset set is not exactly {`ark`,`astr`}, the trimmed month set differs from the H50 admissible months, the expected count is not 166 (76/90 per asset), or any selected file falls outside an asset's admissible window.
- `WAVEB_ACQUISITION_INCOMPLETE` — scope is correct but any expected file lacks HTTP 200, a sha256, or `content_ok`.
- `WAVEB_ACQUISITION_COMPLETE` — all 166 expected files fetched with HTTP 200, hashed, and content-verified; zero missing and zero extra keys.

No threshold, ordering or label depends on any price, return, dispersion state or other outcome.

## 6. Expected result (pre-declared from H43/H48/H50 — not re-derived)

166/166 files served with HTTP 200 and content-verified (ARK 76, ASTR 90); 0 missing, 0 extra; no wave-A or ALPHA file fetched; no dropped pre-listing month fetched. This section records the expectation so a contradicting observation stays visible; section 5 decides the verdict.

## 7. Non-claims

- Raw archive acquisition is not market evidence and is not an economic result.
- No panel, no signals, no returns/spreads/states/p-values/costs/inference, no multiple-testing correction is performed here.
- No candidate is promoted; no confirmatory claim is made; the H10 confirmatory gate is unchanged and still date-gated to 2026-11-30.
- No frozen DISP-001/002/003 artifact, config, ledger, panel or forward block is modified; the sealed holdout is not opened.
- A green test suite proves only what the tests cover.

## 8. Verification plan

- Unit tests: hermetic fixtures for selection (admissible months only, dropped months excluded, ALPHA/wave-A excluded, deterministic ordering), allowlist refusal, content-integrity accept/reject branches (bad zip, wrong header, empty, non-monotone timestamps), reconciliation and verdict branches; plus committed-input and committed-artifact integration checks.
- `python3 -m compileall -q scripts tests` and the full `python3 -m unittest discover -s tests` suite.
- Re-record the verified test claim, session verification record, registry H51 entry, contract pin bump to 51, and frozen-hash re-verification.

## 9. Change log

- v1 (2026-11-18T22:25:05Z): initial preregistration. Consumes the H50 trim decision unchanged; no outcome-informed choice; acquisition scope fixed at the 166 trimmed files before any byte is fetched.
