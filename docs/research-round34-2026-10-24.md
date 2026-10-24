# Research round 34: the stop distance at entry (scheduled daily run)

**Question.** The initial stop (entry − 2 × ATR) was chosen in round 1 on
hourly candles and never re-tested on the daily set-up. Is 2 × ATR right?

**Method.** Initial stop 1.5 / 2 / 2.5 / 3 / 4 × ATR, trailing stop fixed at
3 × ATR, steady set-up (8 slots, 0.5% risk, 6 of 8 checks, top 15). Round
12's simulator and costs, round 21's six close times × two halves.

**Pass bar (set before running).** Higher Sharpe than 2 × ATR in at least
9 of 12 cells and a 2022-26 median worst drop no more than 3 points deeper.

**Result** (`research/results/research34.out`, medians):

| initial stop | 2022-26 return / Sharpe | worst drop | win rate | Sharpe wins |
|---|---|---|---|---|
| 1.5 × ATR | +19.7% / 1.03 | −20.4% | 32% | 9 of 12 (5/4) |
| **2 × ATR (live)** | +15.7% / 1.03 | −16.4% | 36% | ref |
| 2.5 × ATR | +12.5% / 0.99 | −13.8% | 38% | 4 of 12 |
| 3 × ATR | +10.4% / 0.98 | −12.0% | 39% | 3 of 12 |
| 4 × ATR | +7.9% / 0.97 | −9.3% | 39% | 2 of 12 |

**Verdict: no change.** 1.5 × ATR wins 9 of 12 cells but its 2022-26 drop
is 4 points deeper, so it fails the bar (and a bare 9/12 out of four
challengers is weak anyway). The Sharpe is nearly flat (0.97–1.03) across
all distances: because positions are sized from the stop, a tighter stop
simply means bigger positions, so this setting behaves like a second risk
dial rather than an edge. The risk setting already does that job more
transparently, so 2 × ATR stays.
