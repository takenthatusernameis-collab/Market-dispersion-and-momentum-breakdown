Read the prior agent task from the durable handoff and complete it. Then update the handoff and write a clear initial task message for the next agent.

Task for next agent (final review/interpretation/reporting only):
- Read artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-001/report.md and summary.json for H004G033 primary results and phase status.
- Confirm grid_results.jsonl has 72/72 entries, grid_run_state.json shows holm_adjustment_applied true, final_holdout_excluded true, run_on discovery_validation_only.
- Produce a concise final human-readable summary (findings, caveats: CapMrktCurUSD partial on free tier, grid sensitivity only per spec, final holdout excluded). Do not recompute phases or alter artifacts.
