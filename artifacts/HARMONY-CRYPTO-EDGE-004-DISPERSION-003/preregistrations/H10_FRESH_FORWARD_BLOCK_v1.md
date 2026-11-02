# Preregistration — H10 Fresh Sealed Forward Block (DISP-003-H10)

**Program:** HARMONY-CRYPTO-EDGE-004
**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-H10
**Status:** EXPLORATORY_ONLY / BLOCKED (data availability)
**Created:** 2026-11-02T09:43:30Z
**Author:** automated research agent (this session)

## 1. Why this experiment exists (trigger)

The canonical H004V106 sealed forward block (cutoff 2026-09-30, last formation
2026-08-31, 608 formations, high_low_diff_net_1x +0.6165) is development /
exploratory evidence only: it is a strict subset of the grid ledger's
development window and was already inspected, so it is NOT a fresh holdout and
NOT independent confirmation. H6 / H7 require confirmation on a genuinely fresh
sealed forward block with formations after 2026-09-29. The October 2026 Binance
archive published (both monthly klines AND monthly fundingRate HTTP 200) during
the 2026-11-02T09:21:04Z probe (record research_state/cutoff_probe/cutoff_probe_20261102T092118Z.json),
so the cutoff gate is UNBLOCKED and historical data now runs through 2026-10-31.
H10 is the predeclared fresh-block test.

This preregistration locks the methodology BEFORE any fresh-block computation,
per the confirmatory-track rule: freeze a mechanism, endpoint, grid and
decision criteria first; test a selected candidate only on a new sealed future
block.

## 2. Question and estimand

**Question:** On genuinely fresh forward data (formations strictly after
2026-09-29), what is the high-minus-low net-1x dispersion-momentum spread
difference, its HAC/overlap-aware uncertainty, and does it exceed a
predeclared economic-significance threshold and survive Holm correction across
the cell family?

**Estimand:** mean(high spread_net_1x) - mean(low spread_net_1x) over the
fresh sealed forward block, with overlap-aware (month-cluster / HAC)
uncertainty on completed 30-day forward outcomes only.

## 3. Method (frozen before computation)

1. Confirm the cutoff gate is UNBLOCKED (real probe, both October 2026 monthly
   klines AND monthly fundingRate HTTP 200).
2. Run `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31`
   (free public data only). This advances panels to 2026-10-31; it does NOT
   modify the canonical forward block.
3. Re-run `python3 -m unittest discover -s tests`; verify suite green apart from
   the documented, expected post-refresh input-hash consistency result
   (test_forward_block_hashes_match_files_on_disk fails because the canonical
   block's recorded panel input hashes are pre-October while panels advanced --
   this is the correct signal that the cutoff advanced past the frozen block;
   do NOT tamper with the canonical block).
4. Verify canonical H004V106 unchanged: sha256
   `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`,
   n_formations 608, high_low_diff_net_1x +0.6165223953929935,
   date_last 2026-08-31, block_sealed True, data_cutoff_utc
   2026-09-30T00:00:00Z.
5. Seal the fresh forward block to a SEPARATE directory (never the canonical
   `forward_block/` path):
   `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30
   --data-cutoff 2026-10-31 --output-dir <fresh dir>`
   -- formations strictly after 2026-09-29, strict 30-day maturity
   (last_allowed_formation = cutoff - 30 days; no truncated outcomes),
   HAC/overlap-aware uncertainty on completed outcomes only.
6. Report n_formations, n_high, n_low, n_mid, date_first, date_last,
   last_allowed_formation_date, high_low_diff_net_1x, high_low_diff_gross,
   block_sealed, block_sealing_rule, and the HAC/overlap-aware interval.

## 4. Decision rule (predeclared)

- A confirmatory claim requires BOTH:
  (a) |high_low_diff_net_1x| above a predeclared economic-significance threshold
      (after costs), AND
  (b) Holm-significance across the complete declared multiple-testing family.
- Neither raw p-values nor return alone may promote a winner.
- If the fresh block cannot be built (e.g. fewer than MIN_ASSETS_DECILES=20
  assets have complete 30-day forward horizons because October price panels are
  incomplete), label the result BLOCKED / EXPLORATORY_ONLY, record the blocker
  with the exact unmet requirement, and do NOT relax maturity or the asset
  minimum. Do not loop on a known failure.
- In all branches the result is EXPLORATORY_ONLY until the original
  confirmatory gates are met on admissible data with complete
  multiple-testing correction and independent recomputation.

## 5. Safeguards (not relaxed)

- No look-ahead: formations strictly after 2026-09-29; no outcomes computed
  before they are complete (strict 30-day maturity).
- No forward-fill, no synthetic data, no invented fills, no silent sample
  exclusions, no paid sources, no live / paper trading.
- The canonical forward block is read-only and is NOT re-sealed. The fresh
  block writes to a separate output dir. Nothing in `forward_block/`,
  `grid_checkpoints/`, `grid_result_ledger.json`, `grid_summary.json`,
  DISPERSION-001 or DISPERSION-002 is touched.
- October 2026 ranks are NOT backfilled as historical ranks; the fresh block's
  universe/coverage is stated explicitly and narrower if required.

## 6. Expected output

- Fresh sealed forward block artifact under a new output dir
  (e.g. `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10/`),
  new preregistration record here, registry entry H10 (next_sequence_number
  9->10), run-manifest entry, frontier/handoff update.

## 7. Blocker encountered at creation time (2026-11-02)

The fresh block build was ATTEMPTED and returned BLOCKED: "no formations passed
the data gate." Root cause: only BTCUSDT and ETHUSDT have October 2026 price
panels (the other 30 Binance klines panels end 2026-09-30 because their October
monthly zips are unpublished), so the maximum number of eligible assets with a
complete 30-day forward horizon is 2, which is below MIN_ASSETS_DECILES=20.
H10 therefore cannot be evaluated with current data. It remains
CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / BLOCKED. The blocker is preserved;
the next agent should retry the fresh sealed block once >=20 assets have
complete October 2026 price panels, and must not relax the 30-day maturity or
the asset minimum to force a result.

## 8. Open questions for the next agent

- When do >=20 assets obtain complete October 2026 price panels (their October
  monthly zips publish), and does the fresh block then pass the data gate?
- If the fresh block builds, is |high_low_diff_net_1x| above the economic
  threshold and Holm-significant across the cell family? (Do not promote from
  raw p-values or return alone.)
