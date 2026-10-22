# Strategy research, round 8 (2026-10-22): time exits, cooldowns, a third universe

20-coin shared account (10,000 USDT, max 5 open, 1% risk, trailing-stop
scorer with the round-7 RSI zone 40–80). Cells: return / max drawdown /
profit factor.

| Variant | Full 4y | from 2024-10 | from 2025-07 | from 2025-12 |
|---|---|---|---|---|
| **Baseline (round 7 default)** | +188% / −31% / 1.95 | +92% / −31% / 2.06 | +22% / −19% / 1.62 | +34% / −14% / 2.61 |
| A. time exit after 10 days | +224% / −28% / 1.98 | +98% / −28% / 2.05 | +15% / −18% / 1.42 | +30% / −15% / 2.40 |
| A. time exit after 20 days | +180% / −31% / 1.89 | +91% / −31% / 2.05 | +22% / −19% / 1.62 | +36% / −13% / 2.76 |
| A. time exit after 40 days | +193% / −31% / 1.94 | +90% / −31% / 2.03 | +21% / −20% / 1.57 | +33% / −15% / 2.60 |
| B. cooldown 3 days after a stop | +201% / −31% / 2.03 | +88% / −31% / 2.06 | +20% / −20% / 1.57 | +34% / −14% / 2.60 |
| B. cooldown 7 days | +165% / −29% / 1.92 | +94% / −29% / 2.13 | +19% / −19% / 1.55 | +35% / −14% / 2.74 |
| B. cooldown 14 days | +71% / −33% / 1.43 | +56% / −33% / 1.66 | +2% / −18% / 1.07 | +18% / −15% / 1.95 |

## A. Time exit: not adopted

Selling a trade that has made less than half an ATR of progress after N
days frees the slot for something better in theory. In practice it is
noise: 10 days helps the full period and hurts the bear window, 20 and
40 days change nothing. The trailing stop already handles trades that go
nowhere.

## B. Cooldown after a stop-out: not adopted

Waiting a few days before re-entering a coin that just stopped out makes
no consistent difference, and 14 days clearly hurts: a stop-out followed
by an immediate new breakout is one of the strategy's better entries.

## C. Third universe: the caveat on generalisation

| Universe | Full 4y | from 2024-10 | from 2025-07 | from 2025-12 | Buy & hold (full) |
|---|---|---|---|---|---|
| Original 10 (round 6) | +106% / −30% | +69% / −30% | +7% / −21% | +18% / −11% | +68% |
| Other 10 (round 6) | +131% / −25% | +92% / −25% | +22% / −15% | +32% / −15% | +40% |
| **Third 10** (SHIB, SAND, MANA, AXS, EOS, VET, HBAR, ICP, GRT, THETA) | **+40% / −45%** | +16% / −45% | **−12% / −28%** | **−4% / −21%** | **−70%** |
| All 30, max 5 open | +103% / −34% | +34% / −34% | +23% / −22% | +16% / −22% | |
| All 30, max 8 open | +138% / −44% | +48% / −44% | +14% / −28% | +4% / −27% | |

Round 6 said the rules generalise. They do, but not without limit: on a
third set of coins, chosen as "well-known alts that have been around four
years", the strategy made +40% over the period against −70% for holding
them, then **lost money in both recent windows**. These are coins in
structural decline (SHIB, SAND, MANA, AXS, EOS, THETA all lost 60–90% of
their value). A long-only trend strategy on a dying asset gets a few
false breakouts and little else. Adding them to the 20 drags the
portfolio down (+188% → +103%) because they take slots from better
candidates.

The rules are not the problem; the universe is. Lesson, and the one
decision from this round: **trade the strategy on coins that still have
a market** (large, liquid, still-growing names), not on anything with a
chart. The 20-coin list stays as it is. A formal universe rule (for
example, top 30 by market cap, re-checked quarterly) is the next thing to
build, since "I picked these 20" is still a judgement call.

## Standing after eight rounds

- Rules unchanged since round 7: 5 of 8 checks, RSI 40–80, 2×ATR stop,
  3×ATR trail, 1% of equity per trade, max 5 open, 20 liquid coins.
- Backtest, shared account: +188% over four years (about +30%/year),
  drawdowns −14% to −31%, positive in every window, survives triple costs.
- Fails on coins in long-term decline. Universe quality matters as much
  as the rules.
- Live since 16:22 UTC on the OKX demo with the 20-coin list; the record
  there is the test that counts.

## Next

- Universe rule by market cap / volume, re-evaluated quarterly, tested
  by rebuilding the historical universe year by year (so a coin that was
  not top-30 in 2023 is not in the 2023 portfolio).
- Daily report: a command that summarises open positions, P&L, and the
  current score of every coin, so the demo can be reviewed in a minute.
