# Research round 62: do meme coins help or hurt? (scheduled daily run)

**Question.** DOGE, SHIB and PEPE often reach the top 15 by volume and so
enter the bot's list (the OKX demo holds PEPE). Do they add winners, or
mostly noise?

**Method.** Live universe vs the same without DOGE, SHIB and PEPE (the
three named in advance as the meme coins in the data). Steady and growth,
6 of 8 checks, round 12's simulator, round 21's 12 cells (the top 15 refilled
by the next coins). Pass bar (set first, with effect-size floor): higher
Sharpe in 9 of 12 cells and +0.5 points of 2022-26 return or a 1-point
shallower drop, on both set-ups. Part B (bar set before running it):
higher Sharpe in both halves of round 12's 55-coin pool.

**Result** (`research/results/research62.out`):

| 2022-26 medians | with meme coins | without |  Sharpe wins |
|---|---|---|---|
| steady | +15.7%, Sharpe 1.03 | **+17.6%, 1.07** | 10 of 12 |
| growth | +25.9%, 0.97 | **+27.4%, 1.00** | 10 of 12 |

2018-21: about the same (+0.4 to +1.5 points). In the live run meme coins
were 7-8% of trades and 7-9% of profit in 2022-26 (about their share, no
more). Part B, 55-coin pool (meme coins removed, list not refilled):
2022-26 steady +9.5% → +10.5%, growth +14.8% → +16.8%; 2018-21 unchanged.
**Confirmed.**

**Verdict: passes.** Leaving meme coins out added about 1-2 points a year
in 2022-26 with no cost elsewhere. Likely why: their violent reversals stop
the bot out often, and their slots go to coins that trend more steadily.

**Caveats.** Three coins, one of them (PEPE) only since 2023, so the
evidence is thin; it is one more variant tried (luck bar ~600). "Meme coin"
is a judgement, fixed before running here.

**Recommendation (no change made):** an optional "skip meme coins" switch
in the app (off by default), to be tried on one demo account, in the same
way as the trend-check switch (round 33). Needs the owner's go-ahead.
