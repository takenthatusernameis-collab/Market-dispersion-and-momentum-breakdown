# ADR-0003: Continuous evidence-led research loop

**Status:** accepted.

## Decision
After each task or experiment, the controller records evidence and selects the next scoped, unblocked task. It must not wait for a manually supplied experiment ID or stop merely because results are negative, inconclusive or a candidate's data is unavailable.

## Boundaries
Continuous research means the scheduled controller recovers and resumes according to hosted runtime limits, queues next work and preserves checkpoints. One process cannot evade job ceilings or guarantee uptime through service outages. When interrupted, continue on the next scheduled activation.

## Rationale
Progress includes source coverage, negative findings, implementation quality and falsification, not only profitable results.

## Safeguards
Every new hypothesis is preregistered; evidence is immutable; multiplicity is controlled; holdouts stay sealed; paid sources and live/paper trading are prohibited. The program is stopped only by explicit user instruction or a documented external restriction.
