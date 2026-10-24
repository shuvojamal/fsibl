# Research round 33: a closer look at the eight buy checks

The owner asked for a deeper analysis of the buy signal. The bot buys when
at least 6 of these 8 checks pass on the daily close:

| check | passes when |
|---|---|
| trend_up | price above the 200-day EMA, and that EMA rising |
| ema_aligned | 20-day EMA above the 50-day EMA |
| momentum | MACD histogram above zero and rising |
| rsi_zone | RSI(14) between 40 and 80 |
| volume | today's volume above its 20-day average |
| volatility_ok | ATR between 0.5% and 5% of price |
| breakout | close above the previous 20-day high |
| pullback | close within 1 ATR of the 20-day EMA |

Data: round 21's 30 coins at six daily close times (2018-03 to 2026-10),
split 2018-21 / 2022-26. R = profit in multiples of the initial risk
(entry minus the 2xATR stop), after fees and slippage, using the live exit.

## A. Does the score mean anything? Yes, more checks mean better trades

Every coin-day, no portfolio limits (`research/results/research33.out`):

| score | days 2022-26 | avg R | win rate |
|---|---|---|---|
| 4 | 69,445 | +0.30 | 31% |
| 5 | 35,942 | +0.53 | 35% |
| 6 | 11,789 | +0.83 | 38% |
| 7 | 2,249 | +0.92 | 41% |
| 8 | 2 | — | — |

In 2022-26 the payoff rises steadily with the score, which supports the
6-of-8 setting from rounds 24/29. (In the 2018-21 bull market scores 4-6
all paid about +1R; 7 paid +1.8R.) The typical trade still loses (median
-0.5R): the edge comes from a few big winners the trailing stop lets run,
which is why win rates sit near 40%.

All 8 at once almost never happens: breakout (a new 20-day high) and
pullback (close near the 20-day EMA) rarely agree, so in practice the
bot's maximum is 7.

## B. What each check adds (signal days, score 6+)

| check | passes on | avg R if passed / failed, 2022-26 |
|---|---|---|
| volatility_ok | 59% | **+0.97 / +0.53** (2018-21: +1.85 / +0.76) |
| trend_up | 96% | +0.87 / +0.31 |
| momentum | 83% | +0.86 / +0.78 |
| volume | 94% | +0.85 / +0.78 |
| breakout | 53% | +0.88 / +0.81 |
| rsi_zone | 97% | +0.84 / +0.91 |
| pullback | 37% | +0.77 / +0.89 |
| ema_aligned | 95% | +0.73 / +2.75 (few cases) |

- **volatility_ok is the strongest single filter.** Coins moving more than
  5% a day (ATR) make poor trades: the 2xATR stop is too far away.
- **rsi_zone barely matters**: it passes 97% of the time; it rarely decides.
- **pullback and breakout pull in opposite directions** and each only
  passes about half the time or less; together they act as "either a fresh
  high or a calm re-entry".

## C. Remove or require a check (portfolio simulation, 12 cells)

Steady set-up (8 slots, 0.5% risk, 6 checks, top 15). Pass bar set before
running: higher Sharpe than live in at least 10 of 12 cells (stricter than
the usual 9, because 16 variants were tried) and no more than 3 points
deeper 2022-26 drop.

| variant | 2022-26 return / Sharpe | worst drop | Sharpe wins (18-21 / 22-26) |
|---|---|---|---|
| live (6 of 8) | +15.7% / 1.03 | -16.4% | ref |
| **trend_up removed** | +16.0% / 0.92 | -17.3% | **10 of 12** (6/4), passes |
| ema_aligned removed | +16.9% / 0.99 | -18.4% | 9 (6/3) |
| pullback removed | +13.8% / 0.82 | -18.6% | 9 (6/3) |
| momentum required | +14.9% / 0.98 | -16.3% | 8 (5/3) |
| volume required | +15.4% / 1.01 | -16.2% | 8 (4/4) |
| volatility_ok required | +14.3% / 1.07 | -12.8% | 6 (0/6) |
| momentum removed | +9.2% / 0.62 | -19.1% | 0 |
| volatility_ok removed | +5.6% / 0.42 | -21.7% | 4 (4/0) |
| breakout removed | +13.5% / 0.78 | -21.7% | 2 |

(Full table in the results file.) Removing momentum, volatility_ok, volume
or breakout clearly hurts: they earn their place. Making volatility_ok
mandatory won every 2022-26 cell with the shallowest drop (-12.8%), but
lost every 2018-21 cell, so it fails.

**trend_up removed** passed the bar, but most of its wins came from the
2018-21 half and its 2022-26 median Sharpe was lower. So it was checked on
a second data set before any conclusion (bar set first: higher Sharpe in
both halves):

## D. Second data set: round 12's 55-coin pool

| variant | 2018-21 return / Sharpe / drop | 2022-26 return / Sharpe / drop |
|---|---|---|
| live (6 of 8) | +28.4% / 1.59 / -11.4% | +9.5% / 0.69 / -16.4% |
| trend_up removed | +36.1% / 1.76 / -13.5% | +17.3% / 1.00 / -15.5% |

Confirmed in both halves.

## Verdict

Removing the 200-day trend check (it then always counts as passed, so a buy
needs 5 of the other 7) **passes**, with caveats:

- It's one pass out of 16 variants; the 30-coin test's 2022-26 median
  Sharpe was lower (0.92 vs 1.03), even though it won 4 of those 6 cells.
- The 55-coin pool overlaps the 30 coins and shares the 00:00 close, so
  part D is a second look, not a fully independent test.
- Why it might be real: the 200-day EMA reacts late. After a crash, coins
  can trend up for months before price clears it and it turns up; the
  other checks (EMA alignment, momentum, breakout) catch those turns
  earlier, and the stop limits the damage when they fail.
- Why it might not: Part B shows the few signals that fail trend_up did
  worse per trade in 2022-26 (+0.31R vs +0.87R). The portfolio gains come
  from taking more trades (326 vs 253), not better ones.

**Action:** no default changed. It's now a switch, "Skip the 200-day trend
check", in the app's strategy settings (settings.json `ignore_trend`,
`--ignore-check trend_up`), so it can be compared live on one demo account
against the other before it goes near the real account.
