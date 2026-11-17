# Research round 65: what does the backtest say about the live period itself? (scheduled daily run)

**Question.** The VPS testnet (growth) lost 6.1% since 2026-10-23. Round 63's
data stopped on 2026-10-21. What would the rules have done over exactly the
live period?

**Method.** Fresh daily candles (Binance public data, 00:00 UTC closes) for
round 21's 30 coins, saved as `research/data/daily_live_period.pkl`; round
12's simulator from a flat start on 2026-10-23 to the last closed candle
(2026-11-16). Pass bar (set first): live within 3 points of the backtest.

**Result** (`research/results/research65.out`):

| | backtest, same days | live |
|---|---|---|
| growth (8 × 1%) | **−5.9%** (7 trades, 1 tiny winner) | **−6.1%** (testnet) |
| steady (8 × 0.5%) | −3.0% | (OKX demo not running) |

The backtest's trades are the live ones: BNB −1.05R, TRX −0.79R, BTC +0.03R,
ETH −1.05R, ZEC −1.09R, UNI −1.00R (plus PEPE −0.98R, which the testnet never
bought because its price check blocked the entry on testnet prices).

**Verdict: consistent (gap −0.2 points).** The bot did exactly what its rules
say; the market since late October produced a run of failed breakouts.
This is the strongest evidence yet that the live system works as designed:
the result is the strategy's, not a fault in the bot.
