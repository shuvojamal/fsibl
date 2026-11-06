# Research round 54: wait for a second day's confirmation before buying? (scheduled daily run)

**Prompt.** The VPS testnet bought ETH on 2026-11-05 at 2,425.79 and was
stopped out the next day at 2,240.59 (−49.02 USDT). Would buying only when
the signal holds on two closes in a row filter out such one-day blips?

**Method.** Live entry vs "confirm 2 days" (the coin must also have scored
6 of 8 on the previous close). Steady and growth, top 15, round 12's
simulator and costs, round 21's 12 cells. Pass bar (set first, with the
effect-size floor from round 53): higher Sharpe in at least 9 of 12 cells
AND at least +0.5 points of 2022-26 return or a 1-point shallower drop.

**Result** (`research/results/research54.out`):

| | 2018-21 return | 2022-26 return | worst drop 22-26 | win rate | Sharpe wins |
|---|---|---|---|---|---|
| steady, live | +29.5% | +15.7% | −16.4% | 36% | ref |
| steady, confirm 2 days | +12.7% | +12.6% | −12.8% | 39% | 4 of 12 |
| growth, live | +61.7% | +25.9% | −28.3% | 37% | ref |
| growth, confirm 2 days | +25.2% | +23.3% | −22.5% | 39% | 5 of 12 |

**Verdict: fails.** Confirmation raises the win rate only from 36-37% to
39% and cuts trades by about 30%; it misses or enters late on the strong
trends that make the strategy's money, halving bull-market returns. Drops
are shallower mainly because less money is at work. Quick stop-outs like
ETH's are the normal cost of catching trends early. No change.
