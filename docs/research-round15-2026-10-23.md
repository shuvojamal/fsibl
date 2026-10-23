# Research round 15: does the Kronos AI model predict crypto returns? (2026-10-23)

**Question.** PkLavc/Autotrader picks US stocks with Kronos, an open-source
forecasting model (github.com/shiyu-coder/Kronos, AAAI 2026) pre-trained
on candles from 45+ exchanges, crypto included. Does it predict our coins
well enough to trade on, or to use as an extra check before the bot buys?

Script: `research/scripts/research15.py`. Output: `research/results/research15.out`.
Forecast cache: `research/data/kronos_forecasts.pkl` (Kronos commit 67b630e).

## Setup

- Kronos-small, 400-day lookback, 3 samples (Autotrader's settings),
  forecasting each of 15 large coins' close 5 days ahead.
- Run from every daily close from 2025-09-01 to 2026-10-16: 411 days, 6,165
  forecasts.
- Only data after the model's August 2025 release is scored, because the
  model may have seen earlier prices during training.
- **Measures:**
  - information coefficient (IC): rank correlation, across the 15 coins on
    each day, between forecast and realised 5-day return
  - sign hit rate
  - a portfolio holding the 3 best forecasts every 5 days, costs included
- **Baselines:** a naive forecast (last 5 days' return), holding all 15
  equally, and BTC.

## Results

| | Mean IC | t-stat | Sign hit rate |
|---|---|---|---|
| Kronos | +0.037 | +1.09 | 52.7% |
| Naive (last 5 days) | +0.001 | +0.03 | 49.0% |
| Always say "down" | — | — | 54.9% |

Total return over the 14 months, across 5 different start days (costs 0.15%
per side):

| | Range across start days | Worst drawdown |
|---|---|---|
| Kronos top 3 above +1% | **−45% to −69%** | −80% |
| Naive top 3 above +1% | +3% to −36% | −67% |
| All 15 coins, equal weight | −35% to −39% | −65% |
| BTC buy & hold | −25% | |

## What it means

- Kronos has a slight tilt in the right direction (IC +0.037), but it's
  not statistically meaningful (t = 1.1). Its sign hit rate of 52.7% is
  lower than simply always saying "down" in this falling market (54.9%).
- Trading its top picks did clearly worse than holding all 15 coins.
  Picking its most bullish forecasts every 5 days loaded up on the coins
  that then fell hardest, and the frequent switching added costs.
- This was a bad market (BTC −25%, alts worse). A long-only picker will
  struggle in one, but the comparison with "all 15 equally" in the same
  market is fair, and Kronos lost to it.
- The model isn't useless as research, and 14 months is a short test. But
  there's no evidence here that it adds anything to the trend bot, and
  using it would add a 100 MB model, PyTorch, and about 25 s of compute
  per day.

## Decision

Rejected as a signal or filter. If it's revisited, the test to run would be
Kronos as a veto on the trend bot's own buy signals (does a strongly
negative forecast predict that the buy will fail?), using the cache above.
That's a new trial and would count against the deflated-Sharpe bar.
