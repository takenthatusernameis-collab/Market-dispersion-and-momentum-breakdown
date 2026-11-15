# Preregistration — H004V106 Forward Block Internal Self-Consistency Audit (DISP-003-SELFCHECK-001)

**Program:** HARMONY-CRYPTO-EDGE-004
**Experiment ID:** H004V106_FORWARD_BLOCK_SELF_CONSISTENCY_AUDIT
**Status:** EXPLORATORY_ONLY
**Created:** 2026-11-15T15:20:00Z
**Author:** automated research agent (this session)

## 1. Why this audit exists (gap)

The sealed canonical forward block `forward_block/forward_block_evaluation.json` (sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`, n_formations=608) carries **two representations of the same quantity**:

- a per-formation `formations[].n_assets` array (608 records), and
- a derived `eligible_assets_per_date` summary object `{min, mean, max}`, plus header scalars `n_formations`, `state_counts {high, mid, low}`, `date_first`, `date_last`, `n_high`, `n_low`, `n_mid`.

No committed audit verifies that these *internal* fields agree with each other. The existing audits check **different questions**:

- `forward_block_final_integrity_audit.py` (H16/H27) **recomputes** the block from raw panels and reconciles recorded `input_file_hashes` against disk — an external recomputation, not an internal self-consistency check.
- `forward_block_independent_recomputation_audit.py` (H37) recomputes **metrics** (means/differences) from the `formations` array and compares them to the addendum — it does **not** check that the block's own `eligible_assets_per_date` summary equals the mean/min/max of `formations[].n_assets`, nor that `n_formations`/`state_counts`/`date_first`/`date_last` equal what the array implies.
- `expanding_universe_eligibility_audit.py` (H33) reconstructs the per-date eligibility map from raw panels and ties it to the **grid ledger** (108 cells) — not to the canonical forward block's own summary.

This is a specific, not-yet-covered question: **do the canonical block's own header/summary scalar fields equal what its own `formations` array implies?** It is a pure, deterministic, read-only check with no external data dependency.

## 2. Question and estimand

**Question:** Within the sealed canonical forward block, are the following internal identities exactly satisfied (bit-for-bit for integers/dates, within 1e-9 for the mean)?

1. `eligible_assets_per_date.min == min(formations[].n_assets)`
2. `eligible_assets_per_date.max == max(formations[].n_assets)`
3. `eligible_assets_per_date.mean == mean(formations[].n_assets)` within 1e-9
4. `n_formations == len(formations)`
5. `state_counts.high == count(state=="high")`, `state_counts.mid == count(state=="mid")`, `state_counts.low == count(state=="low")`
6. `n_high == state_counts.high`, `n_low == state_counts.low`, `n_mid == state_counts.mid` (header mirrors state_counts)
7. `date_first == min(formations[].formation_date)` and `date_last == max(formations[].formation_date)`
8. `formations[].formation_date` are strictly increasing and unique (no duplicate formation dates)
9. Every `state` value is one of {high, mid, low} and every `n_assets >= MIN_ASSETS_DECILES` (20)

**Estimand:** A deterministic consistency restatement of the block against itself. No outcomes beyond this check; no external data; no recomputation from panels; no sealed holdout opened.

## 3. Method (frozen before computation)

1. Load the canonical forward block and verify its recorded sha256 equals `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` (computed from the committed blob).
2. Confirm `block_sealed=true`, `anchor_id=H004V106`, `data_cutoff_utc=2026-09-30T00:00:00Z`, `date_last=2026-08-31`.
3. Compute each of the 9 internal identities above from the block's own fields only.
4. Record PASS/FAIL per check with exact expected vs actual; overall verdict PASS iff all checks pass.
5. Read-only, stdlib only, no network, no writes to any frozen artifact.

## 4. Decision rule (predeclared)

- Overall PASS: every internal identity holds (exact for counts/dates/states, 1e-9 for the mean).
- Overall FAIL: any identity is violated.
- EXPLORATORY_ONLY/consistency_only: neither validates nor replaces any confirmatory track; cannot produce a high_low_diff_net_1x claim for confirmation; does not change the frozen H10 preregistration or date gate; modifies no frozen artifact.

## 5. Safeguards (not relaxed)

- Read-only; no writes to any frozen artifact/config/input/frontier/registry/sealed holdout.
- No look-ahead, no fabrication, no forward-fill, no outcome-informed parameters, no synthetic market data.
- The canonical block is the source of truth; this audit only checks it against itself.
- Tolerances predeclared: exact for integers/dates/states; 1e-9 absolute for the mean.
- `MIN_ASSETS_DECILES=20` is the preregistered universe floor; the audit asserts every formation meets it but never imposes or changes it.

## 6. Expected output

- Audit artifact under `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/H004V106_forward_block_self_consistency_<timestamp>.json`
- Preregistration record here.
- Registry entry H38 (next_sequence_number 37->38).
- Hermetic seam tests covering all pure functions in the audit script.