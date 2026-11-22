# POINTINTIME-ELIG-001 (H57) — Point-in-time cap eligibility of the committed DISP-003 panel inventory

- **Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-POINTINTIME-ELIG-001
- **Hypothesis ID:** H57
- **Status:** EXPLORATORY_ONLY
- **Label:** source_coverage_point_in_time_eligibility
- **Created:** 2026-11-22T04:00:20Z (preregistered before any figure in this file was computed)
- **Program:** HARMONY-CRYPTO-EDGE-004

## Motivation and distinctness

H56 (`PANELNORM-WAVEA-001`) normalised the 644 H49 wave-A archives into 14 DISP-003-schema
panels and reported a descriptive concurrent-breadth inventory over the declared committed panel
inventory: `>= 20` assets with at least one klines observation in every study month, including
35-39 in the fresh window 2025-01..2026-10. H56 explicitly flagged that this breadth is a
**coverage fact over committed panels, not a proven point-in-time eligibility or rank fact**
(`universe_frontier.json` `historical_rank_coverage_state = NOT_PROVEN_COMPLETE`), and named the
highest-value bounded no-cost next step:

> a read-only point-in-time eligibility/rank-provenance audit of the committed DISP-003 panel
> inventory establishing whether the breadth>=20 fresh-window coverage is point-in-time eligible;
> today's ranks must never be backfilled as historical ranks, and no outcome may be computed on
> coverage alone.

This experiment performs exactly that audit. It is a distinct, bounded, read-only, no-network
measurement. It computes **no forward return, no realized spread, no dispersion state, no cost,
no p-value and no inference**. It is a coverage/eligibility measurement (adaptive research-gate
policy v1 §3, last relaxation option), not an outcome estimate.

The binding confirmatory action remains date-gated: H10's fresh sealed block matures on/after
2026-11-30. Nothing here advances, replaces or unlocks that track.

## Inputs (pinned, read-only)

- Committed klines panel inventory (three declared directories, read only for the daily `open_time`
  index and the first/last covered date):
  - `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/binance_klines_*.csv` (legacy 32)
  - `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-WAVEB-001/panels/binance_klines_*.csv` (ARK/ASTR)
  - `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-WAVEA-001/panels/binance_klines_*.csv` (ALICE/ANKR/APE/API3/APT/AR/ARPA)
- Point-in-time cap observations, read only:
  - `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/marketcap_panel.csv`
    (`CapMrktEstUSD`, authoritative for the 32 legacy assets)
  - `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/raw/coinmetrics_candidates/*_CapMrktEstUSD.json`
    (per-date `CapMrktEstUSD` for the 9 extension assets)
- Frozen hashes re-verified before any figure is trusted: canonical forward block, h10_fresh block,
  grid v3 config, universe frontier. All four must be byte-identical before and after.

No network I/O. No archive fetch. No writes outside the audit JSON under this experiment root.

## Symbol and month conventions (deterministic)

- `symbol -> asset`: lowercase, strip the trailing `USDT` quote (e.g. `1INCHUSDT -> 1inch`,
  `BTCUSDT -> btc`). Every committed klines symbol is a USD-M `USDT` pair.
- Fresh window: the 22 calendar months `2025-01..2026-10`. The per-month formation date is the
  last calendar day of the month (UTC), matching the monthly formation phase.
- An asset is `klines_covered` in a month when its klines panel has >= 1 observation inside that
  UTC month.
- An asset is `strict PIT cap-eligible` at a month-end date `d` when it has a cap observation whose
  date equals `d` (same-day; no forward fill).
- An asset is `as-of PIT cap-eligible` at `d` (7-day staleness) when it has a cap observation with
  date `<= d` and `>= d - 7 days` (most recent prior observation, never a future backfill).

## Predeclared measurements (deterministic)

**M1 — inventory resolution.** For each of the committed klines symbols report: asset id, panel
group, klines first/last covered date, row count, whether it covers each fresh-window month, the
cap source(s) that carry it, cap first/last date, observation count, distinct-date count,
distinct-value count, and whether the cap series carries a **snapshot signature** (fewer than 2
distinct dates, fewer than 2 distinct values, or a cap `last` date on/after today's UTC date).

**M2 — per-month PIT breadth.** For each fresh-window month report the number of assets that are
both `klines_covered` and `strict` cap-eligible at the month end, and the number that are
`klines_covered` and `as-of` (7-day) cap-eligible, plus the explicit missing-asset list with the
reason (`nokline`, `nocap`, `cap_end=<date>`).

**M3 — summary.** `min`/`p50`/`max` of the per-month strict and as-of breadth, the count of
months with strict breadth `>= 20`, the count with as-of breadth `>= 20`, and the list of panel
assets whose klines do not reach the fresh window.

**M4 — rank provenance.** Whether the committed panel inventory constitutes a proven point-in-time
market-cap rank universe. It does not: a rank requires the full eligible population on each date,
and `universe_frontier.json` records `historical_rank_coverage_state = NOT_PROVEN_COMPLETE` with
`last_verified_historical_rank = null`. Report this explicitly; never backfill today's rank.

## Predeclared verdict rules (outcome-blind)

Let `MIN_BREADTH = 20` (the registered outer-decile arity requirement, H55).

- `POINT_IN_TIME_ELIGIBLE` when **all** hold:
  1. every committed klines symbol resolves to a cap source;
  2. no resolved cap series carries a snapshot signature (all have >= 2 distinct dates and > 1
     distinct value and a `last` date strictly before today);
  3. `min` per-month **strict** breadth over the fresh window `>= MIN_BREADTH`;
  4. `min` per-month **as-of** breadth over the fresh window `>= MIN_BREADTH`.
- `POINT_IN_TIME_LIMITED` otherwise; every failing condition is reported with its count.
- The cap-eligibility label is reported separately from `rank_provenance`, which is always
  `NOT_PROVEN_COMPLETE` here (a coverage/eligibility fact, never a rank claim).

## Explicit non-claims

- Not market evidence, not an economic result, not a candidate evaluation.
- No forward return, realized spread, dispersion-state outcome, cost, funding PnL, p-value,
  confidence interval or multiplicity correction is computed.
- No candidate promoted; `confirmatory_claim_allowed = false`; the H10 fresh sealed block stays
  date-gated to 2026-11-30 and is not read for outcomes.
- Does not alter any frozen DISP-001/002/003 artifact, config, ledger, panel, forward block or
  frontier, and does not unlock H1/H6/H7/H10.
- A cap observation is point-in-time **coverage**, not proof that a correct historical market-cap
  rank can be formed from this inventory; today's ranks are never backfilled as historical ranks.
- A green test suite proves only what the tests cover.

## Artifacts

- Script: `scripts/pointintime_eligibility_audit.py`
- Audit: `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-POINTINTIME-ELIG-001/integrity_audit/H004V106_pointintime_eligibility_<utc>.json`
- Test: `tests/test_pointintime_eligibility_audit.py`
- Registry: H57 appended; `next_sequence_number` bumped to 57.