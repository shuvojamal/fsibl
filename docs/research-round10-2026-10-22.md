# Strategy research, round 10 (2026-10-22): partial profit-taking

Universe: top 15 by trailing-90-day volume, re-ranked quarterly (round 9).
Shared account, max 5 open, 1% risk. Variant: sell part of the position
once price reaches k × the initial risk (R), optionally move the stop on
the rest to break-even, and trail the remainder as usual.
Cells: return / max drawdown / win rate / profit factor.

| Exit | Full 4y | from 2024-10 | from 2025-07 | from 2025-12 |
|---|---|---|---|---|
| **Trail only (current)** | **+137% / −28% / 35% / 1.74** | **+59% / −28% / 36% / 1.57** | **+37% / −17% / 36% / 1.85** | **+25% / −17% / 32% / 1.83** |
| Sell 33% at 1.5R, stop to BE | +85% / −24% / 37% / 1.53 | +39% / −24% / 38% / 1.40 | +26% / −17% / 37% / 1.60 | +14% / −17% / 32% / 1.48 |
| Sell 33% at 2R, stop to BE | +89% / −25% / 36% / 1.55 | +41% / −25% / 37% / 1.41 | +27% / −17% / 36% / 1.62 | +15% / −17% / 32% / 1.51 |
| Sell 33% at 3R, stop to BE | +92% / −26% / 35% / 1.56 | +43% / −26% / 36% / 1.43 | +28% / −17% / 36% / 1.65 | +17% / −17% / 32% / 1.57 |
| Sell 50% at 1.5R, stop to BE | +60% / −23% / 37% / 1.40 | +28% / −23% / 38% / 1.30 | +19% / −17% / 37% / 1.45 | +9% / −17% / 32% / 1.29 |
| Sell 50% at 2R, stop to BE | +65% / −24% / 36% / 1.43 | +31% / −24% / 37% / 1.32 | +22% / −18% / 36% / 1.50 | +11% / −17% / 32% / 1.35 |
| Sell 50% at 3R, stop to BE | +70% / −25% / 35% / 1.46 | +36% / −25% / 36% / 1.36 | +24% / −17% / 36% / 1.55 | +13% / −17% / 32% / 1.44 |
| Sell 50% at 2R, stop not moved | +65% / −24% / 36% / 1.43 | +31% / −24% / 37% / 1.32 | +22% / −18% / 36% / 1.50 | +11% / −17% / 32% / 1.35 |

## Result: not adopted

Every profit-taking variant is worse in every window, and the more is
taken and the earlier, the worse it gets. It barely raises the win rate
(35% → 37%) and shaves only a few points off the drawdown, while cutting
the return by a third to a half.

The reason is the same arithmetic as round 3: this strategy's profit comes
from a handful of trades that run for many multiples of their risk.
Selling half at 2R halves exactly those trades and does almost nothing for
the many small losers. "Lock in some profit" feels safer and costs more.

The trailing stop alone stays the exit.

## Ten rounds in one paragraph

Daily candles; enter when 5 of 8 classic checks agree (RSI zone 40–80);
initial stop 2×ATR; trailing stop 3×ATR, no profit target; risk 1% of the
account per trade; at most 5 positions; trade only the 15 most-traded
coins, re-ranked quarterly. Realistic backtest expectation: about +24% a
year with drawdowns up to about −28%, roughly two-thirds of trades losing,
positive in every test window including two bear markets, surviving triple
costs. Ideas tested and rejected: hourly and 4h timeframes, cross-exchange
arbitrage, breakout-only and dip-buying systems, BTC regime filter,
volatility-scaled risk, pyramiding, drawdown throttle, time exits,
re-entry cooldowns, partial profit-taking.
