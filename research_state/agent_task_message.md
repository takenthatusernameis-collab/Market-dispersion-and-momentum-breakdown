## Task for next agent (from 20261108T204437Z)

**Prior task status:** COMPLETE_REVERIFIED (20261108T204437Z). Reverified at HEAD `255acd61` (2026-11-08T20:44:37Z): `python3 -m compileall -q scripts tests` EXIT=0. `python3 -m unittest discover -s tests` → **340 tests OK (skipped=1)** (benign record_test_claim tmp drift repairs during discovery only). `tests.test_state_consistency` 16/16 OK. Frozen hashes unchanged: canonical `7234fc4e...`, H10 fresh `324ab1e...` IMMATURE, orphan `forward_block_h10/` `d1333e74...`, orphan `forward_block_h10_fresh_check/` `f16db31e...`. November 2026 probe BLOCKED (latest `cutoff_probe_20261108T194646Z.json`, target_published=false, control 2026-09 OK); re-probe of 2026-11 forbidden before 2026-11-30. `git diff --stat -- artifacts/ configs/ scripts/ tests/ docs/ prompts/` empty. Verification: `research_state/session_verifications/session_verify_20261108T204437Z.json`.

**What was done this session:** Read durable handoff/task message; re-ran compileall, full suite, `tests.test_state_consistency`, and frozen-hash/probe/frozen-area-diff checks. Bounded delta search found no reproducible code/audit/test defect, no missing frozen-artifact mutation guard, and no reference-consistency drift (verified_test_claim snapshot `340/340/0`, fingerprint `6fd2dc3...` matches current tests/+scripts inventory). No source/artifact/config changed.

**Current state (frozen facts):**
- H10 fresh `forward_block_h10_fresh/forward_block_evaluation.json` is IMMATURE (n_formations=1, n_high=0, n_low=0; claim disallowed). Canonical `forward_block/` and orphan dirs `forward_block_h10/`, `forward_block_h10_fresh_check/` are sealed/frozen — never open, reuse, or promote as fresh confirmation.
- November 2026 probe BLOCKED (`target_published=false`, control 2026-09 OK); re-probe of 2026-11 forbidden before **2026-11-30**.
- Test suite green (340 OK, skipped=1). Compileall clean.
- **No unblocked task exists today (2026-11-08 < 2026-11-30).**

**Actionable next task (date-gated, execute in order):**
1. On/after 2026-11-30: run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. Record the result (do not loop).
2. If `target_published=true`: refresh free public data only (Coin Metrics Community API + Binance Public Data Archive). Re-run compileall/tests. Verify canonical hash `7234fc4e...` unchanged vs `git show HEAD:`. Run fresh sealed H10 block only into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--look-number 1` and preregistered constraints (30-day maturity, MIN_ASSETS_DECIMAL=20, trailing-decile, 0.05 economic threshold, sequential alpha_k = 0.05/(k*(k+1))). Require `n_high > 0 AND n_low > 0` before any confirmatory claim; if still immature, record and do not advance k.
3. If `target_published=false`: record probe result; do not loop; no H10 evaluation.
4. Before 2026-11-30: attempt only a genuine bounded no-cost gap (reproducible code/audit/test defect, missing guard against frozen-artifact mutation, or reference-consistency drift) that does not alter frozen result artifacts/configs. If none exists, record "no unblocked task exists" in handoff + task message and stop. Do not fabricate work, do not re-probe 2026-11, do not open `forward_block/` or the orphan variant dirs.

**Hard constraints:** no paid services/credentials/live or paper trading; point-in-time only (today's rank ≠ historical truth); preserve frozen artifacts/configs; unique IDs + prereg for any new exploratory work; do not report economic edge from immature/null/inspected data.
