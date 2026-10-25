# Research round 37: can the bot make 30% a year for 5 years?

The owner asked whether a 30% CAGR over 5 years is possible in any way.
Round 36's model (4,000 five-year bootstrap paths, realistic drag scaled
with risk, auto savings at 3%), for risk 0.5% / 1% / 1.5% / 2% per trade,
8 slots, 6 of 8 checks. Output: `research/results/research37.out`.

| risk per trade | chance of ≥30%/yr, all history | median, all history | chance of ≥30%/yr, 2022-26 markets | median, 2022-26 | chance of a loss, 2022-26 | bad-case drop, 2022-26 |
|---|---|---|---|---|---|---|
| 0.5% (steady) | 17% | +19.8% | 6% | +12.9% | 6% | −35% |
| 1% (growth) | 57% | +33.0% | 24% | +17.1% | 12% | −59% |
| 1.5% | 61% | +36.7% | 16% | +10.5% | 25% | −72% |
| 2% | 65% | +41.2% | 18% | +11.0% | 29% | −75% |

**What it means**
- 30% a year is reachable with the growth set-up when the 5 years include a
  strong bull market (better-than-even odds on all history), but only 1 in 4
  in markets like 2022-26.
- Going above 1% risk does not pay in harder markets: at 1.5% and 2% the
  median return in 2022-26 conditions falls (to about +11%), the chance of a
  loss doubles (25-29%) and bad-case drops reach −72% to −75%. Big losses
  compound against you. 1% is the most a sensible set-up should risk.
- No setting changed. Recommendation: steady for the main money; growth
  (1%) at most for a smaller part; never above 1%.
