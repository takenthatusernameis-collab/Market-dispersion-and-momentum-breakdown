# Market Dispersion and Momentum Breakdown

**Research status:** exploratory and unresolved; no validated trading edge. The latest completed follow-up found that the discovery-period effect did not replicate later.

This repository continuously researches cross-sectional cryptocurrency momentum conditioned on market-wide return dispersion. Negative, null, failed and blocked results are first-class outputs.

## Current priorities
1. Preserve DISPERSION-001 and DISPERSION-002 as immutable historical evidence.
2. Expand candidate assets in descending historical point-in-time market-cap rank, with no fixed top-N limit.
3. Refresh free market-cap, price, funding, contract-identity and lifecycle data through the latest fully closed UTC daily candle.
4. Execute DISPERSION-003's 216-cell grid: 108 parameter combinations crossed with the legacy 28-asset comparator and the expanding point-in-time universe.
5. Test candidate hypotheses without choosing replacements from an already inspected holdout.

## Safety and evidence rules
- Free public data and no-cost tooling only; no paid APIs, trials, subscriptions, compute, credentials, orders or live/paper trading.
- Historical research only.
- Current market-cap rankings are candidate discovery only, never historical truth.
- No look-ahead, survivorship backfill, forward-filled prices/returns/funding, silent exclusions or outcome-informed changes to frozen experiments.
- The research queue must not wait for a new manual experiment ID. Generate the next stable ID, preregister it, execute what is valid, record blockers and move to the next useful task.
- A failed data gate blocks only the affected cell; it does not stop unrelated source discovery, tests, audits or hypothesis planning.
- Never promote a hypothesis merely because prior results were unfavorable.

## Repository map
- AGENTS.md — always-on worker rules; SKILLS.md — research workflow skills.
- HANDOFF.md and research_state/ — durable task, frontier, hypothesis registry and run state.
- prompts/continuous_research_operating_contract_v1.md — recursive research contract.
- configs/ — frozen grids; docs/ — architecture, protocol, sources and decisions.
- scripts/ and tests/ — evaluation, data validation, recovery and regression tests.
- schemas/ — machine-readable artifact contracts; artifacts/ — immutable experiments.

## Verify locally
Python 3.11+ is recommended. Use free open-source dependencies only.

    python3 -m compileall -q scripts tests
    python3 -m unittest discover -s tests -v
    python3 scripts/generate_grid_v3_manifest.py --output /tmp/dispersion-003-grid.json

A green workflow or passing tests prove implementation checks, not profitability.
