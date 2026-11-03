# Durable research handoff

The program is active and must continue through an evidence-led loop. The current authoritative task is in research_state/agent_task_message.md; the verified research ledger is research_state/agent_handoff.md.

Current evidence:
- DISPERSION-001: primary experiment plus a 72-configuration grid. The grid completed; no configuration passed the recorded Holm-adjusted threshold.
- DISPERSION-002: the discovery effect was not replicated in later chronological splits. A 108-configuration manifest exists, but the committed evidence inspected did not contain a matching complete result ledger.
- Existing panels inspected end on 2024-12-31 and cover 28 mapped assets. Newer dates and candidate assets must be sourced and validated, not assumed.

Next priority: complete DISPERSION-003 H10 fresh sealed forward block evaluation once the November 2026 vintage publishes; the block is currently IMMATURE (n_formations=1, n_high=0, n_low=0) because the 2026-10-28 kline gap plus strict 30-day maturity pins last_allowed_formation to 2026-09-30 and the trailing-decile rule needs >=30 prior in-block dispersions. October 2026 IS published (cutoff gate UNBLOCKED) but does not unblock H10. Re-probe November 2026 (`scripts/probe_cutoff_gate.py --probe-month 2026-11`); when target_published=true, refresh free public data, re-run tests, verify H004V106 unchanged, re-run the fresh sealed block into `forward_block_h10_fresh/` (never `forward_block/`), and require n_high>0 AND n_low>0 plus economic significance + Holm across the family before any claim. Continue when tests are unfavorable or data is blocked. See the operating contract and docs/research_protocol.md.

Blocker (recorded 2026-11-03T05:22:41Z): November 2026 monthly archive not yet published (target_published=false, cutoff_gate=BLOCKED, record research_state/cutoff_probe/cutoff_probe_20261103T052850Z.json). Genuine data-maturity blocker; do not fabricate formations/outcomes or relax the 30-day maturity/state rule.

No paid services, live/paper trading, or changes to completed artifacts.
