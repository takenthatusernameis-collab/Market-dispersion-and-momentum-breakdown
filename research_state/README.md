# Research state

These are compact durable controls for recurring research sessions, not a replacement for immutable experiment artifacts.

- agent_task_message.md: immediate task to execute.
- agent_handoff.md: verified summary and next task.
- universe_frontier.json: historical rank frontier, candidate queue and blockers.
- hypothesis_registry.json: active, rejected, inconclusive and candidate hypotheses.
- run_manifest.json: active program status and latest verified evidence.
- workflow_run_diagnostics.jsonl: scheduled-worker diagnostics.

Every update must be evidence-backed and resumable. Never remove failed candidates or blockers to make the frontier look complete. Validate JSON and reconcile state with committed artifacts. The program remains ACTIVE when one experiment is rejected or a source is blocked.
