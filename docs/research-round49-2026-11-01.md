# Research round 49: a coin collapses while held; what a backstop saves (scheduled daily run)

**Question.** The backtests can't contain a LUNA- or FTT-style collapse
(dead coins are missing from the data), and the daily-close stop can't react
to a crash between closes. OKX has a resting backstop order 20% below each
stop; the Binance accounts don't. How much would one save?

**Stress test.** Every position the live rules opened (round 12's simulator,
growth and steady, 6 of 8 checks, top 15, six close times, 2018-26), with
that coin crashing 90% overnight right after entry. No backstop: sold at
−90%. Backstop 20% below the stop: fills on the way down with 10% extra
slippage. Loss = position share × loss on the coin. Pass bar (set first):
on growth, the 90th-percentile loss above 5% of the account without a
backstop, and the backstop at least halves it.

**Result** (`research/results/research49.out`), loss as a share of the account:

| | no backstop: median / 90th / worst | with backstop: median / 90th / worst |
|---|---|---|
| growth (1% risk) | 8.3% / 14.4% / 42.0% | 3.3% / 5.2% / 13.8% |
| steady (0.5% risk) | 4.4% / 7.3% / 21.0% | 1.7% / 2.6% / 6.9% |

(A normal stop-out is planned to cost 1% or 0.5%.) **Passes.**

**Meaning.** A single coin collapsing is a rare but real event in crypto
(LUNA, FTT). Without a resting order, one such event could cost a growth
account 8-14% typically and up to 42% in a large calm-coin position like
the testnet's TRX; the backstop cuts that to roughly a third. **Recommendation:
add Binance backstop orders (resting stop-loss orders 20% below each stop,
as on OKX) before the real account trades.** This is real-money order code
and needs the owner's go-ahead; no change made.
