# Latest research report

_Updated 2026-10-24 05:45 UTC by Claude (daily scheduled run)_

**OKX demo:** running normally. Holds BNB (bought 737.90) and PEPE (bought
0.00000458), each risking about 25 USDT (0.5% of 5,000). Daily run came in
at 04:26 UTC. Realised so far +76.61 USDT. The live-vs-backtest check shows
4 "only live" buys: the backtest never saw your manual sale on Oct 23 (so
it still "held" BNB/PEPE) and two Oct 22 buys used 5 checks before the
setting moved to 6. Explained, not a fault.

**VPS testnet:** silent since Oct 23 18:02 UTC (holds BTC from 81,804).
Most likely stuck in a git sync conflict; fixed in the code, but the VPS
needs the one-time repair command once (see the chat). Not run in 26 h.

**Real account:** off. Note: one run on Oct 23 17:55 UTC was in live mode
with 0 USDT, so it placed no orders. It is off now.

**Tested today (round 34): the stop distance at entry**, 1.5 to 4 × ATR.
Return per unit of risk is the same at every distance (Sharpe ~1.0);
a tighter stop only means bigger positions, like turning up the risk
setting. 1.5 × ATR earned more but had deeper drops and failed the bar.

**What it means:** keep 2 × ATR. To earn more, use the risk setting
(steady 0.5% vs growth 1%), which does the same thing openly.
