# Research round 67: does it matter when a real account starts? (scheduled daily run)

**Question.** The strategy is in a losing stretch now (testnet −6.1%, matching
the backtest). For the owner's real-money start: is a 1-year result better
when an account starts after the strategy has fallen from its high, or
after a strong run?

**Method.** Steady set-up, round 12's simulator, round 21's six close times;
every start day grouped by how far the strategy was below its equity high,
with the return over the next 365 days. Pass bar (set first): "start after a
drawdown" if starts 5%+ below the high beat starts at a high by at least 3
points of median 1-year return in both halves.

**Result** (`research/results/research67.out`, median 1-year return / chance of a loss):

| start | 2018-21 | 2022-25 |
|---|---|---|
| at/near a high | +20.9% / 8% | +15.7% / 22% |
| 2-5% below | +20.3% / 19% | +14.6% / 28% |
| 5-10% below | +35.4% / 11% | +3.7% / 32% |
| more than 10% below | +24.8% / 0% | +11.6% / 30% |

**Verdict: timing doesn't matter in a useful way.** Starting after a
drawdown helped in the 2018-21 bull market but did worse in 2022-25. No
consistent pattern, so there is no point waiting for a "better moment".

**Meaning for the owner:** start real money when the demo period is done
and the checks are in place (backstop orders, a no-orders test), whatever
the strategy's recent results. A bad recent patch is not a reason to wait,
nor a good one a reason to rush.
