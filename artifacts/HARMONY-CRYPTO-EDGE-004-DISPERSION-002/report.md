# Experiment Report — HARMONY-CRYPTO-EDGE-004-DISPERSION-002

## Summary
Follow-up dispersion/momentum experiment on 108-config grid (H004F001..H004F108), anchor H004F033. Free-data-only, point-in-time universe, no-lookahead, chronological OOS (60/20/20). 53 formations total.

## Phase C — Dispersion-conditioned (anchor)
- High-dispersion gross mean +0.1196 (n=6) vs low -0.0551 (n=8); diff +0.1747 (block-boot CI [0.1747,0.1747]). Mid +0.0056 (n=39).

## Phase D — Expanding rank frontier
- Diff positive at 1-20 (+0.104) and 1-28 (+0.175); negative at 1-10 (-0.102) and 1-15 (-0.055).

## Phase E — Net-of-cost
- ~0.001 degradation per leverage unit (1x/2x/3x). High stays positive net at 3x (+0.1166); low more negative (-0.0581). Turnover 2.0/rebalance; funding PnL included.

## Phase F — OOS
- Discovery (n=31): diff +0.2877 (high +0.2078, low -0.0798).
- Validation (n=11): diff +0.0079.
- Final (n=11): diff -0.0050 (1 high / 1 low).

## Caveats
- Thin high/low tails (n_high<=6, n_low<=8) limit inference; final fold has 1 high/1 low. Do not draw strong conclusions where n<5 in any state.
- Block-boot CIs degenerate to point estimates (single realization per state).

## Controls
free-data-only, point-in-time universe, no-lookahead, chronological OOS. Grid manifest/config/data pipeline unchanged.