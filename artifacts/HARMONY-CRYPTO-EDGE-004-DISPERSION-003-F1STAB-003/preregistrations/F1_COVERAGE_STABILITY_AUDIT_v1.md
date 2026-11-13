# Preregistration — F1 Coverage Stability Audit (DISP-003-F1STAB-003)

**Program:** HARMONY-CRYPTO-EDGE-004
**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1STAB-003
**Hypothesis (registry):** H25
**Status:** EXPLORATORY_ONLY
**Created:** 2026-11-13T05:48:41Z
**Author:** automated research agent (this session)

## 1. Why this experiment exists (trigger)

Two committed, pre-registered diagnostics are the main reason the canonical
H004V106 positive estimate (+0.6165223953929935) is not treated as an edge:

- **H8 / DISP-003-STATEAUDIT-001** (leave-one-calendar-month-out): the estimate
  is `CLUSTER_DOMINATED`; dropping 2025-10 moves it from +0.617 to +0.093
  (delta fraction -0.849, far beyond the predeclared ±0.50 band).
- **H19 / DISP-003-TEMPSTABILITY-001** (median formation-date split at
  2025-11-01): the sign is not temporally stable (+0.6456 over 2025-01..2025-10
  vs -0.1629 over 2025-11..2026-08).

Both were computed on the **26-27-asset** committed universe (arm A). The F1
coverage repair (H23, `DISP-003-F1COVERAGE-001`) re-acquired the four missing
symbols (`1INCHUSDT`, `AAVEUSDT`, `ACHUSDT`, `AGLDUSDT`) and raised the eligible
count on the same formation dates to **29-31** (mean 26.23 -> 30.08). H24
(`DISP-003-F1SENS-002`) measured only whether the **point estimate** moves under
that repair (arm A +0.6165 -> arm B +0.5398, delta -0.0767); it did **not** test
whether the two **stability warnings** that drive the discounted verdict survive
the fuller universe.

That is the gap this experiment fills: **does the F1 coverage repair change the
H8 cluster-domination and H19 temporal-instability conclusions?** It is a bounded,
no-cost, on-disk task that advances the program without touching any frozen
artifact. The H10 fresh sealed forward block remains calendar-gated to the
November 2026 vintage (not before 2026-11-30) and re-probing November before that
date is prohibited, so it cannot be run this session.

## 2. Estimand (descriptive stability robustness — NOT a confirmation)

The estimand is whether the two pre-registered stability **verdicts** are robust
to the four-asset F1 coverage repair, evaluated over the identical sealed
canonical formation window (2025-01-01 .. 2026-08-31, data cutoff 2026-09-30),
using the identical frozen anchor parameters, cost model and trailing-decile
state rule:

- **Arm A (committed):** the 26-27 eligible-asset universe exactly as the frozen
  canonical block was computed.
- **Arm B (repaired):** the 29-31 eligible-asset universe with the four
  F1-repaired kline panels.

For each arm the script reports the baseline `high_low_diff_net_1x`, the
leave-one-calendar-month-out delta fractions, and the median-date temporal split
(first/second half difference, month-cluster bootstrap SE/CI, state counts).

This is **EXPLORATORY_ONLY** descriptive evidence on the already-inspected
development window. It does **not** validate, replace, unlock or re-run any frozen
experiment, does not open any sealed holdout, and cannot promote H1/H6/H7/H8/H9/
H10/H11 or any other hypothesis. It is not a fresh holdout and not independent
confirmation.

## 3. Method (frozen before any computation)

1. **Source (read-only).** Load the committed F1SENS-002 audit artifact
   (`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1SENS-002/integrity_audit/f1_coverage_outcome_sensitivity_20261113T025950Z.json`)
   and take its `arm_a_committed.formations` and `arm_b_repaired.formations`
   (608 records each; fields `formation_date`, `state`, `spread_net_1x`). No
   evaluator re-run and no panel read: the per-formation records are the same ones
   the frozen block and the F1 sensitivity contrast were computed from.
2. **Fidelity anchors (mandatory first step).** Before interpreting anything,
   confirm arm A reproduces the pre-existing committed results exactly:
   - arm A baseline `high_low_diff_net_1x` == 0.6165223953929935 (canonical block);
   - arm A leave-one-month-out on 2025-10 delta fraction == -0.8487210159492463
     (H8, `CLUSTER_DOMINATED`);
   - arm A median split at 2025-11-01 gives first-half +0.6456322213084524
     (n_high=53, n_low=21) and second-half -0.16288800752983412 (n_high=8,
     n_low=69) (H19, `not temporally stable`);
   - arm B baseline == 0.5397762360511249 (H24 / F1SENS-002 stored value).
   If any anchor fails, the script aborts with `FIDELITY_FAILED` and writes no
   verdict.
3. **Diagnostics on each arm** (identical functions for A and B):
   - `leave_one_calendar_month_out`: for each formation month, drop it, recompute
     `high_low_diff_net_1x`, record `delta_frac_vs_baseline = (diff - baseline)/baseline`;
     report the max `|delta_frac|` and the month that attains it.
   - `median_date_temporal_split`: sort formations by date, split at the median
     index (H19's split), compute first/second-half `high_low_diff_net_1x` and a
     formation-month cluster bootstrap (N_BOOT=2000, fixed seed) SE/CI per half.
4. Emit a single artifact
   `integrity_audit/f1_coverage_stability_audit_<UTC>.json` recording the fidelity
   anchors, both arms' diagnostics, the predeclared label, the comparison, and
   byte-verification that the F1SENS source artifact and both frozen blocks are
   unchanged.

## 4. Decision rule (predeclared, inherited verbatim — not outcome-tuned)

The thresholds are **not newly chosen**: they are the exact rules already
pre-registered for H8 and H19, applied unchanged to arm B.

- `cluster_domination_persists` = ( arm B max `|delta_frac|` over
  leave-one-month-out ) > 0.50   [H8's `THRESHOLD_FRAC`]
- `temporal_instability_persists` = sign(arm B first-half diff) !=
  sign(arm B second-half diff), both non-null and non-zero   [H19's sign-flip finding]

**Label:**
- `F1_STABILITY_PRESERVED` iff `cluster_domination_persists` AND
  `temporal_instability_persists`
- otherwise `F1_STABILITY_CHANGED`

The result is `EXPLORATORY_ONLY` in every branch. It cannot promote any hypothesis
and does not re-open the sealed canonical block. A `F1_STABILITY_PRESERVED` label
means the discounted verdict is **not** a coverage artifact (an adverse finding for
any positive-edge claim); it is not evidence for an edge.

## 5. Safeguards (never relaxed)

- Read-only: no writes to `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/`,
  the F1COVERAGE-001 panels/raw, the F1SENS-002 artifact, the canonical block or
  the H10 fresh block; new ID and new paths only.
- Free public data only; **no network** (reuses committed on-disk records); no
  credentials, no secrets, no trading.
- No look-ahead, no forward-fill, no synthetic rows, no silent exclusions, no
  fabricated fills; no truncated outcomes; the 30-day maturity rule is untouched.
- Point-in-time cap only: today's rank is never backfilled as historical rank.
- The F1SENS-002 source artifact and both frozen blocks are byte-verified unchanged
  at the end of the run.
- This is a stability-robustness measurement, not a hypothesis test; no p-value, no
  multiple-testing family, no promotion.

## 6. Expected output

- `scripts/f1_coverage_stability_audit.py` (new, read-only, imports nothing that
  mutates state).
- `integrity_audit/f1_coverage_stability_audit_<UTC>.json` with both arms' fidelity
  anchors, leave-one-month-out tables, temporal splits and the predeclared label.
- `tests/test_f1_coverage_stability_audit.py` regression guard.
- Registry entry H25 (next_sequence_number 24 -> 25); handoff and task-message
  update.

## 7. Change log

- 2026-11-13T05:48:41Z — created before any artifact-producing computation. A
  read-only pipeline-fidelity scratch check was run first to confirm the method
  reproduces H8 (2025-10 delta -0.849) and H19 (+0.6456 / -0.1629 at split
  2025-11-01) on arm A and the F1SENS stored arm B baseline (+0.5398); the
  decision rule in section 4 is inherited verbatim from H8/H19 and was not chosen
  after seeing arm B's outcome. No grid, hypothesis conclusion, cost model,
  parameter, panel or frozen artifact changed.