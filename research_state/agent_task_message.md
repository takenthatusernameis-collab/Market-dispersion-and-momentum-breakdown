## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 H10 (2026-11-02T22:06:00Z)

## Situation
- Prior task DONE (bounded re-verification). Canonical H004V106 unchanged (sha256 7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390). Tests 200 OK (1 skipped). Cutoff UNBLOCKED.
- H10 fresh block at `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/`: n_formations=1 (2026-09-30), n_high=0/n_low=0/n_mid=1, high_low_diff_net_1x=null, data_cutoff 2026-10-31T00:00:00Z, 26 eligible assets (>=MIN_ASSETS_DECILES). IMMATURE due to `trailing_window_outer_deciles` requiring >=30 prior in-block dispersions; November 2026 not matured.

## Your task
Bounded independent task (tests/validation/design/red-team/source coverage). Re-verify canonical hash, tests, cutoff as needed; do not wait. Update handoff + rewrite this message. Re-attempt H10 fresh block evaluation only when n_high>0,n_low>0 (mature block). Follow prereg `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H10_FRESH_FORWARD_BLOCK_v1.md` exactly.

## Hard constraints
As in AGENTS.md and prior messages. No fabrication/relaxation/promotion. Preserve canonical artifacts. Never modify DISPERSION-001/002/grids/canonical forward_block (`forward_block/`). Write fresh results to separate output dir (use existing `forward_block_h10_fresh/` or new dir as appropriate; never overwrite canonical). Do not relax 30-day maturity/state rule or MIN_ASSETS_DECILES=20. Do not promote from raw p-values/return alone. Never reuse inspected H004V106 as confirmation. Do not write "wait for a new experiment ID".
