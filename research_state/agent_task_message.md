# Agent Task Message — 2026-11-22T12:19:02Z (next session)

## Initial task for next agent

Hold the confirmatory H10 track for the hard date gate 2026-11-30. Today is 2026-11-22, before the gate. Do NOT re-probe November 2026 before 2026-11-30 and do NOT execute Option A until the gate is reached (on/after 2026-11-30).

Gate vs probe: the H10 cutoff gate is decided by the latest PUBLISHED-month record. The October 2026 archive is published (`target_published=true`, `cutoff_gate=UNBLOCKED` per the real record `research_state/cutoff_probe/cutoff_probe_20261113T091257Z.json`), so the H10 cutoff gate is UNBLOCKED. The November 2026 probe (`probe_month=2026-11`, target not yet published, 0 of 127 November records published) is recorded separately as BLOCKED and is NEVER promoted into the H10 gate decision. Do not re-probe November 2026 before 2026-11-30.

If, before 2026-11-30, you find another unblocked task, prefer a bounded no-cost action that produces a verifiable artifact/test/audit and leaves clean green state. Do NOT write a bare "hold" memo as the only output — the prior ~30 sessions degenerated into identical hold entries; add real value (state-consistency repair, source-coverage, tests, red-team) or explicitly record that no unblocked task remains.

At/after 2026-11-30, execute Option A: run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`; if `target_published=true`, refresh free public data only (Coin Metrics Community API + Binance Public Data Archive), run `python3 -m compileall -q scripts tests` and the full suite `python3 -m unittest discover -s tests` (install `requirements.txt` first: numpy + pandas), verify the four frozen hashes byte-unchanged (canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`; grid config `1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176`; frontier `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e`), then run a fresh sealed H10 block via `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new cutoff> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`), requiring `n_high > 0 AND n_low > 0` before any confirmatory claim; if the block is immature (`n_high=0` or `n_low=0`), record the blocker and do NOT relax 30-day maturity, the trailing-decile state rule, `MIN_ASSETS_DECILES=20`, or the per-look `alpha_k = 0.05/(k*(k+1))` rule.

Feasibility note (H12/H35): at a 2026-11-30 cutoff the fresh-block window holds only ~31 in-block formations (~1 classifiable), while the trailing-decile state rule needs >=30 prior in-block dispersions and the first mature look (M1, n_high>0 AND n_low>0) needs >=32 formations — earliest cutoff ≈ 2026-12-01. So even after the 2026-11-30 date gate the fresh block may still be immature. Record this; do not relax maturity.

## Verified state (2026-11-22T12:19:02Z, this session)

- **Compile check:** `python3 -m compileall -q scripts tests` OK.
- **Test suite:** full `python3 -m unittest discover -s tests` -> **1418 run, 1418 OK, 0 failures, 0 errors, 8 skipped, EXIT=0** (recorded 2026-11-22T12:25:33Z). The bare runner ships without numpy/pandas, so run `python3 -m pip install --disable-pip-version-check --no-input -r requirements.txt` before the suite (numpy 2.5.5 / pandas 3.1.1). `tests.test_state_consistency` 22/22 OK.
- **Probe evidence (disk):** 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`.
- **Recompute probe counts from disk:** 397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261113T091257Z.json`. Recompute from `research_state/cutoff_probe/` before trusting any quoted census; the published field is `target_published`; this line mirrors disk exactly at 2026-11-22T12:19:02Z.
- **Registry:** `research_state/hypothesis_registry.json` `next_sequence_number` 57 (H1–H57 registered; H57 = point-in-time eligibility audit, POINT_IN_TIME_ELIGIBLE).
- **Frozen hashes:** canonical forward block `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`; grid config `1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176`; frontier `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e` — all verified byte-unchanged vs disk at 2026-11-22T12:19:02Z.
- **Newest session verification record on disk:** `research_state/session_verifications/session_verify_20261122T121902Z.json`.
- **run_manifest:** `next_experiment_status` = `H10_EVALUATED_NULL_DIFF_IMMATURE_AWAITING_NOVEMBER_2026_MATURITY`; all `next_required_actions` DONE except `test_frozen_anchor_on_new_forward_block` (pending fresh sealed block after 2026-09-29). `data_refresh_required: true` but not actionable until November 2026 data publishes (nothing new to fetch); do not re-probe before 2026-11-30.
- **Durable-state repair this session:** the previous task message/handoff quoted a stale newest probe (`cutoff_probe_20261105T205749Z.json`); corrected to `cutoff_probe_20261113T091257Z.json`, which was the cause of the two failing `tests/test_task_message_probe_evidence.py` census tests. Both now pass.

## Hard constraints

Free public data only; historical research only; no fabrication.

## End-of-session requirement

Leave clean state. Waiting for fixed calendar date 2026-11-30 is a date gate.