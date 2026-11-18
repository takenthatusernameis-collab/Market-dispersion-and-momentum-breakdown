# Panel-Coverage Acquisition Queue — bounded wave split and per-study-month utility of the H47 roster

**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-QUEUE-001
**Hypothesis ID:** H48 (allocated in this session)
**Status:** PREREGISTERED (before computation)
**Created:** 2026-11-18T20:25:00Z
**Type:** EXPLORATORY_ONLY — descriptive source-coverage/planning adjudication over already-committed artifacts

---

## 1. Purpose and trigger

H47 (PANELCOV-NARROW-001) converted the H43 probe into an asset-level roster: 9 of
the 10 H41 extension assets are `INCLUDED` and ALPHA is `EXCLUDED`. It recorded
per-asset served windows and `n_required_months_outside_verified_window`, but it
did **not** produce an acquisition decision: which included assets can be acquired
as-is, which require a declared window trim first, how many archive files each
wave needs, and which of the 46 required study months each included asset can
actually populate.

Those are the questions an acquisition step must answer before any file is
fetched, and they are answerable purely from committed evidence (H41 plan, H43
probe, H47 roster, H40 study window). No network, no downloads, no panels, no
outcomes.

## 2. Inputs (read-only)

- **H47 roster** (per-asset `included` flag, `served_window`, `absent` classes):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-NARROW-001/integrity_audit/panel_coverage_eligibility_roster_20261118T191152Z.json`,
  whose `roster_canonical_sha256` must equal
  `171cd174d527ff34c9ba0162f2b38c7e673f7c5b210daa118d8acdb99c067579`.
- **H41 acquisition plan** (920 `plan_entries`; required study months per asset):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001/integrity_audit/H004V106_panel_acquisition_plan_20261116T085222Z.json`
- **H43 archive probe** (920 `per_entry` with `http_status`):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PROBE-001/integrity_audit/H004V106_panel_archive_probe_20261116T142247Z.json`
- **H40 feasibility** (`study_months`, `study_window`; context only):
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-FEAS-001/integrity_audit/H004V106_panel_coverage_extension_feasibility_20261116T215857Z.json`

All are existing committed artifacts and are read-only here.

## 3. Estimand (descriptive counts only)

For each H47-`included` asset:

1. `required_months` = the H41 planned months for that asset that lie inside the
   H40 study window (the 46 study months `2023-01` .. `2026-10`).
2. `absent_required_months` = required months where **either** required kind
   (`klines`, `funding`) is not HTTP 200 in the H43 probe. Uses verified per-file
   probe evidence, not window arithmetic.
3. `wave`:
   - `WAVE_A_UNCONDITIONAL` — no absent required month: every required
     `(kind, month)` file is verified served, so acquisition needs no window
     trim and no backfill.
   - `WAVE_B_REQUIRES_WINDOW_TRIM` — at least one absent required month: the
     affected months are listed; acquiring this asset is admissible only after a
     separately preregistered window-trim decision.
4. `n_planned_files` (`2 * len(required_months)`) and `n_served_planned_files`
   (verified HTTP 200 count).

Wave-level and per-study-month aggregates:

5. `wave_file_counts`: planned / served / absent file counts per wave.
6. `monthly_utility`: for each of the 46 study months, the sorted list of
   included assets whose **both** required kinds are HTTP 200 that month (wave A
   and wave A+B variants), and their counts.
7. `reconciliation`: `wave_A_files + wave_B_files + excluded_files == 920`.

## 4. Pre-declared decision rule (outcome-blind)

- `QUEUE_JOIN_MISMATCH` — the H47 roster's canonical hash does not match the
  pinned value, or an included asset has no H41 plan entries.
- `QUEUE_NO_UNCONDITIONAL_WAVE` — wave A is empty.
- `ACQUISITION_QUEUE_READY` — otherwise.

No threshold, ordering or label depends on any outcome. The rule only reads
file-availability statuses already recorded by H43.

## 5. Expected (pre-declared from H47 — not re-derived)

H47 recorded 9 included assets (7 fully served, 2 pre-listing-only) and ALPHA
excluded. Expected here: wave A = the 7 fully served assets (644 planned files),
wave B = ARK and ASTR (184 planned files, 18 absent: ARK 16, ASTR 2), excluded
ALPHA = 92 planned files, 644 + 184 + 92 = 920, decision
`ACQUISITION_QUEUE_READY`. This section records the expectation so a
contradicting result stays visible; section 4 decides the verdict.

## 6. Non-claims

- Does not acquire, download, fabricate or forward-fill any archive file.
- Does not construct a panel or compute returns/spreads/states/p-values/costs/
  inference; does not promote any candidate.
- Does not re-probe the date-gated `2026-11` cutoff month or any other endpoint.
- Does not alter the confirmatory expanding-universe arm or any frozen
  DISPERSION-001/002/003 artifact, config, ledger or forward block.
- Cannot validate, replace or unlock H1/H6/H7/H10 or any confirmatory track.
- The next authorized confirmatory action remains the H10 fresh-block maturity
  on/after 2026-11-30.

## 7. Artifacts

- Script: `scripts/panel_coverage_acquisition_queue.py` (stdlib only, import-safe,
  `--out` writes only on explicit invocation).
- Test: `tests/test_panel_coverage_acquisition_queue.py` (hermetic synthetic
  fixtures for every rule branch + skip-guarded integration on committed inputs).
- Output: `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-QUEUE-001/integrity_audit/panel_coverage_acquisition_queue_<computed_utc>.json`
