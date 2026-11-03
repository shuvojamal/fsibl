# Research round 51: what a 90-day demo should show (scheduled daily run)

**Question.** The owner tests on demo/testnet for about 90 days before real
money. What spread of 90-day results do the live rules produce, and what
result would be a genuine red flag?

**Method.** Every 90-day window (daily step) of steady and growth equity
curves (6 of 8 checks, top 15, round 12's simulator and costs), round 21's
six close times, 2018-03 .. 2026-10 and the 2022-26 part. Pass bar
(expectation test, set first): a losing 90-day demo is "not evidence against
the strategy" if at least 25% of 90-day windows lose money.

**Result** (`research/results/research51.out`):

| | chance of a loss | 5th pct | median | 90th pct | worst |
|---|---|---|---|---|---|
| steady, 2018-26 | 49% | −5.9% | 0.0% | +20.5% | −13.7% |
| steady, 2022-26 | 60% | −6.9% | −0.9% | +19.8% | −13.7% |
| growth, 2018-26 | 49% | −11.1% | 0.0% | +39.7% | −22.9% |
| growth, 2022-26 | 59% | −12.8% | −1.8% | +35.9% | −22.9% |

**Verdict: passes.** About half of all 90-day periods lose money, and the
typical 90 days is roughly flat; the strategy's profit comes from the
occasional strong quarter (the top 10% of windows made +20% to +40%).

**Meaning for the owner's plan.**
- The 90-day demo cannot show whether the strategy is profitable; that
  takes years (round 35: up to ~21 months below a previous high).
- What it can and should show is that the bot behaves like the backtest:
  trades matching the live-vs-backtest check, fills close to expected prices,
  no errors. That is the real pass/fail for going live.
- Red-flag lines for the result itself: worse than about −7% (steady) or
  −13% (growth) over 90 days is below the 5th percentile and worth
  investigating for bugs or bad execution.
