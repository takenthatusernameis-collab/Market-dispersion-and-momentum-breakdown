# BREADTH-ARITY-001 (H55) — Breadth/arity and 2-asset identification limits of the dispersion-conditioning mechanism

- **Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-BREADTH-ARITY-001
- **Hypothesis ID:** H55
- **Status:** EXPLORATORY_ONLY
- **Label:** feasibility_identification_diagnostic
- **Created:** 2026-11-20T02:33:35Z (preregistered before any figure in this file was computed)
- **Program:** HARMONY-CRYPTO-EDGE-004

## Motivation and distinctness

The adaptive research-gate policy v1 trigger is met: H40 (coverage feasibility), H43 (archive probe),
H46 (reconciliation), H47 (narrow roster), H48 (acquisition queue), H49 (wave-A), H50 (wave-B trim),
H51/H52 (wave-B acquisition), H53 (normalization) and H54 (wave-B QA) are materially distinct,
documented attempts across two source routes that have not advanced the breadth gate for a fresh
dispersion-conditioned mechanism test. The remaining Option-B avenue named by the durable task message
is a bounded mechanism diagnostic on the QA-clean ARK/ASTR (wave-B) panels.

Before spending any session on that diagnostic, two structural questions decide whether it can test the
registered mechanism at all. Neither was ever computed:

1. **Arity.** The registered anchor portfolio rule is `trailing_window_outer_deciles` with tail size
   `k = n // 10` and the canonical implementation refuses to trade when `k < 2`. The minimum
   cross-sectional breadth implied by that rule has never been stated explicitly, and no inventory of
   breadth actually available per month in this checkout exists.
2. **Identification.** With a 2-asset cross-section the population standard deviation of the two
   trailing momentum values is algebraically `|m1 - m2| / 2`, i.e. the dispersion statistic is a
   deterministic, sign-invariant function of the momentum spread. If so, "conditioning on dispersion"
   in a 2-asset universe is not a conditioning experiment at all, and no amount of wave-B data quality
   changes that.

This experiment measures exactly those two properties and the attainable narrow-test sample size. It
computes **no forward outcome, no realized spread, no cost, no p-value and no inference**. It is a
measurement/identification feasibility diagnostic (policy v1 §3, last relaxation option), not an
outcome estimate.

## Inputs (pinned, read-only)

- 4 committed wave-B panels under
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-WAVEB-001/panels/` (ARK/ASTR klines and
  funding). Only close prices are read; funding is not used.
- The 28 committed DISP-002 legacy comparator klines panels under
  `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/data/panels/binance_klines_*.csv` — read **only**
  to count per-month breadth. Their bytes, results and conclusions are untouched and they are already
  inspected development data, never fresh confirmation.
- Canonical rule implementation: `scripts/eval_forward_block.py::portfolio_spread` and
  `MomentumCache` semantics (cumulative product of daily returns over the lookback window).
- Frozen hashes re-verified before any figure is trusted: canonical forward block, h10_fresh block,
  grid v3 config, universe frontier.

No network I/O. No archive bytes. No writes outside the audit JSON.

## Predeclared measurements (deterministic, stdlib only)

**M1 — arity of the registered rule.** For `n = 1..40`, apply the canonical outer-decile tail rule and
record whether both tails are non-empty. Report `min_breadth_outer_deciles` (smallest `n` with two
non-empty decile tails), the per-`n` tail size, and the implied requirement on the fresh forward block.

**M2 — 2-asset dispersion/spread identity.** On the ARK/ASTR overlap, monthly formations at the last
completed UTC day of each month, using the canonical 30-day lookback over daily returns:
compute `m_ark`, `m_astr`, the population standard deviation `d = std([m_ark, m_astr], ddof=0)` and
`|m_ark - m_astr|`. For every formation report `d`, `|Δ|`, `d / |Δ|` (when `|Δ| > 0`) and
`|d - |Δ|/2|`. Report `n_formations`, `max_abs_deviation`, and the count of formations at which the
identity holds to `1e-12`. Also report that `d` is invariant under swapping the two assets while the
signed spread is not, so a dispersion-only state cannot select a long versus short leg.

**M3 — committed-breadth inventory.** For each calendar month in `2023-01..2026-10`, count assets whose
committed klines panel covers the month (at least one daily observation in that month). Report per-month
counts, the split into legacy-28 versus wave-B contributors, `max_breadth`, the count of months with
`breadth >= 20`, and the count of months whose breadth comes only from wave-B.

**M4 — attainable narrow-test sample.** Monthly formations over the ARK/ASTR overlap with a complete
30-day lookback and a complete 30-day forward window that ends on or before the 2026-10-31 panel end.
Report `n_candidate_formations`, `n_lookback_complete`, `n_forward_matured`. No forward value is
computed; only completeness is counted.

## Predeclared verdict rules

- `BREADTH_ARITY_CONFIRMED` when **all** hold: `min_breadth_outer_deciles == 20`; M2
  `max_abs_deviation <= 1e-12` over at least 30 monthly formations; M3 wave-B-only breadth is `< 20`
  in every month; M4 `n_forward_matured < 30`.
- `BREADTH_ARITY_STRUCTURAL_LIMIT` when `min_breadth_outer_deciles == 20` and M2 identity holds but
  M3/M4 also show that the only months with `breadth >= 20` are legacy-28 months ending 2024-12-31.
  (This is the expected outcome and is still not an economic result.)
- `BREADTH_ARITY_UNEXPECTED` otherwise; every deviating figure is reported with its count.

## Explicit non-claims

- Not market evidence, not an economic result, not a candidate evaluation.
- No forward return, realized spread, dispersion-state outcome, cost, funding PnL, p-value, confidence
  interval or multiplicity correction is computed. Dispersion here is a *feature-side* statistic used
  only to demonstrate an algebraic identity.
- No candidate promoted; `confirmatory_claim_allowed = false`; the H10 fresh sealed block stays
  date-gated to 2026-11-30 and is not read for outcomes.
- Does not alter any frozen DISP-001/002/003 artifact, config, ledger, panel, forward block or
  frontier, and does not unlock H1/H6/H7/H10.
- The narrow 2-asset route is closed by construction, not by a failed data fetch; breadth acquisition
  (wave A and later) is the binding requirement for any fresh mechanism test.
- A green test suite proves only what the tests cover.

## Artifacts

- Script: `scripts/panel_breadth_arity_diagnostic.py`
- Audit: `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-BREADTH-ARITY-001/integrity_audit/panel_breadth_arity_diagnostic_<utc>.json`
- Test: `tests/test_panel_breadth_arity_diagnostic.py`
- Registry: H55 added append-only; `next_sequence_number` bumped to 55.
