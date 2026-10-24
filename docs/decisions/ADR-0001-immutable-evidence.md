# ADR-0001: Immutable experiment evidence

**Status:** accepted.

## Decision
Every completed experiment is a stable evidence record. Any changed hypothesis, universe, source, result-affecting code, grid or evaluation rule gets a new experiment ID or a linked corrective revision. Old artifacts are never overwritten to make results look better.

## Rationale
The program must distinguish true replication from changed assumptions and post-hoc selection. Unfavorable evidence is essential.

## Consequences
Reports cite exact configs, hashes, commit, manifest and tests. New candidates preserve old results as baselines. A correction includes a reason and independent reproducibility checks.
