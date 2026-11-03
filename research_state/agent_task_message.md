## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-11-03T03:23:08Z)

## Situation
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged.
- Full test suite green: 210 tests OK (skipped=1).
- Free data refreshed through 2026-10-31 (CoinMetrics + Binance panels).
- Manifest/provenance tests pass.
- Cutoff gate UNBLOCKED.
- H10 fresh block structurally blocked (durable). Adaptive research-gate trigger met.

## Your task
1. Re-verify canonical hash + tests.
2. Create a new uniquely identified exploratory version under adaptive research-gate policy (new ID, new artifact paths, preregistration) addressing the H10 structural blocker with the smallest feasible change (e.g. expand fresh-block window backward to accumulate ≥30 prior in-block dispersions, or a descriptive measurement feasibility study on development data). Keep frozen artifacts unchanged.
3. Do not relax 30-day maturity/state rule or MIN_ASSETS_DECILES=20. Do not modify canonical forward_block/.
4. Update frontier, registry, manifest, handoff.

## Hard constraints
- Free public data only; historical research only; no live/paper trading.
- Preserve DISPERSION-001/002. Never modify canonical forward_block/.
- Do not relax 30-day maturity/state rule or MIN_ASSETS_DECILES=20.
- Do not write "wait for a new experiment ID".

## Open questions
- Does expanding H10 fresh-block window backward yield ≥30 prior in-block dispersions and n_high>0/n_low>0 on dev data?
(End of file)