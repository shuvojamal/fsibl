# Strategy research, round 1 (2026-10-22)

Three strategy families, 10 coins (BTC, ETH, SOL, XRP, DOGE, ADA, LINK,
AVAX, DOT, LTC), daily candles 2022-09-13 → 2026-10-21. Fees 0.1% per side,
0.05% slippage, 1% of equity risked per trade, fills at the next open.

**Walk-forward:** parameters are chosen on the first 70% of each series
(to 2025-07-29) and judged on the last 30% (2025-07-29 → 2026-10-21),
which the tuning never saw.

**Two ways of choosing parameters, compared:**
- *per-coin tuned*: the best setting for each coin on its own past;
- *universal*: the one setting with the best average across all ten coins'
  training data, then applied unchanged to every coin's test period.

The test period was a bear market: buy-and-hold lost 29% to 72% depending on
the coin, −50.5% on average.

## Opportunity scorer (27 parameter sets)

Universal pick: `min_score=5, stop_atr=2.0, reward_risk=3.0`

| Coin | Tuned: train | Tuned: **test** | Universal: train | Universal: **test** | Trades | Win | PF | B&H test | Max DD |
|---|---|---|---|---|---|---|---|---|---|
| BTC | +21.1% | +4.8% | +17.3% | **+3.8%** | 14 | 57% | 2.01 | −28.9% | −1.9% |
| ETH | +11.6% | −1.9% | +6.9% | **+3.7%** | 10 | 50% | 2.00 | −35.0% | −2.1% |
| SOL | +21.8% | −1.6% | +5.7% | **+1.7%** | 14 | 43% | 1.27 | −41.7% | −2.6% |
| XRP | +13.9% | +0.0% | +11.7% | +0.5% | 13 | 31% | 0.91 | −56.4% | −2.1% |
| DOGE | +11.2% | −0.4% | +5.3% | −2.5% | 10 | 20% | 0.23 | −63.8% | −3.4% |
| ADA | +9.5% | +0.0% | +6.5% | +0.3% | 7 | 43% | 0.97 | −71.7% | −2.0% |
| LINK | +5.6% | +2.0% | +4.2% | **+1.7%** | 13 | 38% | 1.29 | −31.1% | −3.7% |
| AVAX | +9.3% | −0.9% | +6.7% | +0.6% | 8 | 12% | 1.43 | −61.8% | −2.7% |
| DOT | +3.1% | +1.7% | +0.9% | **+2.9%** | 4 | 75% | 2.83 | −71.2% | −1.2% |
| LTC | +3.3% | −2.9% | −1.5% | −0.7% | 15 | 27% | 1.02 | −43.6% | −3.1% |
| **Average** | | **+0.1%** | | **+1.2%** | | | | −50.5% | |

Universal setting on unseen data: profitable on 8 of 10 coins, beat
buy-and-hold on 10 of 10, worst drawdown −3.7%.

## Donchian breakout (12 parameter sets)

Universal pick: `entry=20, exit=20, stop_atr=2.0`. On test data: 1–2 trades
per coin, average −0.4%, profitable on 2 of 10. Training returns of +15% to
+40% did not carry over at all. A daily breakout rule simply did not fire
in a falling market, and when it did it was a false break.

## RSI(2) dip-buying (27 parameter sets)

Universal pick: `lo=10, hi=80, stop_atr=3.0`. On test data: 0–3 trades per
coin, average −0.1%, profitable on 3 of 10. Requires price above the
200-day EMA, which rarely held in the test period, so it mostly sat out.

## What this round taught

1. **Per-coin tuning is overfitting.** Tuned per coin, the scorer averaged
   +0.1% on unseen data; one universal setting averaged +1.2%. The
   per-coin "best" settings looked better on the past (+3% to +22%) and
   worse on the future. Same lesson as the hourly EMA strategy earlier.
2. **A wider target helps.** 3:1 reward-to-risk beat 2:1 and 1.5:1 across
   coins, so it is now the default.
3. **Only the scorer earns a place on the demo account.** The other two
   families produce too few trades on daily candles to judge, and what
   they did produce lost money.
4. **The edge is small and the period is one bear market.** +1.2% in 15
   months at 1% risk is capital preservation, not income. At 2% risk it
   would be roughly +2.4% with ~7% drawdowns. The result still needs to
   hold up in a rising market, and in real time on the demo, before it
   deserves more than that.

## Next rounds

- Add a higher-timeframe regime filter (BTC above its 200-day EMA → allow
  entries on all coins) and test whether it improves the win rate.
- Test the scorer on 4h candles again with the 3:1 target and a stricter
  score, where trade frequency is higher.
- Run a third 70/30 split starting a year later to see whether the
  universal setting is stable across different test windows.
