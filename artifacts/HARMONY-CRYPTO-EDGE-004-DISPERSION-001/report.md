# Report: HARMONY-CRYPTO-EDGE-004-DISPERSION-001

- Commit SHA: b41d4d5
- Data gate status: PASS
- Tests run: 11 pass (5 grid + 6 pipeline)

## Phases completed
- C: done (n_high=6, n_low=8, diff_gross=0.17471689140306546)
- D: done (4 rank bands)
- E: done (costs + funding)
- F: done (60/20/20 chronological OOS)
- G: done (72/72 configs on discovery/validation only, final holdout excluded)

## Primary estimate (H004G033, Phase C)
- High dispersion gross mean: 0.11962691759955946
- Low dispersion gross mean: -0.055089973803506
- High-Low difference (gross): 0.17471689140306546
- 95% CI (block bootstrap): high [-0.04429957609831255, 0.28355341129743145], low [-0.08778487777678096, -0.0034922625650584196], diff [0.17471689140306546, 0.17471689140306546]

## Selected decision state per Section 10
Primary test governs the hypothesis verdict; grid results are sensitivity only, run on discovery/validation only with Holm adjustment across 72-config family, no promotion from grid. Final holdout excluded from grid.
