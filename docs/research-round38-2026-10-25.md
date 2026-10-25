# Research round 38: the bot's rules on Dhaka Stock Exchange shares

**Question.** The owner asked for a DSE option that only gives buy/sell
signals and a trailing stop (orders placed by hand). Do the rules work on DSE?

**Data.** "Dhaka Stock Exchange End-of-Day Financial Dataset with Coverage
Metadata", Mendeley Data v4 (2026), doi:10.17632/23553sm4tn.4, licensed
CC BY 4.0. Corporate-action adjusted daily prices, 393 equities plus DSEX,
2012-10 .. 2026-01, cached as `research/data/dse_daily_adj.pkl.gz` (equities
and DSEX only, float32; changed from the original CSVs). Spot-checked against
dse.com.bd's day-end archive (identical). For live use, dse.com.bd serves
day-end data at `/api/live/data-archive/day-end` (about two years back, not
adjusted for bonus shares).

**Method.** Round 12's simulator unchanged, DSE costs 0.40% + 0.30%
slippage per side, top 20 by traded value, halves 2013-10..2019 and
2020..2026-01. Benchmark: holding the DSEX price index. Pass bar set before
running: the primary set-up (8 × 1%, 6 checks, top 20) must make money
after costs in both halves, beat DSEX's Sharpe in both, and have shallower
drops in both.

**Result** (`research/results/research38.out`):

| | 2013-10..2019 | 2020..2026-01 |
|---|---|---|
| bot, primary | −16.3%/yr, worst drop −67% | −13.0%/yr, −71% |
| bot, 0.5% risk | −9.8%/yr, −44% | −2.3%/yr, −47% |
| every other variant (5 checks, top 10/30) | negative | negative |
| hold DSEX | +3.0%/yr, −31% | +3.5%/yr, −37% |

All six checks of the pass bar fail. **Verdict: rejected.**

**Why.** Diagnostics: with zero costs the edge is barely positive (+0.03R
and +0.08R per trade). DSE shares move little day to day, so a 2 × ATR stop
is only a few percent away and the roughly 1.4% round-trip cost takes a
large bite of every trade; the win rate is 23%. Wider stops (4 × / 6 ×
ATR) did not help even without costs. The crypto trend rules have no
usable edge on DSE.

**Recommendation.** Do not build DSE signals on these rules. A different,
slower approach (holding for months, few trades, so costs matter less)
would need its own research before anything is offered.
