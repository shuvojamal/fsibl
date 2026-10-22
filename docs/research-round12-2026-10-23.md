# Strategy research, round 12 (2026-10-23): 9-year stress test, metrics, Monte Carlo

The final rules, unchanged, on daily candles from **August 2017 to October
2026**: the 2018 crash (BTC −73%), the March 2020 crash, the 2022 collapse
(BTC −64%, FTX), and the 2025 chop. Pool of 55 coins including many that
later faded (EOS, NEO, IOTA, DASH, QTUM, ICX, WAVES, OMG, ZIL, XMR...).
Rules: top 15 by trailing-90-day volume (quarterly), 5 of 8 checks, RSI
40–80, 2×ATR initial stop, 3×ATR trailing stop, 1% risk, max 5 open,
highest score first, stops acted on at the daily close (as the live bot does).
Scripts: `research/scripts/research12.py`, `research12b.py`.

## Whole period

| Metric | Value |
|---|---|
| Total return | +553% (vs BTC buy & hold +1,873%) |
| Per year (CAGR) | **+22.7%** |
| Maximum drawdown | **−31.4%** |
| Sharpe / Sortino / Calmar | 0.97 / 1.46 / 0.72 |
| Trades | 487 (about 53 a year) |
| Win rate | 34% |
| Expectancy | **+0.46R per trade** (average win +2.83R, average loss −0.79R) |
| Profit factor | 1.89 |
| Best trade | +32R |

## Year by year

| Year | Strategy | Worst drop in year | Trades | BTC |
|---|---|---|---|---|
| 2018 | **−13.6%** | −16.3% | 18 | −73.0% |
| 2019 | +32.4% | −22.2% | 49 | +94.4% |
| 2020 | +61.5% | −19.9% | 61 | +302.0% |
| 2021 | +53.5% | −13.0% | 69 | +59.8% |
| 2022 | **−27.6%** | −27.7% | 53 | −64.2% |
| 2023 | +76.8% | −19.4% | 59 | +155.6% |
| 2024 | +33.4% | −19.1% | 73 | +121.3% |
| 2025 | **−10.8%** | −20.5% | 68 | −6.3% |
| 2026 (to Oct) | +43.0% | −11.4% | 37 | −4.1% |

Six winning years, three losing. It loses in bear markets, but a fraction
of what holding loses; it lags badly in strong bull years (2020: +62% vs
BTC +302%). That is the trade-off of a risk-controlled trend follower.

## Market regime at entry

| BTC vs its 200-day EMA | Trades | Win | Expectancy |
|---|---|---|---|
| Above (bull) | 327 | 36% | +0.42R |
| Below (bear) | 160 | 31% | +0.55R |

Positive in both regimes. Coins can trend up while BTC is weak; a BTC
regime filter would have thrown away good trades (consistent with round 2).

## Trade distribution

| Result | Trades |
|---|---|
| worse than −1.5R (gapped through the stop) | 13 |
| −1.5R to −0.5R (normal stop-outs) | 230 |
| −0.5R to 0 | 76 |
| 0 to +1R | 58 |
| +1R to +3R | 57 |
| +3R to +10R | 48 |
| more than +10R | 5 |

The best 10% of trades produce **179% of the total profit**; the other 90%
lose money in aggregate. The strategy only works if it is in the market
when the rare large trend comes. Skipping trades at random, or stopping
after a losing streak, is how this kind of system fails in practice.

## Stress and variants (whole period)

| Variant | Per year | Max DD | Sharpe | Expectancy |
|---|---|---|---|---|
| **Baseline** | +22.7% | −31.4% | 0.97 | +0.46R |
| Costs ×2 | +20.8% | −32.3% | 0.91 | +0.43R |
| Costs ×3 | +19.0% | −33.2% | 0.85 | +0.40R |
| Risk 0.5% per trade | +12.1% | −17.1% | 0.97 | +0.46R |
| Risk 2% per trade | +33.8% | **−54.5%** | 0.91 | +0.46R |
| Top 10 instead of 15 | +24.9% | −33.8% | 1.06 | +0.53R |
| ADX(14) > 25 required | +25.9% | −31.3% | 1.12 | +0.62R |

## 12b. Checking the two improvements out of sample

A rule found on the whole period must help in both halves to be trusted.

| Variant | 1st half 2017–22 | 2nd half 2022–26 | 2018 | 2022 | 2025–26 |
|---|---|---|---|---|---|
| Baseline | +166% / Sharpe 1.07 | +140% / 0.87 | −13.6% | −26.0% | +27.7% |
| ADX > 25 | +313% / 1.54 | **+99% / 0.74** | −2.7% | −21.5% | **−1.8%** |
| ADX > 20 | +268% / 1.37 | +97% / 0.72 | −5.9% | −25.7% | +3.2% |
| ADX > 30 | +192% / 1.27 | +61% / 0.60 | −4.3% | −16.7% | −19.6% |
| Top 10 | +187% / 1.15 | +161% / 0.96 | −13.6% | −22.3% | +31.5% |

- **ADX filter: rejected.** Big gains in the first half, worse in the
  second, and it turns 2025–26 negative. It fitted the 2017–2021 market.
- **Top 10: not adopted yet.** Better in both halves here, but round 9
  found top 15 better over 2022–26 with a different pool. Mixed evidence;
  top 15 kept for diversification. Re-test when more live data exists.

## Monte Carlo (10,000 resamplings of the 487 actual trades, 1% risk)

| Quantity | Median | 1-in-20 bad | 1-in-100 bad |
|---|---|---|---|
| Max drawdown over 9 years | −16% | −25% | −31% |
| First-year return | +23% | −5% | (1-in-20 good: +78%) |
| Chance the first year loses money | 10% | | |

The resampling ignores that up to 5 positions overlap, so real drawdowns
run deeper (the actual history hit −31%). Read it as the shape of the risk.

## Decisions

- Rules unchanged: they hold over 9 years, three bear phases and triple costs.
- **Hard circuit breaker added to the live bot (`--max-drawdown`)**: if the
  bot's equity falls 35% below its peak, it stops opening positions until a
  person resets it. 35% sits just beyond the worst drawdown seen in 9 years
  and the 1-in-100 Monte Carlo case, so in normal operation it never fires;
  if it does, the strategy is behaving outside anything observed and should
  be reviewed, not left running. It is independent of the strategy and
  cannot be overridden by it. Exits keep working while it is tripped.
- Recommended risk stays 1%. 2% gives a −55% drawdown, which most people
  abandon, and abandoning a trend follower mid-drawdown locks in the loss.

## Known limitations

- Survivorship: the old Terra LUNA (crashed May 2022) and other delisted
  coins are not downloadable; `LUNAUSDT` today is the post-crash Terra 2.0.
  The volume filter drops collapsing coins quickly, but losses on such
  collapses are understated.
- Daily candles only: intraday gaps through a stop are modelled at the
  next close, as the live bot behaves.
- No funding rates, open interest or order-book data: spot only, and the
  historical data for those is not freely available far enough back.
