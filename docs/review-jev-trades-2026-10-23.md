# Review: zadescoxp/Jev-Trades (2026-10-23)

https://github.com/zadescoxp/Jev-Trades (Apache-2.0). Script:
`research/scripts/review_jev.py`. Output: `research/results/review_jev.out`.

## What it is

- **Dashboard:** Next.js, with a live chart, indicator panels, a manual
  trade desk, and an agent decision log.
- **Data:** Python feed of Yahoo Finance prices for 7 coins.
- **Brain:** "Jev", which sends indicator states on 1m–4h timeframes to a
  paid external AI API (TypeSafe) on every tick. The API returns structured
  judgments (buy/hold/sell, conviction, stop-loss and take-profit width).
- **Trading:** SL/TP from ATR multiples; paper trading by default. Optional
  Bybit live trading through ccxt, gated by `LIVE_ARMED=1`.
- **Testing:** no backtest, no walk-forward, no cost model.

## What its own saved results show

The repo includes its paper-trading database: 2,596 agent decisions over
36.6 hours, all on 1-minute ETH. Of 119 "buy" calls, 6 were executed.

| | Result on 100,000 paper capital |
|---|---|
| 6 round trips, 3 wins | −79 USD with the repo's zero fees |
| Same trades, 0.1% fee per side | **−379 USD** |

Each trade moved 0.2–0.5%. A real round trip costs about 0.2% in fees alone
(more with spread), which eats most of every winner and adds to every loser.
That matches what this repo found in rounds 0a/0b and 5: on 1h and 4h
candles the opportunity strategy lost money at every setting, mostly to
fees. 1-minute bars are worse.

## Verdict

- **Strategy:** nothing to adopt. Six trades is far too few to judge
  anything, and the setup is structurally fee-bound: 1-minute holds, no
  backtest, and an outside AI that can change behaviour without notice.
  There's also no evidence the AI's judgments beat simple rules. A
  `low_reliability_setup` of 0.82 on its own decisions suggests even it
  isn't sure.
- **Good ideas worth noting:** paper mode is the default; live trading is
  behind an explicit arm switch; the AI is separated from execution ("policy
  layer" vs "execution layer"), which matches our risk guard; and its key
  table says no withdraw permission and IP whitelist on.
- **Possible use:** its chart UI could inspire a price chart with entry/stop
  lines in our Tradebot app. Optional.
