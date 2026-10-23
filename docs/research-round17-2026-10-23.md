# Research round 17: gold (PAXG) with the live rules (2026-10-23)

**Question.** Could the bot trade gold? PAXG is a token backed by one troy
ounce of gold (Paxos), traded against USDT on Binance and OKX, so no new
broker is needed. Does it help?

Script: `research/scripts/research17.py`. Output: `research/results/research17.out`.
Data: PAXG daily candles (Binance public API, cached in `research/data/paxg.pkl`),
2020-08 to 2026-10, scored from 2021-03 after the 200-day warm-up. Same
simulator, costs and caveats as round 12. One bug was caught and fixed
before reporting: the freshly downloaded PAXG data had one more day than the
cached crypto data, and on that day the simulator valued every crypto
position at zero.

## Results

**Liquidity:** about 13M USD a day on Binance; OKX lists PAXG-USDT with a
spread of about 0.01%. Plenty for orders of about 1,000 USD. But it is far
below the 15th coin's roughly 50M a day, so it would never enter the top-15
list by itself. It has to be added as a fixed extra symbol.

**Gold behaves differently:** daily correlation +0.15 with BTC and +0.10
with the bot. On BTC's 20 worst days (average −10.7%), PAXG averaged
−0.6%.

**The rules on PAXG alone:** 60 trades, 38% wins, profit factor 1.64,
+4.4%/yr with a max drawdown of −9.3%. Buy and hold returned +16.7%/yr
(gold rose 138% in this window). At 1% risk per trade on a low-volatility
asset the strategy is rarely heavily invested, so on its own it's a weak
way to own gold.

**PAXG added to the live book as a 16th always-eligible symbol** (same 5
slots, 1% risk):

| | Return/yr | Max drawdown | Sharpe |
|---|---|---|---|
| Top 15 only (current) | +22.7% | −31.4% | 0.93 |
| **Top 15 + PAXG** | **+24.6%** | **−27.4%** | **1.05** |

Its 39 trades inside the book made +27.3R with 49% wins. Year by year it's
mixed:

| | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|
| Without PAXG | +36.7% | −27.6% | +76.8% | +33.4% | −10.8% | +43.0% |
| With PAXG | +36.0% | −22.5% | +62.0% | +45.6% | +6.0% | +23.7% |

It helped in the bad crypto years (2022, 2025) and cost money in the strong
ones (2023, 2026), when a gold position sometimes took a slot a crypto
winner would have used.

## What it means

- The gain is real but modest. Sharpe rises 0.12, close to the spread
  between variants measured in round 16 (sd 0.13), so this alone doesn't
  prove it.
- The case for it isn't the backtest number. It's the reason behind it:
  gold is barely correlated with crypto, so it tends to work when crypto
  doesn't, and it softened both bad crypto years. That's diversification,
  not tuning.
- Risk: gold had an unusually strong run in 2024–26. In a long sideways or
  falling gold market, its trades would mostly be small stop-outs (about
  −1R each).

## Recommendation

Add PAXG-USDT to the demo bot as a fixed extra symbol. It's one word in
the workflow's symbol list, with no rule changes, and it uses the same 5
slots and 1% risk. Then compare its demo record with this test. Waiting on
the owner's yes before changing the live demo setup.
