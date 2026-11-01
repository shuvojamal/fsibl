# Latest research report

_Updated 2026-11-01 05:50 UTC by Claude (daily scheduled run)_

**OKX demo: still blocked by GitHub billing (seventh day).** Fix under
GitHub Settings → Billing & plans, then press Run now. BNB and PEPE stay
open with OKX backstop orders.

**VPS testnet:** daily run done at 00:10 UTC, audit passed. No positions
and no new signals today. Realised so far −156.59 USDT (3 trades). Live
still matches the backtest.

**Real account:** off.

**Tested today (round 49): what if a coin collapses while the bot holds
it** (like LUNA or FTX's token, −90% overnight)? Without a resting backstop
order, a growth account would typically lose about 8% (1 in 10 cases 14%,
worst 42% in a big calm-coin position). With a backstop 20% below the stop
(OKX has one) that drops to about 3% (5%, worst 14%).

**Recommendation:** add backstop orders to the Binance accounts before the
real account trades. It's the one missing protection; it needs your go-ahead.
