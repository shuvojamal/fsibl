# Research round 45: how big single positions get (scheduled daily run)

**Prompt.** On 2026-10-28 the VPS testnet bought 7,475.6 TRX at 0.3319,
about 2,481 USDT, half of its 5,000 capital: TRX moves so little that its
2 × ATR stop was only 2.1% away, so 1% risk bought a large position.
**Correction to round 43:** it said positions are "about 5-17% of the
account". That is the typical range (median 9%, 90% of trades below 16% on
the growth set-up), not the maximum; low-volatility coins can reach ~50%.

**Method.** Round 12's simulator, growth and steady set-ups, 6 of 8 checks,
top 15, round 21's 12 cells; position share of equity at entry and each
trade's result as a share of equity. Pass bar for recommending a 25% cap
(set first): positions above 25% are at least 5% of growth trades AND one
of them lost more than 2% of equity. Output: `research/results/research45.out`.

**Result.**
- Growth: median position 9%, 90th percentile 16%, largest 47%. Above 25%:
  40 of 2,508 trades (1.6%), **all TRX**. Their worst loss was −1.43% of
  equity (normal-sized positions: −2.75%), none lost more than 2× the planned
  risk, and on average they made +1.23% of equity per trade.
- Steady: largest position 23%; none above 25%.

**Verdict: fails; no cap.** Big positions are rare, limited to TRX, and were
not where the losses came from.

**Remaining risk worth knowing:** a 50% position is exposed to a sudden gap
(an exchange or stablecoin event) that a backtest of a calm coin can't show.
On OKX the emergency backstop order limits that; **the Binance accounts
(VPS testnet, and the real account later) have no backstop yet**, because the
Binance client has no resting stop orders. Adding Binance stop-loss orders
before real money would close that gap. That's a recommendation, not a change.
