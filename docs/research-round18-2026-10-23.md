# Research round 18: the live rules on XM-style CFD markets (2026-10-23)

**Question.** The owner asked about running the bot on an XM demo account
(MetaTrader 5, CFDs on gold, indices, oil and forex). Before building
anything: do the bot's rules work on those markets once CFD costs are
included? The main extra cost is the overnight financing fee ("swap")
charged for every night a position is open; this strategy holds trades for
weeks.

Script: `research/scripts/research18.py`. Output: `research/results/research18.out`.
Data: Yahoo Finance daily prices 2000–2026 (cached in `research/data/xm_markets.pkl`)
for gold, silver, oil, S&P 500, Nasdaq 100, DAX, Nikkei, EUR/USD, GBP/USD,
USD/JPY and AUD/USD. Futures and index levels stand in for CFD prices.
Scored from 2010.

**Setup:** exactly the live rules, not re-tuned (5 of 8 checks, 2×ATR
stop, 3×ATR trailing stop, 1% risk, max 5 open). Swap swept at 0, 3 and 6%
a year on the open position. Costs tested two ways: crypto-level (0.15% per
side) and typical CFD (0.04% per side).

Two simulator fixes were needed. Markets close on different holidays, so
positions are now valued at their last known close on days their market is
shut. Without that, equity dropped to zero on holidays, the same class of
bug as round 17's.

## Results

**Each market alone** (crypto-level costs, 3% swap): about +2%/yr on gold,
0 to +1%/yr on the stock indices, and negative on oil and on 3 of 4
currency pairs. Buy and hold returned more on every market that rose: S&P
500 +12.2%/yr, Nasdaq +17.7%/yr, gold +7.9%/yr.

**Portfolio** (all markets eligible, max 5 open, 1% risk), at typical CFD
costs:

| | Swap 0% | **Swap 3%** | Swap 6% |
|---|---|---|---|
| Gold, silver, oil + 3 indices | +8.9%/yr, DD −24% | **+5.9%/yr, DD −29%** | +3.4%/yr, DD −33% |
| All 11 markets | +8.1%/yr, DD −30% | **+5.2%/yr, DD −32%** | +1.3%/yr, DD −37% |

The two halves differ a lot: 2010–17 made +0.7% to +3.1%/yr, and 2018–26
made +8.4% to +9.4%/yr (all at 3% swap). The crypto book on the same rules
made +22.7%/yr with a −31% drawdown.

## What it means

- The edge doesn't carry over. These rules make money in crypto because
  crypto trends are large and long. In gold, indices and forex the same
  rules earn about 5%/yr after swaps, with drawdowns about as deep as
  crypto's. Simply holding an S&P 500 index fund did better with no
  trading at all.
- Swaps matter: each 3% of yearly swap costs the portfolio about 3%/yr.
- Professional trend-following in these markets works differently. It
  trades 50 or more futures markets, both long and short, sized by
  volatility. Making that work would be a new research project, not a
  port of this bot.
- Re-tuning the rules for these markets could make the backtest look
  better, but on this evidence it would be curve-fitting (rounds 2 and
  14).

## Decision

Don't build an XM/MetaTrader bot. Building one would also need the owner to
open the XM demo account themselves, and a Windows PC or VPS running
MetaTrader 5 all day, since MetaTrader's Python link only runs on Windows.
Gold exposure is already covered more cheaply through PAXG on OKX
(round 17), which has no swap, no leverage and no new broker.
