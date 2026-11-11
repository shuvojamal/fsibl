# Latest research report

_Updated 2026-11-11 05:50 UTC by Claude (daily scheduled run)_

**OKX demo: still waiting for the VPS setup** (no run since Nov 4).

**VPS testnet:** daily run at 00:10 UTC. ZEC hit its stop: −53.18 USDT
(sold at 1042.95, stop 1062.46). Holds UNI (−7.0%). Realised so far
−258.79 USDT (6 trades).

**Bug fixed:** a rounding error made the bot sell 0.205 of its 0.206 ZEC,
leaving 0.001 ZEC (about 1 USDT) behind, and the audit flagged it. Fixed
for Binance and OKX (it can no longer drop a step), and the audit now
accepts unsellable leftovers under 5 USDT. Both have tests.

**Real account:** off.

**Tested today (round 59): how far past the stop do losing trades sell?**
Usually less than planned (typical loser −0.85× the planned risk), but
about 1 in 17 losers costs 1.5× or more, because stops act at the daily
close and the price can gap before the next sale. A known cost; no change.

**To do (you):** run the VPS setup command for the OKX demo.
