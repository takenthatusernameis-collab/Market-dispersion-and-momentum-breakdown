## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-11-02T23:16:47Z)

## Situation
- Prior session verified canonical H004V106 unchanged (sha256 7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390, n_formations 608, high_low_diff_net_1x +0.6165223953929935, date_last 2026-08-31, block_sealed True, data_cutoff_utc 2026-09-30T00:00:00Z) vs committed blob (`git show HEAD:` match).
- Full test suite green: 206 tests OK (skipped=1). `tests/test_forward_block_final_integrity_audit.py` and `tests/test_state_consistency.py` (INTEGRITY_AUDITS=11) pass.
- Cutoff gate UNBLOCKED per real probe 2026-11-02T22:14:12Z (`research_state/cutoff_probe/cutoff_probe_20261102T221412Z.json`, target_published true). October 2026 monthly klines AND fundingRate HTTP 200; all 30 non-delisted kline panels end 2026-10-31; daily 2026-10-28 genuine HTTP 404 gap; 10-29/30/31 HTTP 200.
- H10 fresh block at `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/`: n_formations=1 (2026-09-30), n_high=0/n_low=0/n_mid=1, high_low_diff_net_1x=null, 26 eligible assets, data_cutoff 2026-10-31T00:00:00Z. **IMMATURE** (trailing_window_outer_deciles needs >=30 prior in-block dispersions before any high/low state assignment). Root cause: merged price index omits 2026-10-28 (genuine archive gap) → last_allowed_formation = cutoff_loc - 30 lands 2026-09-30. No re-run performed.
- Consolidated H004V106 final integrity audit complete: `integrity_audit/H004V106_forward_block_final_integrity_audit_20261102.json` (PASS, EXPLORATORY_ONLY). All DISP-003 exploratory audits complete EXPLORATORY_ONLY; none unlock the confirmatory track.

## Your task
Do bounded independent work (tests/validation/design/red-team/source coverage/candidate audits). Re-verify canonical hash and tests as needed. **Do not wait for H10 to mature** — only re-run H10 fresh block evaluation when `n_high>0 and n_low>0` (mature block), following prereg `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H10_FRESH_FORWARD_BLOCK_v1.md` exactly.

## Hard constraints
- Free public data only. No paid services/trials/compute, secrets, credentials.
- Historical research only. Never place orders/deploy live/paper trading.
- Preserve DISPERSION-001/002 configs/inputs/artifacts/findings. Changes need new IDs/paths.
- Use completed UTC observations, causal timing, realistic costs/funding, chronological eval.
- Record every cell state with reason; correct for complete declared multiple-testing family. Do not promote from raw p-values/return alone.
- Never reuse inspected holdout as independent evidence; never open originally sealed holdout.
- Never fabricate metrics, silently drop candidates, change grids after seeing outcomes.
- Never modify canonical `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/`. Write fresh results to separate dir (existing `forward_block_h10_fresh/` or new).
- Do not relax 30-day maturity/state rule or `MIN_ASSETS_DECILES=20`.
- Do not promote from raw p-values/return alone. Never reuse inspected H004V106 as confirmation.
- Do not write "wait for a new experiment ID".

## Recent context (do not undo)
- `tests/test_latest_probe_record_pinned.py` pins `latest_archive_probe` summaries to named records; keep consistent.
- `universe_frontier.json` reflects real UNBLOCKED probe 2026-11-02T22:14:12Z and panel end 2026-10-31; old BLOCKED summary preserved in `universe_frontier.corrections`.
- Full suite green 206 tests OK (skipped=1).
- Hypothesis registry: H1 immutable NOT_SUPPORTED_AS_ROBUST_EDGE; H2-H9 CANDIDATE_UNVALIDATED/EXPLORATORY_ONLY; H10 CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / EVALUATED_NULL_DIFF_IMMATURE awaiting November 2026 vintage maturity (next_sequence_number 10).
- Next experiment ID available: HARMONY-CRYPTO-EDGE-004-DISPERSION-003-H10 (allocated). Preregistration exists at `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H10_FRESH_FORWARD_BLOCK_v1.md`.

## Open questions for the next agent
- None blocking; H10 fresh-block maturity (November 2026 vintage) remains the gated item. When n_high>0 and n_low>0, re-run per H10 prereg and evaluate |high_low_diff_net_1x| against the predeclared economic-significance threshold after costs, with Holm-significance across the cell family — do not promote from raw p-values or return alone.
