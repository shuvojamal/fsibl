# Research round 68: are buy signals from weekend closes worse? (scheduled daily run)

**Question.** Weekend crypto markets are thinner (lower volume, erratic
moves). Are buy signals from Saturday/Sunday closes less reliable?

**Method.** Live vs no new entries from weekend closes (exits unchanged);
steady and growth, 6 of 8 checks, top 15, round 12's simulator, round 21's
12 cells. Strict pass bar for a calendar effect (set first): higher Sharpe
in 10 of 12 cells plus the usual effect-size floor, on both set-ups.

**Result** (`research/results/research68.out`, 2022-26 medians):

| | steady return / Sharpe | growth return / Sharpe | Sharpe wins |
|---|---|---|---|
| live | +15.7% / 1.03 | +25.9% / 0.97 | ref |
| no weekend entries | +10.2% / 0.74 | +18.2% / 0.77 | 3 / 1 of 12 |

**Verdict: fails clearly.** Skipping weekend entries costs 5-8 points a year
(2018-21 too). Weekend signals are as good as any; skipping them only
misses trends. No change.
