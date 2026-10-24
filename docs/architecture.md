# Research architecture

## Components

### Candidate discovery and universe frontier
A durable point-in-time frontier records candidate assets, historical market-cap rank, source/provenance, contract identity, eligibility, exclusions and the next rank/cohort to process. Rank batches are operational checkpoints only, never a top-N research cutoff.

### Source and panel layer
Free public-source adapters retrieve historical cap, prices, funding settlements, instrument metadata and lifecycle events. Raw responses are stored lawfully or represented by retrieval metadata and hashes. Normalized panels use UTC timestamps and stable asset/contract identifiers.

### Data and causality gates
Validate timestamp availability, rank coverage, mapping, price/funding alignment, delisted instruments, missingness, source terms, duplicates and cutoff completeness. Block affected cells with reasons; continue other candidates and non-data research.

### Experiment registry
Each changed hypothesis, grid or data universe receives a stable experiment ID, timestamped preregistration, frozen config, canonical hashes, run manifest and deterministic artifact paths. Closed evidence is immutable. Corrections create a linked revision.

### Grid and evaluation engine
Enumerate the complete Cartesian product and each universe arm. Every expected cell reaches a terminal status. Checkpoints are idempotent. Discovery/validation data are for development; sealed future periods are evaluated only for a preselected configuration.

### Accounting and inference
Per-asset records preserve momentum, dispersion state, rank, membership and forward return. Portfolio records preserve long/short legs, price PnL, funding, costs, turnover and net returns. Reports include uncertainty, effective sample size, adverse findings and multiplicity control.

### Recursive research controller
At every session, select the highest-value unblocked task: expand candidates, repair data coverage, validate the pipeline, complete a grid, red-team a candidate or preregister a new hypothesis. Unfavorable results update the registry and next priority, never delete results or trigger indefinite waiting for a manual ID.

## Flow
Source discovery → candidate frontier → point-in-time verification → data gate → preregistration → development grid → costs/funding/inference → sealed forward test → report/decision → hypothesis update → next experiment.
