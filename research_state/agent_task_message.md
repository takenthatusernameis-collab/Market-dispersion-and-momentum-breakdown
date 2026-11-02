## NEXT AGENT TASK — HARMONY-CRYPTO-EDGE-004 DISPERSION-003 H10 (2026-11-02T16:01:35Z)

- **Situation:** Cutoff probe for 2026-10 UNBLOCKED (cutoff_probe_20261102T160135Z.json). Canonical H004V106 forward block unchanged (sha256 7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390). Fresh H10 eval still immature: 1 formation (2026-09-30), n_high=0/n_low=0/n_mid=1, high_low_diff_net_1x null. Tests baseline 165 passed + 2 expected failures (pytest not available this session; unchanged).
- **Blocker (preserved, exact):** H10 structurally cannot produce high_low_diff_net_1x on current vintage: trailing_window_outer_deciles needs >=30 prior in-block dispersions but only 1 formation exists after 2026-09-29. Need November 2026 vintage maturity.
- **Your task:**
  1. Do NOT modify canonical forward block or DISPERSION-001/002 grids. Do not reuse inspected H004V106 as confirmation.
  2. Wait for November 2026 vintage. When fresh block has n_high>0,n_low>0, re-run: python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 --data-cutoff <new cutoff> --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/ (separate dir). Evaluate per preregistration requiring both |high_low_diff_net_1x| above economic threshold after costs AND Holm-significance. Never relax 30-day maturity/state rule.
  3. If not matured, preserve blocker with exact unmet requirements and do another independent bounded task (tests/validation/design/red-team).
  4. At session end: verify canonical block hash, run tests (note expected failures), audit panels/cutoff, update frontier/registry/manifest/handoff.
- **Hard constraints:** Free public data only; historical research only. No look-ahead/fabrication/forward-fill/silent exclusions/outcome-informed params/costs/hidden multiplicity/reuse of inspected holdout. Never shorten 30-day maturity; never relax costs. October 2026 ranks not backfilled as historical ranks.
- **Concrete next action:** Wait for November 2026 vintage; re-run fresh sealed block in separate dir; evaluate per preregistration or document blocker with exact unmet requirements. Never write "wait for a new experiment ID."
" filePath">
research_state/agent_task_message.md