# Strategy specification

The one strategy this repo recommends running, stated so it can be checked:
what it does, why it should work, what it assumes, when it fails, how it is
built, and how it was validated. Evidence is in `docs/research-round*.md`
and reproducible from `research/`.

## 1. What it does

Long-only spot trend following on daily candles.

| Part | Rule |
|---|---|
| Universe | The 15 Binance/OKX spot coins with the highest trailing-90-day dollar volume, re-ranked at each run; coins the exchange does not list are skipped |
| Entry | At least 5 of 8 checks on the latest closed daily candle: price above a rising 200-EMA; 20-EMA above 50-EMA; MACD histogram positive and rising; RSI(14) between 40 and 80; volume above its 20-day average; ATR between 0.5% and 5% of price; close above the prior 20-day high; close within 1 ATR of the 20-EMA |
| Initial stop | Entry − 2 × ATR(14) |
| Exit | Trailing stop: highest close since entry − 3 × ATR, raised after each daily close, never lowered. No profit target |
| Size | Risk 1% of account equity per trade: quantity = 1% of equity ÷ (entry − stop) |
| Portfolio | At most 5 positions; when more coins signal than slots are free, highest score first |
| When not to trade | Fewer than 5 checks agree (most days for most coins); all 5 slots full; coin outside the top 15; daily loss limit hit; circuit breaker tripped |

## 2. Rationale

Trend following is one of the most persistent documented effects across
asset classes (time-series momentum: past 6–12 month returns predict the
sign of future returns). The usual explanation is behavioural (slow
reaction to information, then herding) plus risk transfer: trend followers
are paid for taking the other side of hedgers and for sitting through
long losing streaks that most investors will not tolerate.

Crypto is a strong case: it trends hard in both directions, is dominated
by retail flows, and has frequent multi-month moves of 100%+. The rules
here do not predict direction. They wait for evidence that a trend exists,
cut losers quickly at about 1R, and let the rare large trend run for 10R+.
Expectancy comes from the asymmetry, not from accuracy: 34% winners with
an average win 3.6 times the average loss.

## 3. Assumptions

- Large crypto trends will keep occurring (several a year across the top 15).
- Spot liquidity in the top-15 coins stays deep enough for market orders of
  this size with costs near 0.1% fee + 0.05% slippage per side.
- The exchange is solvent and reachable once a day.
- The person running it will not switch it off during a −20% to −30%
  drawdown, because that is exactly when the next large trend is most likely
  to be missed.

## 4. Failure conditions (when it loses money)

- **Long sideways or falling markets**: many small stop-outs, few trends.
  2018 (−14%), 2022 (−28%), 2025 (−11%).
- **Strong steady bull markets**: it makes money but far less than simply
  holding (2020: +62% vs BTC +302%). Not a loss, but it disappoints.
- **Gap crashes**: a coin falls through its stop in one day; the loss is
  taken at the close, beyond 1R (13 of 487 trades were worse than −1.5R).
- **Exchange failure or delisting**: outside the strategy's control. Keep
  only the capital you trade on the exchange.
- **Edge decay**: if many traders run the same rules, trends get front-run.
  Monitored by comparing live results with the backtest (section 6).

## 5. Implementation

- Code: `tradebot/opportunity.py` (rules), `tradebot/live.py` (execution
  and risk), `tradebot/okx_client.py` (exchange), `tradebot/scan.py` (universe).
- Schedule: `.github/workflows/demo-bot.yml` runs once a day at 00:07 UTC,
  after the daily candle closes, and commits state and a report to
  `demo_state/`.
- Hard limits, enforced outside the strategy and not overridable by it:
  per-trade size cap, daily loss limit (3% of capital), maximum positions,
  drawdown circuit breaker (35% below peak, latches until reset), a `STOP`
  file that blocks all orders, demo by default, real money only with
  `--live --i-accept-the-risk`.
- Keys: environment secrets only, never in the repo; trade permission only,
  no withdrawals.
- Fault handling: a coin the exchange does not list is skipped; network
  errors skip that coin for the run; state is saved atomically after each run;
  a crash turns the GitHub run red.

## 6. Validation

| Test | Result |
|---|---|
| Walk-forward (tune on old data, judge on new) | Rounds 1–2: per-coin tuning overfits; one universal setting is used |
| Out-of-sample coins | Round 6: ten coins never used before did as well or better |
| No-hindsight universe | Round 9: volume ranking replaced the hand-picked list (+188% → +137% on 2022–26) |
| Ablation | Round 7: each of the 8 checks earns its place |
| Costs | Rounds 7 and 12: survives 3× the assumed costs |
| Stress, 2017–2026 | Round 12: +22.7%/yr, max drawdown −31%, Sharpe 0.97, through three bear phases |
| Half-split check of new ideas | Round 12b: ADX filter rejected (helped one half only) |
| Monte Carlo | Round 12: 10% chance of a losing first year; 1-in-100 drawdown about −31% |
| Ideas tested and rejected | Hourly/4h timeframes, cross-exchange arbitrage, breakout-only, RSI(2) dip-buying, BTC regime filter, ADX filter, volatility-scaled risk, pyramiding, drawdown throttle, time exits, re-entry cooldowns, partial profit-taking |

**Live validation (in progress):** OKX demo via the daily GitHub job since
2026-10-22. Go live only if, after at least 3 months, the demo's
expectancy per trade is positive and its drawdown is within the backtest
range. Expect live results below the backtest.

## 7. Expectation, honestly

About +15–25% a year over a full cycle, with drawdowns of 20–30% along the
way, roughly one losing year in three, and about two in three trades losing.
These are backtest estimates, not promises; live trading usually does worse.
