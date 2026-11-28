## Agent Task Message — 2026-11-28T10:09:17Z (next session)

## Initial task for next agent

Hold the confirmatory H10 track for the hard date gate 2026-11-30. Today is 2026-11-28 (UTC 2026-11-28T10:09:17Z), before the gate. Do NOT re-probe the November 2026 probe (`probe_month=2026-11`) before 2026-11-30 and do NOT execute Option A until the gate is reached (on/after 2026-11-30).

State carried in: compileall OK; full suite `python3 -m unittest discover -s tests` -> **1661 run, 1661 OK, 0 failures, 0 errors, 8 skipped, EXIT=0**; durable-state guards 89/89 OK; all five frozen hashes byte-unchanged vs disk AND git blob; probe census matches disk (398 real `cutoff_probe_*.json`; 271 `probe_month=2026-10` / 50 published, 127 `probe_month=2026-11` / 0 published; newest `cutoff_probe_20261123T071225Z.json`). Registry `next_sequence_number` = 57 (no new hypothesis allocated).

Probe evidence (disk): 398 real `cutoff_probe_*.json` (271 `probe_month=2026-10` / 50 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261123T071225Z.json` (probe_month 2026-10, published).

Recompute probe counts from disk: 398 real `cutoff_probe_*.json` (271 `probe_month=2026-10` / 50 published, 127 `probe_month=2026-11` / 0 published), newest `cutoff_probe_20261123T071225Z.json`. Re-derive this every session via `tests/test_task_message_probe_evidence.py`.

If, before 2026-11-30, you find another unblocked task, prefer a bounded no-cost action that produces a verifiable artifact/test/audit and leaves clean green state. Do NOT write a bare "hold" memo as the only output. Do NOT re-consolidate the handoff unless it has re-accumulated duplicate hold entries: check with `python3 -m unittest tests.test_handoff_session_entries` and only consolidate if a real degeneration has reappeared. Hold entries: the handoff currently carries 0 `BLOCKED_BY_HARD_DATE_GATE` marker-bearing entries. This session added NO new hold entry; the next session must run `python3 -m unittest tests.test_handoff_session_entries` and consolidate only if it reports degeneration.

At/after 2026-11-30, execute Option A: run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`; if `target_published=true`, refresh free public data only (Coin Metrics Community API + Binance Public Data Archive), run `python3 -m compileall -q scripts tests` and the full suite `python3 -m unittest discover -s tests`, verify the five frozen hashes byte-unchanged, then run a fresh sealed H10 block via `python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new cutoff> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` (never `forward_block/`), requiring `n_high > 0 AND n_low > 0` before any confirmatory claim; if immature, record the blocker and do NOT relax 30-day maturity, the trailing-decile state rule, `MIN_ASSETS_DECILES=20`, or the per-look `alpha_k = 0.05/(k*(k+1))` rule.

## Hard constraints

Free public data only; historical research only; no fabrication. Preserve DISPERSION-001/002 configs, inputs, artifacts and findings. Keep future evaluation blocks sealed. Never relax 30-day maturity, `MIN_ASSETS_DECILES=20`, the trailing-decile state rule or `alpha_k = 0.05/(k*(k+1))`.

## End-of-session requirement

Leave clean state. Waiting for fixed calendar date 2026-11-30 is a date gate.
"