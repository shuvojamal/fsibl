# Strategy research, round 5 (2026-10-22): the window tests, done right

## The mistake

Rounds 2 and 3 cut each test window out of the price history and ran the
strategy on that slice alone. The strategy's slowest indicator is a
200-day EMA, so every window was blind for its first ~200 days: no entries
possible, whatever the market did. Two consequences:

- the per-window returns in rounds 2 and 3 were understated, and
- the claim "no entries on any coin since 2026-05-25" was false. The
  window starting 2026-05-25 was simply still warming up. The demo bot
  proved it by entering BTC, ETH and SOL on its very first check.

The full-history results (rounds 1, 3, 4) and the portfolio simulation
(round 4, which warmed its indicators properly) are unaffected. The
comparisons *between* variants within a window were still fair, since
every variant had the same handicap. The backtester now warms indicators on
the whole series and starts trading at the window's first candle
(`run_opportunity(..., start=i)`).

## Corrected per-coin window results

10 coins, daily candles, 1% risk per trade, fees and slippage as before.
Cells: average return across coins / coins profitable / total trades.

| Exit variant | from 2024-10 | from 2025-03 | from 2025-07 | from 2025-12 | from 2026-05 |
|---|---|---|---|---|---|
| Fixed 3:1 target + EMA exit | +3.4% 7/10 292t | −0.5% 5/10 217t | −0.7% 4/10 169t | +1.0% 7/10 122t | +2.2% 9/10 59t |
| Trailing stop 2×ATR | +5.8% 8/10 251t | −0.6% 5/10 174t | −0.4% 4/10 127t | +1.5% 7/10 74t | +2.5% 9/10 40t |
| **Trailing stop 3×ATR (default)** | +5.6% 8/10 175t | −0.3% 5/10 125t | −0.1% 5/10 94t | +1.9% 8/10 53t | +2.5% 7/10 32t |
| Trailing stop 4×ATR | +7.4% 9/10 134t | −0.4% 4/10 99t | −0.4% 6/10 74t | +1.7% 8/10 40t | +2.9% 9/10 21t |
| Buy & hold, average of the 10 coins | −4.2% | −37.8% | −50.4% | −19.0% | +7.2% |

Reading: with the windows done properly the picture is steadier than
round 2 suggested. No window is a disaster; the two bear-market windows
(2025-03, 2025-07) come out flat (−0.1% to −0.7%) while holding the coins
lost 38–50%, and the two calmer windows earn +2% to +6%. The trailing
exits are better than the fixed target in four windows out of five and
trade far less. 3×ATR and 4×ATR are close; 3×ATR stays the default for its
smaller drawdowns in round 3.

Most recent window (from 2026-05-25), trailing 3×ATR, per coin:

| Coin | Return | Trades | Win | Max DD | Buy & hold |
|---|---|---|---|---|---|
| BTC | +6.1% | 3 | 67% | −2.5% | +8.9% |
| ETH | +3.6% | 3 | 33% | −1.9% | +17.6% |
| SOL | +5.3% | 3 | 67% | −3.6% | +25.2% |
| XRP | −0.3% | 5 | 20% | −4.3% | +0.9% |
| DOGE | −0.2% | 3 | 33% | −3.6% | −20.0% |
| ADA | −1.7% | 3 | 33% | −3.9% | −7.3% |
| LINK | +5.2% | 3 | 67% | −3.2% | +32.3% |
| AVAX | +3.5% | 2 | 50% | −2.9% | +4.6% |
| DOT | +0.5% | 2 | 50% | −3.2% | −8.4% |
| LTC | +3.1% | 5 | 60% | −3.3% | +16.5% |

## What the strategy sees right now

On daily candles the market has been in an uptrend since late September:
the default setting would have entered BTC on most days since 2026-09-22,
ETH and SOL on many of them, and LINK, LTC, XRP, ADA on some. The
short-term (hourly) chart is falling at the same time, which is why the
hourly EMA bot sits out while the daily scorer is long BTC, ETH and SOL on
the demo account. Both are behaving as designed; they look at different
timescales.

## Standing after five rounds

- Daily opportunity scorer, 5 of 8 checks, 2×ATR initial stop, 3×ATR
  trailing stop, 1% of account equity per trade, about five coins.
- Full history: +12.4% per coin-pot over four years; in a shared account
  with five positions, about +20% a year with −30% drawdowns (round 4).
- Bear-market windows: roughly flat. Calm or rising windows: a few percent
  per coin-pot per quarter.
- Still unproven in real time. The demo record is the test that matters.
