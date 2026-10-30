# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003
## Mandate
Continue quantitative research. Historical-only, free-data-only. No live/paper trading. No paid services or secrets.

## Current state (verified 2026-10-30T08:37:00Z)
- Tests: `python3 -m unittest discover -s tests` -> **98 run, 98 OK, 0 failures**. The pre-existing mtime-guard failure on frozen `formation_returns_conditioned.csv` was a test defect (see below), now fixed. Frozen artifacts byte-unchanged (`git diff --stat -- artifacts/ research_state/ configs/` empty; only `tests/__pycache__` and the edited test file in working tree).
- Cutoff gate: BLOCKED. Binance monthly series date_last = 2026-09-30; October 2026 archive still unpublished. Do NOT re-probe. Canonical forward block: data_cutoff_utc 2026-09-30T00:00:00Z, last_allowed_formation_date 2026-08-31, 608 formations.
- DISPERSION-003: grid 216/216 OK, 0 Holm-rejected. Canonical H004V106 forward block (608 formations) not significant (HAC t=1.548, CI [-0.164,1.397]). All integrity audits done (TAIL_ROBUST, cluster bootstrap includes zero, temporal stability not stable, CLUSTER_DOMINATED per H8, REGIME-001/002). Defective archive unchanged.
- Frontier: exhausted (cursor 6347, CoinMetrics community catalog fully walked), candidates_discovered=[], candidates_verified=220, candidates_blocked=6127. Catalog growth required for new discovery.
- Registry: H1 immutable NOT_SUPPORTED_AS_ROBUST_EDGE; H2-H7, H9 CANDIDATE_UNVALIDATED; H8 EXPLORATORY_ONLY. Program ACTIVE.

## Priority next actions
1. Verify: run tests (expect 98 run, 98 OK). Spot-check JSON; confirm `git diff --stat -- artifacts/ research_state/ configs/` empty.
2. Respect blocker: October 2026 Binance archive unpublished (date_last 2026-09-30). Keep BLOCKED; do NOT re-probe.
3. Do not re-run recorded audits (TAIL_ROBUST, cluster bootstrap, temporal stability, REGIME-001/002, state representativeness, forward-block integrity, phase B placebo).
4. Until October publishes: no independent work available on frozen data (grid/audits/placebo/registry/frontier complete). Catalog exhausted. Follow adaptive research-gate policy if triggers arise.
5. When October publishes: `scripts/refresh_free_data.py --price-end 2026-10-31 --cap-end 2026-10-31` if cutoff >= 2026-10-29 with October present. Preregister/evaluate fresh sealed forward block with HAC/overlap-aware uncertainty, only completed 30-day outcomes; require economic significance + Holm across family before promotion; account for H8 cluster-dominance.
6. Leave clean state; update handoff/registry/manifest/frontier as appropriate. Never wait for user-provided experiment ID.

## Constraints
Free public data only, historical-only, point-in-time ranks, no forward-fill, no trading, no secrets. Never change DISPERSION-001/002. All cells recorded with reason. No relaxation of 30-day maturity rule; do not open sealed holdout.

## Test defect fixed this session (2026-10-30)
`tests/test_disp002_phase_b_placebos.py::test_frozen_files_unchanged` had two defects that produced a false failure on byte-untouched frozen files:
- `int(f.stat().st_mtime) == 1793211518` — the fs rewrites mtime on checkout/restore (observed +35 h after the freeze on an untouched file). Now a bounded sanity check (mtime not in the future); content identity is the authoritative assertion.
- `sha256(file_bytes) == git blob SHA` — mismatched hash domains that can never agree. Now `file_bytes == git cat-file blob <sha>` (blob bytes from the index), immune to eol/text filters and mtime churn. Helper `_git_blob_bytes` added; `_git_blob_sha` and the unused `hashlib` import removed.