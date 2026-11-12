# Research round 60: is the testnet's first three weeks within expectations? (scheduled daily run)

**Prompt.** The VPS testnet (growth set-up, 8 × 1%) went from 5,000 USDT on
2026-10-23 to 4,700.28 on 2026-11-12: −6.0% in 20 days, six closed trades,
five of them losers.

**Method.** Every 20-day window of the growth set-up's backtest equity
(round 12's simulator, round 21's six close times, 2018-26 and 2022-26).
Pass bar (consistency test, set first): consistent if −6.0% is above the
5th percentile of 2022-26 windows.

**Result** (`research/results/research60.out`):
- 2022-26: the live result is at the **8th percentile** (5th percentile
  −7.0%, median −0.2%); a 20-day result this bad or worse happens about 1 time
  in 12.
- 2018-26: 6th percentile (5th percentile −6.6%).

**Verdict: consistent with the backtest, but an unlucky start.** Execution
is not the cause: the live-vs-backtest check matches 10 of the testnet's
trades with fills within about 1% of the backtest's. This is the market
the strategy met (several short-lived breakouts that reversed), not the bot
behaving differently. Rounds 48 and 51 already showed losing starts are
common; per round 51, a 90-day result below about −13% for growth would be
the point to investigate.
