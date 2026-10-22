# Strategy research, round 4 (2026-10-22): one account, many coins

Rounds 1–3 gave every coin its own pot of money. A real account is one pot
shared by all the coins, which changes two things: each trade's size is a
fraction of the *whole* account, and several coins can signal at once. This
round simulates that: 10 coins trading from one 10,000 USDT account with
the trailing-stop scorer, risking 1% or 2% of total equity per trade, with
a cap on how many positions may be open at the same time.

Daily candles, fees 0.1%/side, slippage 0.05%, next-open fills.

| Window | Max open | Risk/trade | Return | Per year | Max DD | Trades | Win | PF |
|---|---|---|---|---|---|---|---|---|
| Full 4 years | 2 | 1% | +38.0% | +8.1% | −18.1% | 96 | 34% | 1.42 |
| Full 4 years | 3 | 1% | +42.8% | +9.1% | −23.8% | 139 | 32% | 1.34 |
| Full 4 years | **5** | **1%** | **+108.9%** | **+19.6%** | **−30.3%** | 204 | 32% | 1.55 |
| Full 4 years | 10 | 1% | +75.2% | +14.6% | −51.9% | 311 | 30% | 1.31 |
| Full 4 years | 5 | 2% | +126.7% | +22.0% | −46.5% | 197 | 32% | 1.54 |
| from 2024-10 | 5 | 1% | +70.8% | +29.8% | −30.3% | 104 | 33% | 1.63 |
| from 2025-07 | 5 | 1% | +7.7% | +6.2% | −21.4% | 60 | 32% | 1.01 |
| from 2025-07 | 2 / 3 / 10 | 1% | −5.4% / −2.5% / −5.1% | | −16% to −32% | | | 0.6–0.8 |
| from 2025-12 | 5 | 1% | +18.6% | +23.1% | −11.2% | 35 | 37% | 2.04 |

Equal-weight buy-and-hold basket of the same 10 coins: full 4 years
+67.9%; from 2024-10 −4.2%; from 2025-07 −50.4%; from 2025-12 −19.0%.

## Reading this correctly

**The big numbers are mostly bigger bets, not a new edge.** In the
per-coin tests each trade risked 1% of a one-tenth-sized pot. Here each
trade risks 1% of the *whole* pot, so every trade is up to ten times larger
relative to the money behind it. Returns scale up accordingly, and so do
the drawdowns: −30% at "1% risk, 5 open" is a far cry from the −10% of the
per-coin tests. The per-trade quality (profit factor 1.3–1.6, win rate
about a third) is the same as before.

**It is path-dependent.** In the 2025-07 window the 5-open cap earns +7.7%
while 2, 3 and 10 all lose. Which coins get a slot first decides the
outcome, and that is luck, not skill. Treat any single window's figure as
noise around a small positive mean.

**The full-period return is one bull run.** Almost all of the +109% was
earned in 2023–24. The strategy beat holding the basket over four years
(+109% vs +68%) with a smaller worst drawdown (−30% vs roughly −60% for the
basket), which is the genuine point in its favour: it took part in the
bull run and sidestepped most of the bear.

## Decisions

1. **Five coins, max five open, 1% of account equity per trade** is the
   setting for the demo account. More coins or more open positions add
   drawdown faster than return; 2% risk nearly doubles the drawdown for a
   small gain.
2. **The live trader now sizes from account equity**, not from the
   per-trade cap. Before this round `--trade-usdt 200` with 1% risk on a
   5,000 USDT demo account produced trades of about 40 USDT risking 2 USDT
   each, far too small to learn anything from. Now `--risk 0.01` means 50
   USDT of risk per trade on that account and `--trade-usdt` only caps the
   notional (set it to about 1,000).
3. **Expect −20% to −30% drawdowns** on the way to the long-run return. If
   that is not acceptable, run `--risk 0.005`, which halves both.

## Next

- Round 5: pyramiding (adding to a winner as its trail rises) and a
  portfolio-level daily loss limit, in the shared-account simulation.
- Keep the demo running untouched for weeks. The research says "small
  positive, large swings"; only the demo record can say whether that
  holds in real time.
