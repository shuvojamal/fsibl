# Research round 36: 500 USDT for 5 years with today's set-ups

The owner asked what CAGR to expect from 500 USDT over 5 years "under
existing conditions". Round 25 answered for the old set-up; this uses the
current ones (steady 8 × 0.5%, growth 8 × 1%, 6 of 8 checks), with and
without auto savings on idle USDT at 3%/yr.

Method: 4,000 five-year block-bootstrap paths (30-day blocks) of the daily
returns from round 21's six close times, costs included. Realistic =
minus a drag for live execution and backtest optimism (3%/yr steady, 6%/yr
growth); stress = half the daily return kept. Two pools of history: all of
2018-26 (with the 2020-21 bull market) and 2022-26 only (cautious).
Full table: `research/results/research36.out`.

**Median CAGR, realistic scenario:**

| set-up | cautious (2022-26 markets) | all history (2018-26) |
|---|---|---|
| steady | +10.3% | +16.9% |
| steady + savings | +13.0% | +19.8% |
| growth | +15.6% | +30.0% |
| growth + savings | +17.4% | +32.8% |

**500 USDT after 5 years, steady + savings, cautious view:** median about
920; bad 5% about 485 (a small loss); good 5% about 1,920. Chance of ending
below 500: 6%. Typical worst drop along the way: about −21%.

Growth + savings, cautious view: median about 1,120, but bad 5% about 370,
chance of a loss 12%, typical worst drop −37%.

**Planning number:** steady with auto savings, about **12-13% a year**
(500 → ~900 in 5 years), with a wide range around it. The higher
"all history" figures need another 2020-21-style bull market.
