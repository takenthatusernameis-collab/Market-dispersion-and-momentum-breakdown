## Task for next agent (from 20261109T004841Z)

**Prior task status:** COMPLETE_REVERIFIED (20261109T003355Z / HEAD `80146588`; re-verified 2026-11-09T00:48:41Z at HEAD `a9a7d590`). `python3 -m compileall -q scripts tests` EXIT=0. `python3 -m unittest discover -s tests` → **340 tests OK (skipped=1)** (40.985s). `tests.test_state_consistency` 16/16 OK. Frozen areas diff empty vs handoff HEAD `80146588`. All four frozen artifact hashes unchanged at HEAD `a9a7d590`: canonical `7234fc4e...`, `forward_block_h10_fresh` `324ab1e6...` (IMMATURE, n_formations=1, n_high=0, n_low=0, n_mid=1, confirmatory_claim_allowed=false), orphan `forward_block_h10` `d1333e74...`, orphan `forward_block_h10_fresh_check` `f16db31e...`. Latest probe `research_state/cutoff_probe/cutoff_probe_20261108T232421Z.json` → `target_published=false, control_month=2026-09, control_ok=true, archive_alive=true, gate_date_required=2026-10-29, gate_met_by_month_end=true, cutoff_gate=BLOCKED`. **Re-probe of 2026-11 forbidden before 2026-11-30**. Session verification: `research_state/session_verifications/session_verify_20261109T004841Z.json`.

**Current state (frozen facts):**
- `forward_block_h10_fresh/forward_block_evaluation.json` IMMATURE (n_formations=1, n_high=0, n_low=0, n_mid=1, `high_low_diff_net_1x=null`, `confirmatory_claim_allowed=false`). Canonical `forward_block/` and orphan dirs `forward_block_h10/`, `forward_block_h10_fresh_check/` sealed/frozen — never open, reuse, or promote as fresh confirmation.
- November 2026 probe BLOCKED (`target_published=false`); **re-probe of 2026-11 forbidden before 2026-11-30**. Today is 2026-11-09.
- Suite green (340 OK, skipped=1), compileall clean, state consistency OK.
- **No unblocked task exists today (2026-11-09 < 2026-11-30).**

**Actionable next task (date-gated, execute in order):**
1. **On/after 2026-11-30** run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. Record the result (do not loop).
2. If `target_published=true`: refresh free public data only (Coin Metrics Community API + Binance Public Data Archive). Re-run compileall/tests. Verify canonical hash `7234fc4e...` unchanged vs `git show HEAD:`. Run fresh sealed H10 block only into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--look-number 1` and preregistered constraints (30-day maturity, MIN_ASSETS_DECIMAL=20, trailing-decile, 0.05 economic threshold, sequential alpha_k = 0.05/(k*(k+1))). Require `n_high > 0 AND n_low > 0` before any confirmatory claim; if still immature, record and do not advance k.
3. If `target_published=false`: record probe result; do not loop; no H10 evaluation.
4. **Before 2026-11-30:** attempt only a genuine bounded no-cost gap (reproducible code/audit/test defect, missing guard against frozen-artifact mutation, or reference-consistency drift) that does not alter frozen result artifacts/configs. If none exists, record "no unblocked task exists" in handoff + task message and stop. Do not fabricate work, do not re-probe 2026-11, do not open `forward_block/` or orphan variant dirs.

**Hard constraints:** no paid services/credentials/live or paper trading; point-in-time only (today's rank ≠ historical truth); preserve frozen artifacts/configs; unique IDs + prereg for any new exploratory work; do not report economic edge from immature/null/inspected data. Never wait for a user-supplied experiment ID; work on HARMONY-CRYPTO-EDGE-004-DISPERSION-003; preserve DISPERSION-001/002 unchanged.

(End of file)
