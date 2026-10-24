# ADR-0002: Point-in-time expanding market-cap universe

**Status:** accepted.

## Decision
The candidate queue expands in descending historical market-cap rank at each timestamp, with no fixed top-N cutoff. Operational batch sizes only control checkpointing and retries.

## Rationale
Current membership introduces look-ahead and survivorship bias and can exclude assets that later disappeared. Historical membership requires timestamped cap evidence and explicit contract identity.

## Consequences
Track rank, cap metric, as-of/availability time, asset/contract IDs, effective dates, source hash and exclusions. Missing historical evidence blocks the specific asset/date; never fall back to current rank. Continue scanning later candidates and unrelated tasks.
