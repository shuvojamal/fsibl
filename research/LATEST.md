# Latest research report

_Updated 2026-10-30 05:50 UTC by Claude (daily scheduled run)_

**OKX demo: still blocked by GitHub billing (fifth day).** Runs on Oct 29
and 30 refused again. Fix under GitHub Settings → Billing & plans, then
press Run now. BNB and PEPE stay open with OKX backstop orders.

**VPS testnet:** daily run done at 00:10 UTC, audit passed.
- BNB hit its trailing stop and was sold at 695.99: −52.45 USDT.
- TRX is up 8.5% (+210.81 USDT); its stop was raised to 0.3352.
- BTC is −4.7%, close to its stop (77,039).
Open P&L +167.37 USDT; realised −52.45.

**Real account:** off.

**Fixed:** the live-vs-backtest check showed each new trade as "only live"
for its first day. It now includes orders from the latest close.

**Tested today (round 47): a minimum stop distance (3% or 5%)** for very
calm coins like TRX, which get very large positions. It made practically
no difference. No change.

**Recommendation:** fix GitHub billing; before real money, add a Binance
backstop order (the one protection still missing).
