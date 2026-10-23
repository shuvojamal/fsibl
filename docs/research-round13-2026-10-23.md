# Research round 13: funding-rate carry (2026-10-23)

**Question.** Is there a profit source that doesn't depend on the price
moving? Perpetual futures pay a funding rate every 8 hours. When it's
positive, the shorts get paid. If you buy a coin on spot and short the same
amount on the perpetual, price moves cancel out and you collect the
payments. This is called "cash and carry".

Script: `research/scripts/research13.py`. Output: `research/results/research13.out`.
Data: Binance's public futures data dumps (monthly funding files and perp
daily klines, 20 coins, 2020-01 to 2026-09), cached in `research/data/funding.pkl`.

## Rules tested

- Each day, compute each coin's trailing 7-day funding, annualised.
- Open a hedge when it is above ENTER; close it when it drops below EXIT.
- At most 5 hedges at once, highest funding first, equal capital slots.
- Perp margin is 1x by default, so a slot of capital C holds C/2 of spot and
  a C/2 short.
- Daily P&L is funding received plus the basis change (spot move minus perp
  move). Costs are 0.25% per side across both legs, so 0.50% per round trip.
- ENTER/EXIT were tuned on 2020-03 to 2023-12 and tested on 2024-01 onward.

## Results

| | CAGR | Max drawdown | Trades |
|---|---|---|---|
| Training 2020–23, best (enter 10%, exit 3%) | +24.3% | 0.9% | 95 |
| **Unseen 2024–26, same rule** | **+3.1%** | 0.5% | 40 |
| Unseen, always hedged BTC+ETH | +5.2% | 0.3% | 2 |
| Unseen, 3x perp margin | +4.6% | 0.8% | 40 |
| Last 90 days | −1.4% | 0.4% | 12 |

By year: 2020 +16%, 2021 **+88%**, 2022 +1%, 2023 +5%, 2024 +13%, 2025 +1%, 2026 −0.4%.

Every coin's average funding over the last 90 days was below 8% a year.
TRX and ATOM were negative.

## What it means

1. **This edge is real, but it only shows up in euphoric markets.** It paid
   hugely in 2021, when leveraged longs were paying 30–100% a year to stay
   in. In quiet markets it pays less than a stablecoin deposit (about 4–5%),
   and switching costs eat the rest.
2. **Tuning didn't carry over.** Every setting looked brilliant on 2020–23
   and earned about 2–3% a year afterwards. The training period was mostly
   about 2021.
3. **Drawdowns in this test are tiny, but the real risks aren't in the
   data.** They are: the exchange failing (all legs sit on one venue; FTX
   2022); the short being liquidated in an intraday squeeze when margin is
   above 1x (daily data can't see this); funding turning negative for long
   stretches; and stablecoin risk.
4. **It doesn't compete with the trend bot.** It's the other way round: carry
   pays most in exactly the euphoric phases where the trend bot is fully
   invested anyway.

## Decision

- Don't trade carry now. At under 8% gross funding it doesn't beat holding
  stablecoins.
- Added a monitor instead: `python -m tradebot funding` reads OKX's public
  funding history (no keys) and flags any coin whose 7-day funding is at
  least 20% a year. At 1x margin that's about 10% a year on the whole
  capital. Today's scan flagged nothing (top was DOGE at +7%):
  `research/results/research13-funding-now.out`.
- If a flag shows up and stays for weeks, the next step is an OKX demo test
  of the two-leg trade (spot buy plus perp short), not real money.
