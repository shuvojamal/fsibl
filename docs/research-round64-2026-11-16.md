# Research round 64: skip the most volatile coins by rule? (scheduled daily run)

**Question.** Round 62 found that leaving out DOGE, SHIB and PEPE added
1.5-2 points a year in 2022-26, and suggested their violent reversals as the
reason. If volatility is the mechanism, a rule (no hand-picked list) should
work too: each quarter, drop the 2 or 3 most volatile coins (90-day daily
return volatility) from the top 15 and fill from the next by volume.

**Method.** Live vs drop 2 / drop 3 most volatile vs round 62's named list;
steady and growth, 6 of 8 checks, round 12's simulator, round 21's 12 cells.
Pass bar (set first, with effect-size floor): higher Sharpe in 9 of 12 cells
and +0.5 points of 2022-26 return or a 1-point shallower drop, both set-ups.

**Result** (`research/results/research64.out`, 2022-26 medians):

| | steady return / Sharpe | growth return / Sharpe | 2018-21 (steady / growth) |
|---|---|---|---|
| live | +15.7% / 1.03 | +25.9% / 0.97 | +29.5% / +61.7% |
| drop 2 most volatile | +13.3% / 0.83 | +18.2% / 0.72 | +34.0% / +71.9% |
| drop 3 most volatile | +12.9% / 0.84 | +19.5% / 0.79 | +34.0% / +72.2% |
| no meme coins (r62) | +17.6% / 1.07 | +27.4% / 1.00 | +29.9% / +63.2% |

**Verdict: the volatility rule fails** (7-8 of 12 cells; 2022-26 3-8 points
worse, though better in 2018-21).

**What it means for round 62.** Its explanation does not hold: dropping
volatile coins in general hurts recent results, so the meme-coin gain is
specific to those three coins. With only three coins and a few years, that
is the shape of a lucky result. **Lower confidence in round 62.** The
optional "skip meme coins" switch stays a possibility to try on a demo
account, but it should not be expected to add 1.5-2 points a year, and it is
not worth applying to the real account on this evidence.
