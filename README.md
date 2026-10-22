# tradebot

A small crypto trading bot for Binance spot markets. It uses only Python's
standard library (Python 3.9+) and **never places real orders**. It can:

- **backtest**: replay the strategy over past candles, with fees (0.1% per side) and slippage
- **optimize**: tune the settings on older data, then test them on newer data they never saw
- **paper**: trade live prices with fake money, saving positions to `paper_state/`
- **arb**: scan nine exchanges for cross-exchange price gaps and paper-trade them (see below)

Price data comes from Binance's public market-data API
(`data-api.binance.vision`). No API key or account is needed.

## Strategy

Trend following, long only:
- **Buy** when the fast EMA crosses above the slow EMA and RSI is below `--rsi-max`.
- **Sell** when the fast EMA crosses back below the slow EMA, or on the stop-loss or take-profit.

The bot decides when a candle closes and fills at the next candle's open, so
the backtest never uses future prices.

## Usage

```bash
python -m tradebot backtest BTCUSDT ETHUSDT SOLUSDT --interval 1h --candles 5000
python -m tradebot optimize BTCUSDT --interval 1h
python -m tradebot paper BTCUSDT ETHUSDT --capital 1000 --fast 12 --slow 26
python -m unittest discover -s tests
```

## Cross-exchange arbitrage (`arb`)

```bash
python -m tradebot arb BTCUSDT ETHUSDT SOLUSDT --poll 3            # scan until Ctrl+C
python -m tradebot arb BTCUSDT --exchanges binance okx mexc --seconds 600
```

Every few seconds the scanner fetches the best bid and ask for each coin on
Binance, Kraken, Coinbase, OKX, KuCoin, Gate, Bitget, MEXC and HTX (public
endpoints, no keys). For every pair of exchanges it computes

    gross gap = sell-side bid / buy-side ask − 1
    net gap   = gross gap − taker fee on each side

and prints the widest one. A gap whose net is positive is paper-traded, sized
to the smaller of the two top-of-book quantities. Every scan is appended to
`arb_logs/scans.csv`, every paper trade to `arb_logs/arb_trades.csv`.

Paper mode assumes you already hold USDT *and* the coin on every exchange,
because moving coins between exchanges takes minutes and costs a withdrawal
fee, and the gap is gone long before the transfer lands.

**What a 5-minute scan over 10 coins found:** see `docs/arb-scan-2026-10-22.md`.

## Results so far (1h candles, Mar–Oct 2026)

| | Default settings | Tuned, on unseen data |
|---|---|---|
| BTC | −15.5% (buy & hold +23.0%) | −9.0% (buy & hold +10.6%) |
| ETH | −14.2% (buy & hold +20.4%) | −19.5% (buy & hold +2.4%) |
| SOL | −2.0% (buy & hold +26.2%) | −8.7% (buy & hold +18.1%) |

The tuned settings made +13% to +21% on the data they were tuned on, then lost
money on newer data. This is called **overfitting**, and it is why screenshots
of backtest profits mean very little.

## On "accuracy"

Win rate alone doesn't tell you whether a strategy makes money:
- At a 25% win rate you still profit if the average win is more than 3× the average loss, after fees.
- At a 70% win rate you still lose if the occasional loss wipes out many small wins.

Use **profit factor** (gross gains ÷ gross losses, after fees) and compare
against **buy & hold**. A strategy that can't beat simply holding the coin
isn't worth running.

## Before using real money

- Paper trade for weeks, and check the results against the backtest.
- Check the law where you live. Bangladesh Bank, for example, has warned that
  crypto trading is not authorised in Bangladesh.
- Only risk money you can afford to lose.
