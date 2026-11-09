# Research round 57: how much do fees and slippage matter? (scheduled daily run)

**Question.** Binance charges 0.10% per spot trade, 0.075% when fees are
paid in BNB. Slippage could be higher than the backtests' 0.05% in fast
markets. How sensitive are the results, and is the BNB discount worth it?

**Method.** Fee 0.075 / 0.10 / 0.15% × slippage 0.02 / 0.05 / 0.15% per side,
steady and growth, 6 of 8 checks, top 15, round 12's simulator, round 21's
12 cells. Pass bar (set first): BNB fees "worth recommending" if they add at
least 0.3 points a year in 2022-26 (at 0.05% slippage).

**Result** (`research/results/research57.out`, 2022-26 medians):
- Steady: +15.7% at the standard 0.10% fee; +15.9% with BNB fees (+0.2
  points); worst case in the grid (0.15% + 0.15%) +14.5%.
- Growth: +25.9% standard; +26.3% with BNB fees (+0.4 points); worst case
  +23.6%.
- Each extra 0.05% of cost per side: about −0.4 points a year (steady),
  −0.8 (growth).

**Verdict.** Steady: BNB fees not worth the bother (+0.2). Growth: just over
the bar (+0.4). Overall the strategy trades rarely (about 50 trades a year),
so costs are a small factor; even tripled slippage costs only about 1 point.

**If BNB fees are used on the real account:** keep a few USDT of BNB, top
it up occasionally, and note that the bot's P&L leaves out fees paid in BNB
(`fill_summary` counts only fees paid in USDT or the coin), so reported
profit would be slightly flattering. No change made.
