# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Mandate
Continue quantitative research in this repository without waiting for a new manual experiment ID. Follow prompts/continuous_research_operating_contract_v1.md and docs/research_protocol.md. Historical-only, free-data-only, no live/paper orders.

## State on handoff
- Tests pass (40/40 via `python -m unittest discover -s tests`). DISPERSION-001/002 artifacts unchanged.
- DISPERSION-003 grid complete: 216 OK / 0 BLOCKED / 0 FAILED / 0 Holm-rejected.
- Forward block H004V106 sealed per committed artifact (data_cutoff_utc 2026-09-30T00:00:00Z, last_allowed_formation_date 2026-08-31, date range 2025-01-01..2026-08-31, n_formations 608, high_low_diff_net_1x 0.6165, status OK). Committed artifact is the source of truth.
- **BLOCKER (forward block):** Next sealed forward block for H004V106 requires formation dates >= 2026-09-30 with 30-day horizon; need completed UTC observations through at least 2026-10-29. Verified data cutoff: 2026-10-23T00:00:00Z (latest fully closed UTC daily Binance kline candle; CoinMetrics panels extend through 2026-10-23). 2026-10-23 < 2026-10-29 → BLOCKED (6 days short). **Do not compute outcomes prematurely.**
- Universe: 32 cap+Binance assets verified. Frontier cursor=76, 822 eligible candidates, rank_frontier_exhausted=false. `candidates_discovered` queue empty.

## First measurable deliverable
1. **Data cutoff monitoring** — Refresh free data (`scripts/refresh_free_data.py`) and check the cutoff. Do NOT evaluate the forward block unless cutoff >= 2026-10-29. If still < 2026-10-29, record the blocker (cutoff/date/horizon) in research_state/agent_handoff.md and proceed to the integrity task below. If >= 2026-10-29, evaluate only the preselected anchor H004V106 on the sealed block, no parameter/asset/threshold/cost search, and record the new cutoff.
2. **Frontier expansion** — `candidates_discovered` queue empty. Only populate it if new verified cap+Binance candidates appear; validate in bounded batches via `scripts/validate_candidate_batch.py`. If none, proceed to integrity checks.
3. **Integrity check** — Confirm DISPERSION-001/002 unchanged (git status/diff); run `python -m unittest discover -s tests` (must be 40/40); update handoff and next task with one concrete measurable action.

## Mandatory sequencing
1. Monitor/refresh data cutoff; evaluate sealed block H004V106 (preselected only) only when cutoff >= 2026-10-29.
2. Advance universe frontier if new verified assets exist; persist hashes/provenance.
3. Update hypothesis_registry.json if warranted (H6 is candidate; next_sequence_number=6).
4. Verify tests (40/40); confirm DISPERSION-001/002 unchanged; update handoff and next task.

## Definition of done
Provide verified test output, explicit forward-block blocker record (dates/cutoff/horizon), confirmation DISPERSION-001/002 unchanged, updated handoff + next task with one concrete next action. Do not declare program complete.

## Concrete next action
Run `scripts/refresh_free_data.py` again in next session and check the cutoff; if still < 2026-10-29, record the blocker and run `python -m unittest discover -s tests`; otherwise evaluate sealed block H004V106 only.

## Updated adaptive-policy task — integrity audit first (2026-10-24)

Do not wait idly for 2026-10-29. First independently audit the canonical H004V106 forward-block artifact and reconcile it with the archive and hypothesis registry. Recompute summary statistics from the formation records and source hashes; check finite/extreme dispersion, outcome units, state membership, mean-versus-median gap, outlier influence, costs, and overlap-aware uncertainty. Save new audit evidence only; do not rewrite either sealed or archived artifact.

After the discrepancy is reconciled, register any genuinely revised/positive-direction hypothesis under a new ID. The current block is already inspected and may only be treated as exploratory/development evidence. Do not compute the next sealed forward block until the cutoff supports complete 30-day horizons (currently required through 2026-10-29). Continue candidate-frontier work only when new candidates are evidenced; current ranks are not historical truth. Run the full test suite and keep DISPERSION-001/002 immutable.

