# PANELNORM-WAVEA-001 v1 — wave-A extension panel normalization

- Hypothesis: H56
- Experiment id: `HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-WAVEA-001`
- Status: `EXPLORATORY_ONLY` (source-coverage normalization)
- Created: 2026-11-20T05:55:51Z — **before** any panel byte or coverage figure was computed
- Preregistration precedes the artifact: the artifact JSON recorded by
  `scripts/panel_wave_a_normalization.py --execute` must carry a
  `computed_utc` strictly after this `Created` stamp.

## Question

H55 (`BREADTH-ARITY-001`) closed the 2-asset route by construction and named
breadth acquisition as the binding constraint: the registered outer-decile
dispersion rule needs >= 20 concurrently priced point-in-time eligible assets,
and wave B alone supplies only ARK/ASTR (breadth 2) in 2025-01..2026-10.
H49 already acquired the raw bytes for the 7 fully served wave-A extension
assets (ALICE, ANKR, APE, API3, APT, AR, ARPA; 644 monthly archives covering
the 46 H40 study months 2023-01..2026-10), but those bytes were never
normalized into DISP-003-schema panels, so their usable breadth contribution is
unknown.

This study asks one descriptive coverage question only: can the 644 H49
wave-A archives be reconciled byte-for-byte and normalized into 14
DISP-003-schema panels (7 assets x 2 kinds) without any interpolation,
backfill or silent row loss, and what concurrent asset breadth does the
resulting panel inventory support per study month?

## Pre-declared scope

- Assets: exactly `alice, ankr, ape, api3, apt, ar, arpa` (H48 wave-A set).
  Wave B (`ark`, `astr`) and excluded `alpha` are **out of scope** and must not
  appear in any selected record.
- Kinds: `klines`, `funding`.
- Months: the 46 study months declared by the H49 `scope_declaration`
  (2023-01..2026-10). No month outside that window is fetched or normalized.
- Expected inputs: 644 archives, 92 per asset (46 months x 2 kinds).
- Data vintage: the H49 acquisition audit is the single source of truth for
  URL, archive path and sha256. Nothing is re-derived from today's listings or
  today's market-cap ranks.

## Method (pre-declared, outcome-blind)

1. Re-verify the pinned input digests (H49 audit file sha256 and the canonical
   sha256 of its 644 records) before any write. Abort on mismatch.
2. Re-fetch only the 644 URLs pinned in the H49 records into the gitignored
   cache `data/panel_archive_wave_a/`. Each response must be HTTP 200 and its
   sha256 must equal the digest H49 recorded; any mismatch is reported as a
   reproducibility failure, never patched.
3. Re-validate every archive with stdlib `zipfile`/`csv`: exactly one csv
   member, documented header, >= 1 data row, non-decreasing integer timestamps.
4. Restrict rows to their source month's UTC half-open window; count (never
   collapse) duplicate timestamps across months.
5. Render 14 panels with the DISP-003 schema already used by the committed
   legacy (DISP-001/003) and H53 wave-B panels.
6. Coverage accounting: per study month, count the assets that have both kinds
   served, over the declared inventory (committed DISP-003 panels + H53 wave-B
   panels + these wave-A panels). Reported counts are coverage, not evidence.

## Pre-declared verdict rule

- `PANELNORM_WAVEA_SCOPE_MISMATCH` if any pinned digest fails, the derived
  asset/kind/month scope differs from the declaration above, or the panel count
  is not 14.
- `PANELNORM_WAVEA_INCOMPLETE` if any archive is missing, fails its H49
  sha256, is content-invalid, leaves a declared month uncovered, contributes an
  out-of-window row, or produces a duplicate timestamp.
- `PANELNORM_WAVEA_COMPLETE` only when all 644 archives reconcile into 14
  panels with exact row accounting.

## Explicit non-claims

- Panels are not market evidence. No returns, spreads, dispersion states,
  p-values, costs, funding-adjusted outcomes or inference are computed.
- No candidate is promoted; no confirmatory claim is allowed; the H10 sealed
  block remains date-gated to 2026-11-30 and is not touched or matured here.
- Historical point-in-time eligibility is unchanged: the current market-cap
  snapshot is never labeled historical ranking truth and no rank is backfilled.
- Frozen DISP-001/002/003 artifacts, configs, ledgers, committed panels, the
  canonical forward block and the frontier stay byte-identical.
- The wave-A bytes are a re-fetch of the H49 endpoint for reproducibility of an
  already-completed acquisition; this is not a new attempt at a failed gate and
  cannot substitute for a fresh mechanism test.
