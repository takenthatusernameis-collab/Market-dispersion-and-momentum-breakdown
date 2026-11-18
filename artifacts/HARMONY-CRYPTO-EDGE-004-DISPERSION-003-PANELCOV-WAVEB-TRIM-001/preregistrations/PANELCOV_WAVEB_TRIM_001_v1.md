# Wave-B (ARK/ASTR) Explicit Window-Trim Decision — bounded, read-only, no-fetch planning

**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-WAVEB-TRIM-001
**Hypothesis ID:** H50 (allocated in this session)
**Status:** PREREGISTERED (before any computation; read-only over committed evidence only)
**Created:** 2026-11-18T21:35:00Z
**Type:** EXPLORATORY_ONLY — source-coverage window-trim decision (design/planning; no market data fetched, no outcomes computed)

---

## 1. Purpose and trigger

H48 (PANELCOV-QUEUE-001) ended the exploratory coverage chain at a ready bounded acquisition queue:

- **wave A** = ALICE, ANKR, APE, API3, APT, AR, ARPA — 644 planned files, all verified served, unconditional acquisition (executed as H49: 644/644 fetched and content-verified).
- **wave B** = ARK, ASTR — 184 planned files, **18 absent**: ARK 2023-01..2023-08 both kinds (16 files, all BEFORE_FIRST_SERVED HTTP 404), ASTR 2023-01 both kinds (2 files, all BEFORE_FIRST_SERVED HTTP 404). Wave B is admissible **only after a separately preregistered window trim** — no fetches may run until that trim is registered.
- **ALPHA** = 92 files excluded under the H47 no-backfill rule.

H48 stopped at planning and left the wave-B trim decision unmade. This study makes it: a NEW-ID, bounded, no-cost, EXPLORATORY_ONLY decision declaring exactly which of the 46 required study months (2023-01..2026-10) are admissible for ARK and ASTR without backfill, and exactly what the trimmed window loses. It is not a repeat of any inspected endpoint: no prior session registered this trim, and no wave-B byte has ever been fetched.

This study is **read-only planning**: it consumes only the committed H47 eligibility roster, the H48 acquisition queue, the H43 probe and the H41 plan. It fetches nothing, downloads nothing, builds no panel, and computes no returns/spreads/states/p-values/costs/inference. Acquisition of the trimmed wave-B files, if ever pursued, is a separate, later-authorized step.

## 2. Inputs (read-only, pinned)

- **H47 eligibility roster** (`roster_canonical_sha256` = `171cd174d527ff34c9ba0162f2b38c7e673f7c5b210daa118d8acdb99c067579`):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-NARROW-001/integrity_audit/panel_coverage_eligibility_roster_20261118T191152Z.json`
  — per-asset served windows (`first`/`last` month per kind with HTTP 200) and absence classifications.
- **H48 acquisition queue** (`queue_canonical_sha256` = `38c099db5c233222cc51f39348f06e933871337b807d4761512d2800ec2375c7`):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-QUEUE-001/integrity_audit/panel_coverage_acquisition_queue_20261118T201951Z.json`
  — wave labels (WAVE_B_REQUIRES_WINDOW_TRIM for ark, astr) and per-asset planned/served/absent counts.
- **H43 archive probe** (920 `per_entry` with `http_status`):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PROBE-001/integrity_audit/H004V106_panel_archive_probe_20261116T142247Z.json`
- **H41 acquisition plan** (920 `plan_entries`, authoritative archive URLs):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001/integrity_audit/H004V106_panel_acquisition_plan_20261116T085222Z.json`
- **H40 feasibility** (`study_months`, 46 months `2023-01`..`2026-10`).

Frozen DISP-003 artifacts (canonical forward block, h10 fresh block, universe frontier, grid v3 config) are only hashed before/after, never written.

## 3. Scope — wave B (ARK, ASTR) only, no backfill

Pre-declared expected scope, fixed before computation from H47/H48 evidence:

- assets: `ark`, `astr` (2)
- kinds: `klines`, `funding` (2)
- months: the 46 study months
- planned files: 2 x 2 x 46 = **184**

**Exclusions, declared before computation:**
- Wave A (7 assets, 644 files): acquired as H49; not part of this decision.
- ALPHA (92 files): excluded under the H47 no-backfill rule; not part of this decision.
- Any month outside the H40 study window. Not considered here.
- No `probe_month=2026-11` re-probe; that window remains date-gated to **2026-11-30**.
- No network access, no HEAD probe, no content downloaded.

## 4. Pre-declared trim rule (outcome-blind)

For each wave-B asset, the **verified served window** is the intersection, over both required kinds, of months with an HTTP 200 probe record, bounded by the 46 study months:

`served_window(asset) = [max(first_klines, first_funding), min(last_klines, last_funding)] ∩ study_months`

An asset's **admissible study months** = `served_window(asset)`. Required study months outside it (classified BEFORE_FIRST_SERVED or AFTER_LAST_SERVED with HTTP 404 in H47) are **dropped, never backfilled, never fetched**. The trimmed acquisition plan for a wave-B asset contains exactly `2 * |admissible months|` planned files, all within the served window.

Pre-declared verdicts:

- `TRIM_SCOPE_MISMATCH` — the derived wave-B asset set does not equal {ark, astr} or an expected asset lacks an H41 plan entry or H47 roster record.
- `TRIM_DECISION_RECORDED` — admissible months and dropped months are declared per asset from verified served windows only; no file outside a served window is planned; no fetch is performed.

No threshold, ordering or label depends on any price, return, dispersion state or other outcome. The rule reads probe status and served windows only.

## 5. Expected decision (pre-declared from H47/H48 — not re-derived)

From the committed H47 roster and H48 queue:

- **ARK**: served window klines [2023-09, 2026-10], funding [2023-09, 2026-10] → admissible study months **2023-09..2026-10** = 38 months = **76 planned files**, all servable within the trimmed window; drops 2023-01..2023-08 = 8 months = **16 files** (all BEFORE_FIRST_SERVED HTTP 404). The trim loses no served data: all 16 dropped files were never served.
- **ASTR**: served window klines [2023-02, 2026-10], funding [2023-02, 2026-10] → admissible study months **2023-02..2026-10** = 45 months = **90 planned files**, all servable within the trimmed window; drops 2023-01 = 1 month = **2 files** (all BEFORE_FIRST_SERVED HTTP 404). The trim loses no served data.
- Trimmed wave B total: **166 planned files, 166 servable, 0 absent within the trimmed window**; 18 pre-listing placeholder files dropped (never served, HTTP 404).

This section records the expectation so a contradicting result stays visible; section 4 decides the verdict.

## 6. Non-claims

- Does not construct a panel, estimate any effect, or make any confirmatory or economic claim.
- Does not validate, replace or unlock H1/H6/H7/H10 or any confirmatory track.
- Does not fetch any archive file; wave-B acquisition (if ever authorized) remains a separate later step and must not be represented as evidence produced here.
- Does not alter the confirmatory expanding-universe arm or any frozen DISP-001/002/003 artifact, config, ledger or forward block.
- The next authorized confirmatory action remains the H10 fresh-block maturity on/after **2026-11-30**.

## 7. Artifacts

- Script: `scripts/panel_wave_b_window_trim.py` (stdlib only, import-safe; pure selection/trim/verification helpers; writes only under `--out`).
- Test: `tests/test_panel_wave_b_window_trim.py` (hermetic trim-rule fixtures + skip-guarded integration on the committed artifact).
- Output: `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-WAVEB-TRIM-001/integrity_audit/panel_wave_b_window_trim_<computed_utc>.json`.

## 8. Change log

- v1 (2026-11-18): initial preregistration, allocated before any computation. Scope, trim rule, exclusions and expected counts fixed from H48/H47/H43/H41 evidence.
