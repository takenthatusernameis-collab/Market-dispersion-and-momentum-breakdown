## Task for next agent (from 20261108T165049Z)

**Prior task status:** COMPLETE_REVERIFIED (20261108T165000Z). Reverified at HEAD `4261151a` (2026-11-08T16:50:49Z): `python3 -m compileall -q scripts tests` EXIT=0. `python3 -m unittest discover -s tests` → **338 tests OK (skipped=1)**. Frozen hashes verified: H004V106 canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390`; H10 fresh IMMATURE `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f`. Nov 2026 probe BLOCKED (`cutoff_probe_20261108T153647Z.json`, `target_published=false`). Reference audits pass (critical=0, errors=0). No source/artifact/config modified; working tree clean vs HEAD `4261151a`.

**Current state (frozen facts):**
- H10 fresh is IMMATURE (n_formations=1, n_high=0, n_low=0). Canonical `forward_block/` is sealed/frozen — never open/reuse as fresh confirmation.
- November 2026 probe BLOCKED; re-probe of 2026-11 forbidden before **2026-11-30**.
- Test suite green (338 OK, skipped=1).
- **No unblocked task exists today (2026-11-08 < 2026-11-30).**

**Actionable next task (date-gated, execute in order):**
1. On/after 2026-11-30: run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. Record the result in `research_state/cutoff_probe/` (do not loop).
2. If `target_published=true`: refresh free public data only (Coin Metrics Community API + Binance Public Data Archive). Re-run `python3 -m compileall -q scripts tests` and `python3 -m unittest discover -s tests`. Verify canonical hash `7234fc4e...` unchanged. Run fresh sealed H10 block only into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--look-number 1` and preregistered constraints (30-day maturity, MIN_ASSETS_DECIMAL=20, trailing-decile, 0.05 threshold). Require `n_high > 0 AND n_low > 0` before any confirmatory claim; if still immature, record and do not advance k.
3. If `target_published=false`: record probe result; do not loop; no H10 evaluation.
4. Before 2026-11-30: attempt only a genuine bounded no-cost gap (reproducible code/audit/test defect, missing guard against frozen-artifact mutation, or reference-consistency drift) that does not alter frozen result artifacts/configs. If none exists, record "no unblocked task exists" in handoff + task message and stop. Do not fabricate work, do not re-probe 2026-11, do not open `forward_block/`.

**Hard constraints:** no paid services/credentials/live or paper trading; point-in-time only (today's rank ≠ historical truth); preserve frozen artifacts/configs; unique IDs + prereg for any new exploratory work; do not report economic edge from immature/null/inspected data.
