# Research round 43: a cap on each position's size (scheduled daily run)

**Question.** Risk-based sizing buys more when the stop is close; could one
position grow large enough that a gap through its stop does real damage?
Would a cap at 50%, 33% or 20% of equity per position help, and at what cost?

**Method.** Steady (8 × 0.5%) and growth (8 × 1%), 6 of 8 checks, top 15,
round 12's simulator, round 21's six close times × two halves. Pass bar
(set first): higher Sharpe than no cap in at least 9 of 12 cells, or at
most 1 point less 2022-26 return with a shallower worst drop.

**Result** (`research/results/research43.out`): the caps barely ever bind.
Steady: identical results for 50%, 33% and 20%. Growth: identical for 50%
and 33%; 20% gave 2022-26 +27.2% vs +25.9% but a slightly deeper drop
(−29.0% vs −28.3%) and won only 2 of 12 cells. **No pass, no change.**

**Why.** The volatility check only allows coins whose daily range (ATR) is
at least 0.5% of price, and in practice the coins traded move 3-6% a day, so
the 2 × ATR stop is 6-12% away and a 0.5-1% risk buys a position of only
about 5-17% of the account. Oversized positions don't arise with these
settings, so the tail risk a cap would guard against is already small.
(This records the quick test from an earlier scheduled session that failed
before saving.)
