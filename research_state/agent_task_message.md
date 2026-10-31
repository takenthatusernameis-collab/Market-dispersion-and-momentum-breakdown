# DELAY-ELIMINATION OVERRIDE — 2026-10-30

Before executing the task below, perform a cheap state-fingerprint check (HEAD + changed paths + existing archive cutoff metadata).

- If code/tests changed since the last verified test run, run affected tests first and the full suite at the milestone.
- If no code/test/data/state changed, skip the full test suite, skip repeated archive probes, do not append another session outcome, and do not update the manifest/frontier/handoffs just to refresh timestamps.
- Resume substantive work only on a new archive publication, a genuinely new free-data source, a state change, or a concrete untested integrity invariant.
- Keep a single event-triggered review; no minute-level polling and no duplicate wakeups.
- The 30-day maturity and sealed-forward-block rules remain mandatory. This override changes only the engineering cadence, not the research protocol.

---

# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Mandate
Continue quantitative research. Historical-only, free-data-only. No live/paper trading. No paid services or secrets.

## Current state (verified 2026-10-31T01:05:00Z)
- Tests: `python3 -m unittest discover -s tests` -> **131 run, 131 OK, 0 failures** (121 prior + 10 new). pandas/numpy are installed in this environment (were missing; script-executing tests previously errored). All `test_state_consistency` pass.
- Forward block H004V106 **outcome** byte-unchanged: n_formations 608, high_low_diff_net_1x=+0.6165223953929935, date_last 2026-08-31, block_sealed True. Only `input_file_hashes` changed this session: 32 `binance_funding_*.csv` (truncated panels rebuilt to the full 45-month window, 4107 data rows each) and `binance_panel_manifest.json` (boundary/rows corrected). Klines panel hashes, grid ledger, DISPERSION-001/002 and the defective archive are byte-unchanged.
- `git diff --stat -- artifacts/ research_state/ configs/` is **no longer empty**: funding panels + manifest + forward-block hash block changed as above, plus `research_state/run_manifest.json` (`funding_panel_row_count_repair_20261031` entry). This is the second metadata-only provenance repair in two sessions (first was the CoinMetrics manifest boundary inversion on 2026-10-30). No outcome, grid, hypothesis or decision rule changed.
- Binance monthly/daily archives: October 2026 unpublished (verified post-close; 404s recorded across monthly klines/funding and daily klines endpoints). Control 2026-09 -> 200.
- Cutoff gate: BLOCKED. Canonical forward block H004V106 data_cutoff_utc 2026-09-30T00:00:00Z, last_allowed_formation_date 2026-08-31, n_formations 608, block_sealed=True.
- DISPERSION-001/002 unchanged (immutable). Phase B placebo red-team present (EXPLORATORY_ONLY). Canonical sealed forward block H004V106: high_low_diff_net_1x=+0.6165, HAC t=1.5482, CI [-0.164,1.397] not significant, median -0.0106. Integrity audits done (TAIL_ROBUST, cluster bootstrap includes zero EXPLORATORY_ONLY, temporal stability not stable EXPLORATORY_ONLY, state representativeness CLUSTER_DOMINATED H8 EXPLORATORY_ONLY). Defective archive byte-unchanged; development/exploratory evidence only.
- Frontier/catalog exhausted (cursor 6347). Registry: H1 NOT_SUPPORTED_AS_ROBUST_EDGE (immutable). H2-H7, H9 CANDIDATE_UNVALIDATED. H8 EXPLORATORY_ONLY with addenda. Program ACTIVE.

## Priority next actions
1. Verify state quickly each session per override: `git rev-parse HEAD`, `git diff --stat -- artifacts/ research_state/ configs/`, spot-check JSON files. Confirm the forward-block *outcome* fields are unchanged (`n_formations` 608, `high_low_diff_net_1x` +0.6165223953929935, `date_last` 2026-08-31, `block_sealed` True) — only `input_file_hashes` may differ.
2. Respect blocker: October 2026 Binance archive unpublished. Keep cutoff BLOCKED; do NOT re-probe monthly/daily endpoints already recorded as 404.
3. Do not re-run recorded audits. H2-H7, H9 CANDIDATE_UNVALIDATED; H8 EXPLORATORY_ONLY. Do not modify frozen artifacts/state/configs.
4. Until the next month publishes, no further independent work on frozen data (grid complete, audits complete, catalog exhausted). Adaptive-gate trigger not met. Complete any bounded, no-cost local task only if a concrete untested integrity invariant is found — **and first check whether a committed manifest's boundary/rows/hash fields still agree with the artifact it describes**; that is the recurring failure class (CoinMetrics manifest 2026-10-30, Binance manifest 2026-10-31) and it is cheap to check.
5. When the next month publishes: `scripts/refresh_free_data.py --price-end <month-end> --cap-end <month-end>` only if cutoff >= month-end with that month present. Preregister/evaluate a fresh sealed forward block with HAC/overlap-aware uncertainty, only completed 30-day outcomes; require economic significance + Holm across family before promotion; account for H8 cluster-dominance.
6. Leave clean state; update handoff/registry/manifest/frontier as appropriate. Never wait for user-provided experiment ID. Program ACTIVE.

## Constraints
Free public data only, historical-only, point-in-time ranks, no forward-fill, no trading, no secrets. Never change DISPERSION-001/002. All cells recorded with reason. No relaxation of 30-day maturity rule; do not open sealed holdout.