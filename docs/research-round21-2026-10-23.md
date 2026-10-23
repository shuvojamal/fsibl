# Research round 21: is the edge a lucky choice of candle close time? (2026-10-23)

**Question.** All backtests, and both live bots, use daily candles that
close at 00:00 UTC. A real trend edge shouldn't depend on when the "day"
ends. If results swing a lot when the close moves, part of the backtest is
timing luck.

Script: `research/scripts/research21.py`. Output: `research/results/research21.out`.
Data: hourly Binance candles for the 30 coins that filled most of the bot's
top-15 slots in round 12, 2017-08 onward (about 1.9 million hourly
candles), rebuilt into daily candles closing at 00, 04, 08, 12, 16 and 20
UTC. Cached as `research/data/daily_offsets.pkl.gz`. Round 12's simulator
and universe rule, live rules unchanged, scored from 2018-03.

## Results

| Close (UTC) | Return/yr | Max DD | Sharpe | Trades | Avg R |
|---|---|---|---|---|---|
| **00:00 (live)** | **+25.4%** | −36.2% | **1.03** | 476 | +0.50 |
| 04:00 | +18.3% | −39.6% | 0.79 | 504 | +0.38 |
| 08:00 | +18.8% | −41.6% | 0.83 | 495 | +0.38 |
| 12:00 | +12.8% | −43.1% | 0.63 | 504 | +0.25 |
| 16:00 | +18.2% | −41.2% | 0.79 | 511 | +0.35 |
| 20:00 | +19.7% | −36.0% | 0.87 | 502 | +0.38 |

All six lost in 2018, 2022 and 2025, and all six made money in the other
years.

## What it means

- **The edge is real across timings.** Every close time is profitable,
  with positive expectancy per trade, and the same years are good and bad.
  That's what a genuine trend effect looks like.
- **The headline number is the lucky end.** 00:00 ranks first of six.
  The median close time makes about +18%/yr with Sharpe about 0.8, not +25%
  and 1.0. There may be a real reason 00:00 does best: it's the "official"
  daily close most traders and exchanges use, so breakouts there may be
  seen and followed by more people. But this test can't tell that apart
  from luck.
- In this 30-coin universe, drawdowns run to −36% to −43%, deeper than
  round 12's −31%.

## Decision

- Keep 00:00 UTC. It's the standard close, and switching to another time
  because it tested better would itself be curve-fitting.
- Lower the planning numbers: `docs/STRATEGY.md` section 7 now says
  drawdowns of 20–40%, and says to plan around the median (about +18%/yr)
  rather than the headline.
