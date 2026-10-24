# Initial Task Message — Continuous Dispersion Research

## Mandate
Continue quantitative research in this repository without waiting for a new manual experiment ID. Follow prompts/continuous_research_operating_contract_v1.md and docs/research_protocol.md. The work is historical-only, free-data-only and never places live or paper orders.

## State on handoff
- Tests pass (21/21). DISPERSION-003 grid manifest verified: 216 configs, 216 unique IDs (H004V001..H004V216), 216 unique hashes, anchors H004V105/H004V106 present.
- DISPERSION-001/002 artifacts unchanged and closed/immutable.
- Historical panels cover 28 mapped assets through 2024-12-31; rank frontier not proven exhausted.

## First measurable deliverable
Extend free public data (CoinMetrics Community API for market caps, Binance Public Data Archive for klines/funding) to the latest fully closed UTC daily candle for all known and discovered candidates. Build the expanding point-in-time universe for DISPERSION-003 (legacy28_comparator + expanding_point_in_time). Begin discovering candidates below the existing 28-asset set by descending historical point-in-time market-cap rank in batches of 25 (checkpoints only, no fixed top-N cutoff). Create artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels structure as needed and record cutoffs/provenance/hashes.

## Mandatory sequencing
1. Validate prior artifacts are intact. Never overwrite or edit DISPERSION-001 or DISPERSION-002 results.
2. Freeze DISPERSION-003 preregistration: exact primary anchor (H004V106 in expanding_point_in_time), source cutoffs, forward split (post-2024 block starting 2025-01-01), cost assumptions, expected result cells (216), grid hash and decision rules.
3. Find candidates by historical market-cap ranks, not current ranks. No fixed top-N cutoff. Keep a durable row for every discovered name, including excluded and blocked candidates.
4. Extend data to the latest fully closed UTC daily candle where sources allow. For every source and candidate record date range, counts, missingness, mapping, access terms, retrieval time and hash.
5. Run the registered primary anchor and complete the declared 216-cell development/validation grid; do not stop if early results are negative. Resume safely from checkpoints.
6. Use the fresh post-2024 forward period only for the pre-frozen anchor; never sweep parameters on it.
7. Report cost-adjusted net outcomes, historical funding attribution, uncertainty, effective sample size, rank-breadth stability and adverse results. If the sample is inadequate, label exploratory/inconclusive.
8. Update the hypothesis registry and choose the next theory-led test by evidence and expected information gain. Allocate a new ID automatically; never wait for manual ID approval.
9. Update the frontier, manifests, handoff and next task. The next task must itself be executable and unblocked where possible.

## Continue even when
- the result is negative, null, inconclusive or rejected;
- an individual asset has missing data;
- a public endpoint is down or rate-limited;
- an implementation or reproducibility defect is found;
- no parameter configuration passes multiplicity or economic criteria.

In these cases preserve evidence and continue with a justified different task. Never bypass a gate, invent data, select a winner by raw return, or mutate a frozen hypothesis. A blocked phase is not permission to stop unrelated research.

## Definition of done for this activation
Provide verified test output, manifest count/hash checks (216/216 unique), data-gate/frontier progress (discovered candidates beyond 28, cutoffs recorded), the exact artifacts changed, and one next concrete task. Do not declare the program complete.
