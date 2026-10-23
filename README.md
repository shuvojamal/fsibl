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
python -m unittest discover -s tests -t .
```

## Opportunity strategy (`--strategy opportunity`)

Full specification (rationale, assumptions, failure conditions, validation): `docs/STRATEGY.md`.

Trades only when enough independent checks line up. Eight checks, one
point each:

| # | Check | Passes when |
|---|---|---|
| 1 | `trend_up` | price above a rising 200-EMA |
| 2 | `ema_aligned` | 20-EMA above 50-EMA |
| 3 | `momentum` | MACD histogram positive and rising |
| 4 | `rsi_zone` | RSI between 40 and 80 (not oversold, not blow-off) |
| 5 | `volume` | volume above its 20-bar average |
| 6 | `volatility_ok` | ATR between 0.5% and 5% of price |
| 7 | `breakout` | close above the previous 20-bar high |
| 8 | `pullback` | price within 1 ATR of the 20-EMA |

A trade needs `--min-score` of them (default 5). The initial stop is 2×ATR
below entry, and the position is sized so that hitting it loses `--risk`
of equity (default 1%). The exit is a **trailing stop**: after each daily
close the stop is raised to the highest close since entry minus 3×ATR, and
never lowered, so a real trend can pay many times the initial risk while a
failed one costs about 1%. (`trail_atr=0` in `OppParams` restores the older
fixed 3:1 target plus EMA-cross exit.) Every log line names the checks
that passed, so you can see *why* the bot bought.

```bash
python -m tradebot backtest BTCUSDT ETHUSDT --strategy opportunity --interval 1d --candles 1500
python -m tradebot paper BTCUSDT ETHUSDT SOLUSDT --strategy opportunity --interval 1d
python -m tradebot live BTCUSDT ETHUSDT --strategy opportunity --interval 1d --dry-run
```

With `live`, the opportunity strategy sizes each buy from the **whole
account**: `--risk` (default 1%) of account equity is lost if the stop is
hit, and `--trade-usdt` only caps the notional. Set the cap generously
(e.g. `--trade-usdt 1000 --max-trade-usdt 1000` on a 5,000 USDT account)
or the risk sizing never gets room to work. On one shared account, cap the
number of simultaneous positions with `--max-open 5`; a long list of coins
is fine as long as the cap holds (`docs/research-round4-2026-10-22.md`,
`docs/research-round6-2026-10-22.md`).

**Which coins:** trade the 15 most-traded coins, re-checked each quarter,
not a hand-picked list (`docs/research-round9-2026-10-22.md`):

```bash
python -m tradebot scan --top 15                 # ranked list with today's signals
python -m tradebot scan --top 15 --symbols-only  # just the symbols, for `live`
```

Use **daily candles**. On 1h and 4h candles the strategy loses money at
every setting, mostly to fees; on daily candles it was profitable on
unseen data for BTC, ETH and SOL, with small drawdowns, at about one or two
trades a month. Full numbers in `docs/opportunity-backtest-2026-10-22.md`.
It protects capital in bad markets; it does not keep up with buy-and-hold
in good ones.

## Funding-rate carry monitor (`funding`)

```bash
python -m tradebot funding                 # 15 big coins, OKX public data, no keys
```

Shows each coin's perpetual funding over the last 7 days, annualised, and
flags any at 20% a year or more, where buying spot and shorting the
perpetual (price-neutral) would beat holding stablecoins. It only watches;
it places nothing. Round 13 found carry paid +88% in 2021 but only about 3%
a year in 2024–26 (`docs/research-round13-2026-10-23.md`).

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

## Trading a real Binance account (`live`)

Same strategy engine as `paper`, but orders go to the exchange. By default
it talks to the **Spot Testnet**, which uses fake money.

1. Get testnet keys: log in at https://testnet.binance.vision with GitHub,
   click *Generate HMAC_SHA256 Key*. The account comes pre-funded with test
   USDT.
2. Put the keys in environment variables (never in a file in this repo):

   ```bash
   export BINANCE_API_KEY=...
   export BINANCE_API_SECRET=...
   ```
3. Dry run first (connects, checks balances and symbol rules, prints what it
   *would* do, places nothing):

   ```bash
   python -m tradebot live BTCUSDT ETHUSDT --dry-run
   ```
4. Then let it trade on the testnet:

   ```bash
   python -m tradebot live BTCUSDT ETHUSDT --trade-usdt 20
   ```

Every fill is appended to `live_state/live_trades.csv` with the exchange's
order id, so you can check it against the exchange's own history. For a
one-screen status (balance, open positions with P&L and distance to stop,
realised trades, today's score for every coin):

```bash
python -m tradebot report BTCUSDT ETHUSDT SOLUSDT --exchange okx --state-dir okx_opp
python -m tradebot report BTCUSDT --exchange none --state-dir okx_opp   # no keys: positions + scores only
```

`python -m tradebot audit --state-dir demo_state --max-open 5` checks the
state for internal consistency: the trade log nets to the quantities held,
realised P&L matches the SELL rows, every stop sits below the highest price
held, and no more positions are open than the cap. The daily workflow runs
it after saving, so a broken ledger shows up as a failed run.

**Bad-data guard** (on by default, buys only): `live` skips a buy when the
exchange price is more than `--max-price-gap` (2%) away from Binance's live
price (signals come from Binance data; orders may go to OKX or a testnet),
or when the latest closed candle is older than one interval. It does not
skip a coin just because it rose since the close; research round 23 found
that costs money
(`--no-fresh-check` turns that off). Stop-loss and exit sales never wait on it.

**Emergency backstop** (`--backstop 0.20`, OKX): besides the daily-close
stop, a real conditional sell order rests on the exchange 20% below each
position's stop and is raised as the stop trails. It only fires in a crash,
or if the bot doesn't run for days. The next run books the sale (reason
`backstop`). The bot cancels it before any sale of its own. Research
round 19: checking stops at the close beats resting stop orders in crypto
(intraday wicks), and a backstop this far down costs about 0.6%/yr.

**Fill tracking:** every buy and sell is logged to `fills.csv` with the
price the decision used, the real fill and the fee. `report` and the
dashboard's Bot tab show average slippage per side against the backtest's
assumption of 0.05% slippage plus a 0.10% fee.

**Live vs backtest:** `python -m tradebot shadow <symbols> --state-dir demo_state`
replays the backtest over the days the bot has traded (same coins, capital,
slots and rules) and lists the trades both took, the trades only one took,
and the average entry-price gap. Coins the exchange doesn't list are left
out. The daily jobs write it to `shadow.txt`, and the app shows it on the
Bot tab. Over the evaluation period it's the main evidence for whether live
trading matches the research.

**Risk guard** (on by default, between the strategy and the exchange):

| Flag | Default | What it does |
|---|---|---|
| `--trade-usdt` | 20 | USDT spent per buy |
| `--max-trade-usdt` | 50 | refuses any single buy above this |
| `--max-daily-loss` | 20 | stops opening trades after losing this much in a day (UTC) |
| `--kill-file` | `STOP` | create this file and the bot places no more orders |

On restart it reads the account: coins it finds on the exchange are adopted
as open positions, so a crash or reboot doesn't leave anything untracked.

**OKX demo trading** works the same way with `--exchange okx`. OKX's demo
is a real exchange-run simulated account with its own order matching and
trade history. Create a key in demo mode (Read + Trade, Spot, no IP
restriction) and set `OKX_API_KEY`, `OKX_API_SECRET`, `OKX_PASSPHRASE`:

```bash
python -m tradebot live BTCUSDT ETHUSDT --exchange okx --dry-run
python -m tradebot live BTCUSDT ETHUSDT --exchange okx --trade-usdt 50
```

**Running it every day without a computer on:** `.github/workflows/demo-bot.yml`
runs the opportunity bot once a day at 00:07 UTC on GitHub's servers
(`live --once`), trading the top 15 coins by volume plus anything it still
holds, and commits its state and a `report.txt` to `demo_state/`. It is off
until you add the three OKX demo secrets and set the repository variable
`TRADEBOT_ENABLED=true` (Settings → Secrets and variables → Actions). Because
it checks once a day, a stop is acted on at the next daily run, not the
moment it is touched; expect fills somewhat worse than the backtest's.

## Dashboard app (phone or browser)

`dashboard/index.html` shows the bot live: equity and P&L (open positions
priced every 15 s), all trades, today's signals, recent runs and the log,
with **Pause / Resume** (no new trades; stops keep running) and **Run now**.
From the app you can also **sell a position (or all of them) now** at market,
not bought back for the re-buy wait you choose (default 7 days; the freed
slot can take one of today's other buy signals in the same run); **stop or
start the daily schedule**; **edit the
strategy settings** (capital, risk per trade, max positions, backstop, daily
loss limit, circuit breaker, gold, re-buy wait, profit alert); and **reset a tripped circuit breaker**.
The app writes small request files (`settings.json`, `CLOSE`, `RESET_HALT`,
`PAUSED`) into `demo_state/`; the workflow validates and clamps them with
`python -m tradebot controls` before they reach the bot (risk is capped at
2%, positions at 10).
It talks only to GitHub (with a fine-grained token kept on your device) and
to Binance for prices. `.github/workflows/android.yml` wraps it in an Android
app and publishes `TradebotDesk.apk` as the release **dashboard-latest**.

**Going live** needs two flags, `--live --i-accept-the-risk`, and live-only
API keys. On the VPS this is packaged as an opt-in third account (see
`deploy/vps/README.md`, "Real-money account"): separate keys file and
records, off by default, a no-orders test first, and live only after the
owner types `I ACCEPT THE RISK` in the app. On Binance, create a key with *Enable Spot Trading* only: no
withdrawals, no margin, no futures, and restrict it to your IP. Start with
`--trade-usdt` set to an amount you are fine losing entirely.

Do not go live because the testnet "looks good". Run the testnet for at least
a few weeks, compare `live_trades.csv` with the backtest for the same dates,
and only go live if the two agree *and* the strategy is beating buy-and-hold.
As of the scan above, it is not.

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
