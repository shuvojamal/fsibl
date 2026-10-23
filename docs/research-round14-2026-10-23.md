# Research round 14: cross-sectional momentum rotation (2026-10-23)

**Question.** Instead of checking each coin on its own (the trend bot), what
if we rank the coins against each other every week and hold the strongest
ones? This is "relative-strength rotation", one of the best-documented
effects in finance books and papers.

Script: `research/scripts/research14.py` (reuses round 12's data and helpers).
Output: `research/results/research14.out`.

## Rules tested

- Every 7 or 14 days, rank the top 15 coins by 90-day dollar volume (the
  same universe as the bot) on their return over the last 14, 30, 60 or 90
  days.
- Hold the best 3 or 5 in equal weights. Only hold coins with a positive
  return; empty slots stay in cash.
- Variant: go fully to cash when BTC is below its 200-day EMA.
- Decide at the close, fill at the next open. Costs are 0.1% fee plus 0.05%
  slippage on every trade.
- That's 64 settings in all. Tuned on 2017-08 to 2021-12, tested on 2022 to
  2026-10.

## Results

| | Unseen 2022–26 | Max drawdown |
|---|---|---|
| Best setting on training (14d, hold 5, weekly, no filter) | **−3.2%/yr** (training said +189%/yr) | −77% |
| All 32 settings without the BTC filter | median about −6%/yr | −73% to −95% |
| All 32 settings with the BTC filter | +6% to +23%/yr, every one positive | −50% to −68% |
| **Trend bot (current rules), same period** | **+18.8%/yr, Sharpe 0.81** | **−28%** |

- The training ranking said almost nothing about unseen results (rank
  correlation +0.04).
- Daily returns are 0.71 correlated with the trend bot's, so splitting money
  50/50 between the two gives almost no diversification. On the unseen half,
  the 50/50 mix earned +23.2%/yr with a −44% drawdown and Sharpe 0.71, worse
  risk-adjusted than the trend bot alone.
- The whole-period numbers (+84%/yr, 2021 +1,247%) are mostly survivorship
  bias plus one euphoric year. LUNA and FTT, both top momentum coins in
  2021–22, can't be downloaded, so the crashes that would have hit this
  strategy are missing. Real results would be worse than shown.

## What it means

1. Pure rotation is the tuning trap again. It was brilliant in 2017–21,
   lost money afterwards, and got worse with higher costs (−8.7%/yr at
   double costs).
2. The BTC-below-200-EMA filter is what keeps rotation alive: all 32
   filtered settings stayed positive on unseen data. Even so, they drew down
   about twice as deep as the trend bot for similar or lower returns.
3. The trend bot's per-trade stop is what keeps its drawdown near 30%.
   Rotation has no stop and is always fully in alts, so it rides each crash
   down.

## Decision

Rejected. The trend bot stays the only strategy. One thing worth keeping:
for any always-invested crypto strategy, a BTC regime filter is close to
essential. It didn't help the trend bot (round 11) because the trend bot's
own checks and stops already keep it out of bear markets.
