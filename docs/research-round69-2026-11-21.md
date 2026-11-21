# Research round 69: would a much smaller coin list do as well? (scheduled daily run)

**Question.** A first real account might be simpler trading only the
biggest coins. Round 29 tested 10-25 coins; this tests the top 2 (usually
BTC and ETH) and top 5 by volume against the live top 15.

**Method.** Steady and growth, 8 slots, 6 of 8 checks, round 12's simulator,
round 21's 12 cells. Pass bar (set first): Sharpe at least as high in 9 of
12 cells and at most 2 points less 2022-26 return.

**Result** (`research/results/research69.out`, 2022-26 medians):

| | steady return / Sharpe | growth return / Sharpe | trades 22-26 |
|---|---|---|---|
| top 15 (live) | +15.7% / 1.03 | +25.9% / 0.97 | ~250 |
| top 5 | +9.3% / 0.96 | +17.1% / 0.96 | 135 |
| top 2 | +2.1% / 0.49 | +4.0% / 0.50 | 64 |

2018-21 shows the same: top 5 about half the return, top 2 a quarter.

**Verdict: both fail clearly.** A trend strategy needs many coins to find
enough trends; with BTC and ETH alone it trades rarely and earns little.
The top 15 stays. (Drops are shallower with fewer coins only because less
money is invested.)
