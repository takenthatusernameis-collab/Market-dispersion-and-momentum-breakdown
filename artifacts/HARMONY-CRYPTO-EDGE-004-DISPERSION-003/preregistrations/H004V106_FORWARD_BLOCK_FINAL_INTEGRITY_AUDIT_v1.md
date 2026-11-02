# Preregistration — H004V106 Forward Block Final Integrity Audit (DISP-003)

**Program:** HARMONY-CRYPTO-EDGE-004
**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003
**Anchor:** H004V106 (sealed forward block, cutoff 2026-09-30)
**Status:** EXPLORATORY_ONLY
**Created:** 2026-11-02T21:10:48Z
**Author:** automated research agent (this session)

## 1. Why this audit exists (trigger)

The canonical H004V106 sealed forward block (cutoff 2026-09-30T00:00:00Z,
last formation 2026-08-31, 608 formations, state counts high=61/low=90/mid=457,
high_low_diff_net_1x +0.6165223953929935) is development/exploratory evidence
only: it is a strict subset of the grid ledger's development window and was
already inspected, so it is NOT a fresh holdout and NOT independent confirmation.
It must never be relabeled as confirmatory.

Ten separate integrity audits already exist under
`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/` covering
integrity, independent recomputation (x2), tail influence, overlap-aware
uncertainty, cluster bootstrap, temporal stability, regime conditioning, state
representativeness, rolling window, placebo/red-team, and HAC addendum. There is
NO single consolidated artifact that combines: reconciliation (recorded input
hashes vs files on disk), finite-value checks, state counts, mean/median, tail
influence, cost treatment, overlap-aware uncertainty, and independent
recomputation in one document.

This preregistration locks the audit methodology BEFORE the consolidated audit
script runs, per the confirmatory-track rule: freeze methodology first; then
audit. The audit is additive and read-only: no sealed artifact, grid ledger,
manifest, DISPERSION-001 or DISPERSION-002 artifact is modified.

## 2. Question and estimand

**Question:** Is the canonical H004V106 sealed forward block internally
consistent, finite, and reproducible across every audit dimension collected in
one consolidated artifact?

**Estimand:** Canonical reported summary statistics vs an independent
recomputation from the sealed block's formation records, bounded by predeclared
thresholds: recomputed-vs-reported high_low_diff_net_1x within 1e-9, state
counts exact match, finite-dispersion count == n_formations, non-finite count 0,
tail-influence leave-one-out max |delta frac| < 0.10, trim k=3 delta frac < 0.20,
winsorize p=0.10 delta frac < 0.20, net = gross - 0.001 per formation, overlap-
aware CI computed on formation-month clusters with all states present.

## 3. Method (frozen before computation)

1. Read the canonical block at
   `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`.
   Record `audited_artifact_sha256` (expected
   7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390).
2. Reconcile inputs: recompute sha256 of every file under
   `data/panels/` except `candidate_batch_validation.json` and
   `data_refresh_provenance.json`, plus `grid_config_manifest.json` and
   `grid_result_ledger.json`, and compare each against the block's recorded
   `input_file_hashes`. Report match/mismatch per file and overall.
3. Independent recomputation from formation records: n_formations, state counts
   (high/low/mid), n_assets min/max, finite vs non-finite dispersion count,
   spread_net/spread_gross mean and median, high_net/high_gross mean,
   low_net/low_gross mean, high_low_diff_net/gross, date_first, date_last.
4. Finite-value checks: every formation's dispersion, spread_net_1x and
   spread_gross finite; report counts and first offending record if any.
5. Mean/median audit: recomputed spread_net/spread_gross mean and median vs
   reported values within 1e-9.
6. Tail influence: leave-one-out max absolute fractional change in
   high_low_diff_net_1x (< 0.10), trimmed mean k=3 (< 0.20), winsorize p=0.10 (<
   0.20).
7. Cost treatment: verify spread_net_1x == spread_gross - 0.001 for every
   formation; verify high_low_diff_net == high_low_diff_gross (cost cancels in
   difference of state means); report.
8. Overlap-aware CI: call
   `scripts/eval_forward_block.py::overlap_aware_interval` on the formation
   records (n_boot=2000, rng_seed=20261102) and report status/interval/SE;
   both states are present (n_high=61, n_low=90) so status OK is expected.
9. Independent recomputation check: every recomputed value matches the stored
   reported value within 1e-9; boolean flag per metric and overall.
10. Write consolidated artifact
    `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/
    H004V106_forward_block_final_integrity_audit_20261102.json` with audit_id,
    audit_utc, audited_artifact, audited_artifact_sha256, canonical_summary,
    canonical_recomputed, reconciliation, tail_influence, cost_treatment,
    overlap_aware, conclusion, status EXPLORATORY_ONLY.

## 4. Decision rule (predeclared)

- PASS: all recomputed-vs-reported values within 1e-9, finite count == n_formations,
  non-finite count 0, state counts exact match, tail-influence thresholds respected
  (leave-one-out max |delta frac| < 0.10, trim k=3 < 0.20, winsorize p=0.10 < 0.20),
  cost treatment consistent (net = gross - 0.001 per formation), overlap-aware status
  OK.
- FAIL: any threshold violated. On FAIL the audit artifact records the failing element
  and reason; no artifact is modified to force a pass.
- Input-hash reconciliation is reported per file for transparency but is NOT a PASS
  criterion: the canonical block was sealed before October 2026 data existed, so panel
  hashes on disk now include October rows (documented expected signal; the block's own
  sha256 and contents are unchanged). This is not tampering and does not affect the
  sealed block's outcomes, which use only data through 2026-08-31.

## 5. Safeguards (not relaxed)

- Read-only: the canonical forward block, the defective archived block,
  DISPERSION-001/DISPERSION-002 configs and artifacts, grids, ledger and manifest
  are never modified.
- No look-ahead, no forward-fill, no synthetic data, no invented fills, no
  silent sample exclusions, no paid sources, no live / paper trading.
- No promotion from this audit: it describes internal consistency only; it
  cannot validate, replace or unlock any frozen confirmatory track.
- This audit targets the canonical block only; H10 fresh-block maturity is a
  separate, still-blocked question.

## 6. Expected output

- Consolidated audit artifact (new ID, additive).
- `tests/test_forward_block_final_integrity_audit.py` asserting artifact fields
  and thresholds.
- `tests/test_state_consistency.py` INTEGRITY_AUDITS list extended 10 -> 11.
- run-manifest + handoff + task-message updates for the next agent.

## 7. Open questions for the next agent

- None; this session completes the audit chain for the canonical block. Next
  agent should address H10 fresh-block maturity (November 2026 vintage) or
  another independent unblocked action per AGENTS.md.
