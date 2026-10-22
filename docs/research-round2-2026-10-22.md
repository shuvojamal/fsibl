# Strategy research, round 2 (2026-10-22)

Three questions about the opportunity scorer that survived round 1, plus a
robustness check. Same setup: 10 coins, fees 0.1%/side, 0.05% slippage,
1% of equity risked per trade, next-open fills.

## A. Does a BTC regime filter help?

Only take entries when BTC itself is above its 200-day EMA (market-wide
risk-on). Daily candles, test window 2025-07-29 → 2026-10-21.

| | Plain scorer | With BTC filter |
|---|---|---|
| Average test return | **+1.2%** | +0.2% |
| Coins profitable | **8/10** | 5/10 |
| Trades (10 coins) | 108 | 31 |

**No.** The filter removed most trades, including most of the winners.
The scorer's own 200-EMA check on each coin already does this job. Dropped.

## B. Is the universal setting stable across time windows?

Re-run the round-1 selection with the train/test split at 50%, 60%, 70%
and 80% of the history.

| Split | Test window | Setting chosen on training data | Avg test | Profitable | Avg B&H |
|---|---|---|---|---|---|
| 50% | 2024-10 → 2026-10 | score 4, stop 3.0, 3:1 | −0.5% | 3/10 | −4.4% |
| 60% | 2025-03 → 2026-10 | score 4, stop 2.0, 3:1 | −2.8% | 1/10 | −37.9% |
| 70% | 2025-07 → 2026-10 | score 5, stop 2.0, 3:1 | +1.2% | 8/10 | −50.5% |
| 80% | 2025-12 → 2026-10 | score 5, stop 2.0, 3:1 | +1.9% | 8/10 | −19.2% |

**Not stable.** With earlier splits the training data prefers a looser
score (4 of 8), and that setting loses on its test window. The round-1
result depends on where the split falls, which is the signature of a weak
or lucky edge, not a strong one.

Then the fixed setting from round 1 (score 5, stop 2.0, 3:1), applied to
every window with no re-tuning:

| Test window | Avg return | Profitable | Trades | Avg PF | Avg B&H |
|---|---|---|---|---|---|
| 2024-10 → 2026-10 | +0.3% | 5/10 | 203 | 0.99 | −4.4% |
| 2025-03 → 2026-10 | −1.5% | 2/10 | 158 | 0.67 | −37.9% |
| 2025-07 → 2026-10 | +1.2% | 8/10 | 108 | 1.40 | −50.5% |
| 2025-12 → 2026-10 | +1.9% | 8/10 | 52 | 2.07 | −19.2% |
| 2026-05 → 2026-10 | 0.0% | 0/10 | **0** | — | +7.0% |

And over the full four years as one block (includes the 2023–24 bull run):

| Coin | Return | Trades | Win | PF | Max DD | Buy & hold |
|---|---|---|---|---|---|---|
| BTC | +14.6% | 81 | 44% | 1.56 | −7.3% | +274.7% |
| ETH | +9.1% | 66 | 39% | 1.32 | −7.8% | +43.8% |
| SOL | +9.7% | 60 | 40% | 1.34 | −9.0% | +185.1% |
| XRP | +6.9% | 93 | 41% | 1.12 | −6.1% | +278.7% |
| DOGE | −0.1% | 58 | 31% | 0.91 | −9.8% | +27.9% |
| ADA | +5.4% | 51 | 35% | 1.06 | −6.0% | −55.2% |
| LINK | +7.2% | 44 | 39% | 1.31 | −6.3% | +60.8% |
| AVAX | +5.6% | 36 | 33% | 1.42 | −7.5% | −54.9% |
| DOT | +2.0% | 41 | 41% | 0.90 | −5.3% | −85.1% |
| LTC | −3.8% | 68 | 31% | 0.79 | −8.7% | +0.1% |
| **Average** | **+5.7%** | | | | | +67.6% |

Reading: over a long horizon the fixed setting is positive on 8 of 10
coins with drawdowns under 10%, about +1.4% a year at 1% risk per trade.
But it has losing stretches (the 2025-03 window: it bought the spring
2025 rally and was stopped out in the crash) and fallow stretches (**zero
trades on any coin since 2026-05-25**, which is also why the demo bot has
done nothing). And it captures almost none of a bull run: +14.6% on BTC
against +275% for holding.

## C. Does the scorer work on 4h candles?

4h candles 2024-07 → 2026-10, 3:1 target, test window from 2026-02-14.

| min_score | stop ATR | Avg train | Avg test | Profitable | Trades/coin |
|---|---|---|---|---|---|
| 5 | 2.0 | −1.0% | −7.4% | 0/10 | 92 |
| 5 | 3.0 | +0.2% | −3.0% | 2/10 | 83 |
| 6 | 2.0 | +3.1% | −1.1% | 3/10 | 34 |
| 6 | 3.0 | +2.2% | +0.3% | 7/10 | 27 |
| 7 | 2.0 | +2.8% | −4.1% | 0/10 | 8 |
| 7 | 3.0 | +1.4% | −2.7% | 1/10 | 7 |

**No.** Only one setting is marginally positive, and the pattern (more
trades → bigger losses) says the costs eat it. Daily stays the timeframe.

## Conclusions

1. The scorer has a **small, long-run positive expectancy** at low risk,
   not a dependable monthly income. Its honest description: it avoids
   crashes and takes a few percent a year out of trending stretches.
2. It is **not robust to the test window**, so any single-window number,
   including round 1's +1.2%, should be read as "about zero, maybe a bit
   positive".
3. No filter or timeframe tested so far improves it. The next ideas are
   different in kind, not more tuning of this one:
   - **Trailing stop instead of a fixed 3:1 target**, so a real trend pays
     more than 3R (the BTC +14.6% vs +275% gap is the cost of capped exits).
   - **Volatility-scaled risk**: risk 1% in calm markets, less in wild ones.
   - **Short side on futures** (demo only) to earn something in bear
     markets instead of sitting out; a different risk profile entirely.
