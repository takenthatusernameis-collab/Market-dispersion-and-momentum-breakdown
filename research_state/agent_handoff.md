## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-11-03T01:14:31Z)

## Situation
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged.
- Full test suite green: 206 tests OK (skipped=1).
- Cutoff gate UNBLOCKED (latest probe `research_state/cutoff_probe/cutoff_probe_20261103T011431Z.json`).
- H10 fresh block (`artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/`) remains IMMATURE (n_formations=1, n_high=0/n_low=0/n_mid=1, date 2026-09-30, high_low_diff_net_1x null). State rule requires >=30 prior in-block dispersions before high/low assignment.

## Your task
Do bounded independent work (tests/validation/design/red-team/source coverage/candidate audits). Re-verify canonical hash and tests as needed. Do not wait for H10 to mature; only re-run H10 fresh block evaluation when n_high>0 and n_low>0, following prereg exactly (H10_FRESH_FORWARD_BLOCK_v1.md). Write fresh results to a separate dir (never under canonical `forward_block/`).

## Hard constraints
- Free public data only. No paid services/trials/compute, secrets, credentials.
- Historical research only. Never place orders/deploy live/paper trading.
- Preserve DISPERSION-001/002 configs/inputs/artifacts/findings. Changes need new IDs/paths.
- Use completed UTC observations, causal timing, realistic costs/funding, chronological eval.
- Record every cell state with reason; correct for complete declared multiple-testing family. Do not promote from raw p-values/return alone.
- Never reuse inspected holdout as independent evidence; never open originally sealed holdout.
- Never fabricate metrics, silently drop candidates, change grids after seeing outcomes.
- Never modify canonical `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/`. Write fresh results to separate dir.
- Do not relax 30-day maturity/state rule or `MIN_ASSETS_DECILES=20`.
- Do not promote from raw p-values/return alone. Never reuse inspected H004V106 as confirmation.
- Do not write "wait for a new experiment ID".

## Open questions for the next agent
- When n_high>0 and n_low>0 appear in the fresh block (November 2026 vintage maturity), re-run per H10 prereg to a new separate dir and evaluate |high_low_diff_net_1x| against the predeclared economic-significance threshold after costs, with Holm correction across the cell family. Do not relax maturity/state rules.

(End of file)
