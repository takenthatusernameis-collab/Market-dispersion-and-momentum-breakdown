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

## 4.1. Sequential looks and alpha-spending (added 2026-11-04T22:45Z)

H10 is re-evaluated each calendar month as the Binance archive publishes
(November 2026, December 2026, ...). Each re-evaluation with a wider formation
window is a sequential look at the same estimand, so research protocol 6
requires a predeclared alpha-spending rule rather than reusing a fixed 0.05 on
every look:

    "For future ongoing blocks, freeze each new block and evaluate it once.
    Number sequential looks and apply a predeclared alpha-spending rule such as
    alpha_k = 0.05 / (k * (k + 1))."

This section is the single declaration of that rule for H10. It is added before
any mature outcome exists, so it cannot be outcome-informed.

- **Rule:** `alpha_k = 0.05 / (k * (k + 1))`, with k the 1-based sequential look
  number at which the fresh block is evaluated.
- **Declared per-look values:**
  - k=1 -> alpha_1 = 0.025, cumulative_spend = 0.025, remaining_budget = 0.025
  - k=2 -> alpha_2 = 0.05/6, cumulative_spend = 0.025 + 0.05/6,
    remaining_budget = 0.05 - (0.025 + 0.05/6)
  - The series sums to 0.05 over k = 1..inf, so the family-wise error rate is
    controlled at the declared family alpha 0.05 in the limit and is strictly
    below it for any finite number of looks.
- **Look counter semantics:** k counts completed evaluations of the fresh block
  that produced an outcome (n_high>0 AND n_low>0). An evaluation that returns
  IMMATURE (n_high=0 or n_low=0, high_low_diff_net_1x = null) produces no
  inference and does NOT advance the counter; the next mature evaluation is
  still look k, not k+1. A skipped look consumes no budget.
- **Inference rule:** a confirmatory claim on the fresh block requires BOTH
  section 4(a) (|high_low_diff_net_1x| above the predeclared economic-
  significance threshold after costs) AND section 4(b) (Holm-significance across
  the complete 216-cell family) evaluated at the per-look alpha_k for the current
  look number, NOT at a fixed 0.05. The Holm correction itself is unchanged and
  always spans the complete declared family; the alpha-spending rule only sets
  the per-look significance level against which the Holm-adjusted p-value is
  compared.
- **Implementation:** scripts/alpha_spending.py is the single implementation
  (pure arithmetic, no market data, stdlib-only). Guard:
  tests/test_h10_sequential_alpha_spending.py asserts the prereg text and the
  module agree on the rule and on the k=1 and k=2 values, and that cumulative
  spend stays below the family budget.
- **Not relaxed:** no look-ahead, no outcome-informed choice of k, no reuse of an
  inspected holdout, no lowering of the family alpha to manufacture a pass.

## 4.2. Quantified economic-significance threshold (added 2026-11-07T06:27Z)

Section 4(a) requires `|high_low_diff_net_1x|` to be "above a predeclared
economic-significance threshold (after costs)" but stated no number, so no
outcome could ever satisfy or fail criterion 4(a): the confirmatory gate was
structurally undecidable. This section supplies the number. It is added before
any mature fresh-block outcome exists, so it cannot be outcome-informed.

- **Endpoint is already net of cost.** `high_low_diff_net_1x` =
  mean(high spread_net_1x) - mean(low spread_net_1x), where
  `spread_net_1x = spread_gross - COST_1X` and `COST_1X = 0.001` per side-pair
  (BASE_COST_TURN 0.0005 x 2, scripts/eval_forward_block.py:43-44). The
  threshold therefore applies to a cost-adjusted quantity; no further cost
  deduction is made at the decision step.
- **Declared threshold:** a confirmatory claim requires
  `|high_low_diff_net_1x| >= ECONOMIC_SIGNIFICANCE_THRESHOLD = 0.05`, i.e. a
  net high-minus-low spread of at least 5% per 30-day formation cohort, in
  either direction. The sign is NOT pre-registered: H1's registered prediction
  is negative, but H10's estimand is the magnitude of the spread on genuinely
  fresh data, and a positive result is a candidate for a separately registered
  hypothesis (H2/H7), never a retroactive rewrite of H1.
- **Why 0.05.** It is ~50x the per-formation cost (0.001) embedded in the
  endpoint, so it cannot be satisfied by costless noise; it annualizes to roughly
  20%+ over the 30-day formation cadence, a conservative bar for a
  dispersion-conditioned cross-sectional momentum spread. It is a round,
  mechanism-agnostic, predeclared number, chosen in ignorance of every observed
  outcome -- including the canonical H004V106 block's +0.617, which is
  development/exploratory evidence and is NOT an input to this threshold. The
  threshold is deliberately an order of magnitude below that exploratory
  estimate so that it functions as a genuine hurdle rather than a rubber stamp.
- **State-count floor (research protocol 6).** A magnitude claim also requires
  the inference to be estimable: `n_high >= 5 AND n_low >= 5`. If either state
  has fewer than five independent formations, the result is labeled
  INCONCLUSIVE / EXPLORATORY_ONLY regardless of the magnitude, and the look
  counter does not advance. This is the protocol's own floor, folded into
  criterion 4(a) so it cannot be overlooked at decision time.
- **Not relaxed:** the threshold is never lowered to manufacture a pass, never
  re-derived from the fresh block's outcome, and never applied to the canonical
  block (which is read-only development evidence). If the fresh block's
  `|high_low_diff_net_1x|` is below 0.05, or either state has <5 formations,
  the correct record is INCONCLUSIVE, not SUPPORTED.

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
  (e.g. `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/`),
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

**Update 2026-11-02 (post-probe):** October 2026 monthly klines AND monthly
fundingRate ARE published (cutoff probe UNBLOCKED, record
research_state/cutoff_probe/cutoff_probe_20261102T221412Z.json, EXIT=0). The
fresh block now BUILDS with 26 eligible assets (>= MIN_ASSETS_DECILES=20) and
passes the data gate, BUT is still IMMATURE: n_formations=1 (2026-09-30),
n_high=0/n_low=0/n_mid=1, high_low_diff_net_1x=null,
last_allowed_formation_date 2026-09-30. The remaining blocker is the state rule
(`trailing_window_outer_deciles` requires >=30 prior in-block dispersions before
any high/low state assignment), which cannot be satisfied until the November
2026 vintage matures (n_high>0,n_low>0). No relaxation of the 30-day maturity
rule or MIN_ASSETS_DECILES=20. The used output directory is
`forward_block_h10_fresh/` (not `forward_block_h10/`). This note is a
documentation correction of the originally stale narrative; no methodology,
parameters, costs or acceptance criteria changed.

**Update 2026-11-02T22:15Z (panel-coverage correction):** the earlier note
claimed only BTCUSDT and ETHUSDT had October 2026 price panels and the other 30
panels ended 2026-09-30. That was stale even when written: a direct audit of the
committed panels shows all 30 non-delisted Binance kline panels end
2026-10-31 (MATICUSDT ends 2024-09-11 and EOSUSDT ends 2025-05-21, delisted by
construction), and marketcap_panel.csv spans 2023-01-01..2026-10-31. The
26-eligible-asset count was therefore correct for a different reason than the
narrative stated: eligibility is the intersection of a cap observation and a
price observation *on that date*, and the formation loop only visits dates that
are present in the merged price index. The merged index omits 2026-10-28 (a
genuine archive gap: the October 2026 daily kline for 2026-10-28 returns
HTTP 404 while 10-29/30/31 return HTTP 200), which shifts the index position
of 2026-10-31 so that `last_allowed_formation = cutoff_loc - 30` lands on
2026-09-30 rather than 2026-10-01, excluding the one formation whose 30-day
outcome would otherwise have been complete. The block is therefore sealed
correctly, but it contains exactly one formation and the state rule cannot fire.
This is a data-vintage maturity problem, not a pipeline defect; no code path was
changed and the artifact was re-run byte-identically (only `evaluated_utc` and
the later-added `overlap_aware_uncertainty` section differ). The blocker is
preserved: re-attempt only when the November 2026 vintage yields n_high>0 and
n_low>0.

## 8. Open questions for the next agent

- When do >=20 assets obtain complete October 2026 price panels (their October
  monthly zips publish), and does the fresh block then pass the data gate?
- If the fresh block builds, is |high_low_diff_net_1x| above the economic
  threshold and Holm-significant across the cell family? (Do not promote from
  raw p-values or return alone.)
