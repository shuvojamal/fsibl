# Opportunity strategy backtests, 2026-10-22

Eight independent checks, one point each; a trade is taken only when
`min_score` of them agree. ATR stop (2×), 2:1 reward-to-risk target, 1% of
equity risked per trade. Fees 0.1% per side, 0.05% slippage, fills at the
next candle's open. Walk-forward: tuned on the first 70% of each series,
judged on the last 30%.

## 1-hour candles (Mar–Oct 2026)

| Coin | min_score | Trades/mo | Win | Profit factor | Return | Buy & hold |
|---|---|---|---|---|---|---|
| BTC | 4 | 65.7 | 20% | 0.44 | −66.2% | +22.9% |
| BTC | 5 | 32.0 | 26% | 0.57 | −40.8% | +22.9% |
| BTC | 6 | 14.5 | 28% | 0.65 | −24.4% | +22.9% |
| BTC | 7 | 1.7 | 58% | 2.78 | +6.9% | +22.9% |
| ETH | 7 | 2.7 | 37% | 1.08 | −1.2% | +20.6% |
| SOL | 7 | 4.0 | 32% | 0.98 | −3.0% | +26.7% |

The pattern is the same on all three coins: the more selective, the less
money lost. At hourly resolution a 2×ATR stop is only about 2% away, so the
0.3% round-trip cost is 15% of the risk on every trade, and frequent
trading bleeds out through fees. Only the strictest setting (7 of 8) comes
out near break-even, on too few trades to trust.

## 4-hour candles (Jul 2024–Oct 2026)

| Coin | min_score | Trades/mo | Train return | **Test return** | Test B&H |
|---|---|---|---|---|---|
| BTC | 5 | 10.9 | −6.6% | −4.4% | +15.7% |
| BTC | 6 | 4.6 | +3.0% | −2.7% | +15.7% |
| BTC | 7 | 1.0 | +4.6% | −5.2% | +15.7% |
| ETH | 6 | 4.5 | −0.9% | −4.9% | +14.1% |
| SOL | 6 | 4.2 | +6.7% | −6.2% | +19.4% |

Loses on unseen data at every setting.

## Daily candles (Sep 2022–Oct 2026)

| Coin | min_score | Trades/mo | Win | PF | Train return | **Test return** | Test B&H | Max DD |
|---|---|---|---|---|---|---|---|---|
| BTC | 5 | 1.8 | 45% | 1.37 | +15.7% | **+3.8%** | −28.9% | −8.8% |
| ETH | 5 | 1.5 | 44% | 1.28 | +8.4% | **+2.8%** | −35.0% | −5.0% |
| SOL | 5 | 1.5 | 43% | 1.17 | +5.5% | **+0.7%** | −41.7% | −10.7% |
| BTC | 6 | 1.0 | 44% | 1.49 | +14.6% | +1.2% | −28.9% | −5.7% |
| ETH | 6 | 0.7 | 41% | 1.17 | +6.7% | −2.1% | −35.0% | −5.4% |

This is the only configuration that is profitable on both the tuning data
and the unseen data, on all three coins, with the same settings. Note what
the unseen period was: a market where simply holding lost 29–42%. The bot
made a few percent because it was mostly *out*: about one or two trades a
month, each risking 1% of equity, small drawdowns.

Over the full four years, though, buy-and-hold made +275% on BTC and the
strategy made +11%. Selectivity protects capital; it does not capture a
bull run, because the bot is in the market for a small fraction of the
time and risks 1% at a time.

## What to take from this

- "Only trade when there's a real opportunity" works in the sense the
  books promise: fewer trades, higher win rate, small drawdowns, and it
  sidesteps the crashes. It does not turn a small account into a big one.
- Daily candles, `min_score` 5, risk 1% is the recommended setting. The
  bot will look once a day and trade one to two times a month.
- The test-period edge (+1% to +4% over 14 months) is small enough that it
  could be luck. Paper-trade it for months before believing it.
- Raising `--risk` scales both the gains and the drawdowns in proportion.
  2% is still conservative; 5% and up is how accounts blow up.
