## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 (2026-11-03T02:35:00Z)

## Situation
- Canonical H004V106 sha256 `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged.
- Free data refreshed through 2026-10-31 (CoinMetrics + Binance panels).
- Test suite currently 2 failures: `test_binance_manifest_provenance` (manifest lists only 4 BTC/ETH series vs 32 on-disk symbols) and `test_refresh_provenance_boundaries` (coinmetrics date_first '2023-01-01' vs panel min '2023-01-01T00:00:00...').
- H10 fresh block structurally blocked (durable). Cutoff gate UNBLOCKED.

## Your task
1. Fix manifest/provenance format so tests pass (210 OK). Do not weaken tests.
2. Re-verify canonical hash + tests.
3. Address H10 structural blocker via new exploratory ID (adaptive policy). Keep frozen artifacts unchanged.
4. Update frontier, registry, manifest, handoff.

## Hard constraints
- Free public data only; historical research only; no live/paper trading.
- Preserve DISPERSION-001/002. Never modify canonical forward_block/.
- Do not relax 30-day maturity/state rule or MIN_ASSETS_DECILES=20.
- Do not write "wait for a new experiment ID".

## Open questions
- Does expanding H10 fresh-block window backward yield ≥30 prior in-block dispersions and n_high>0/n_low>0 on dev data?
EOF