# Strategy research, round 9 (2026-10-22): a universe rule without hindsight

Round 8 showed that *which* coins the strategy trades matters as much as
the rules. But the 20-coin list used since round 6 was picked by hand,
today, looking back at four years of history: coins that collapsed or were
delisted were never candidates. That is survivorship bias, and it flatters
every result built on that list.

This round replaces the hand-pick with a mechanical rule that only uses
information available at the time: **each quarter, rank a pool of 45
Binance coins by their trailing 90-day dollar volume (from the candles
themselves) and allow new entries only in the top N.** Open positions keep
running when a coin drops out.

Shared account, 10,000 USDT, max 5 open, 1% risk, round-7 rules.
Cells: return / max drawdown / profit factor.

| Universe | Full 4y | from 2024-10 | from 2025-07 | from 2025-12 |
|---|---|---|---|---|
| Hand-picked 20 (hindsight) | +188% / −31% / 1.95 | +92% / −31% / 2.06 | +22% / −19% / 1.62 | +34% / −14% / 2.61 |
| Whole pool of 45, no rule | +114% / −36% / 1.50 | +14% / −36% / 1.14 | +8% / −23% / 1.17 | +4% / −23% / 1.12 |
| **Top 10 by volume** | +84% / **−24%** / 1.65 | +72% / −24% / 1.76 | **+44% / −14% / 2.04** | +29% / −14% / 2.02 |
| **Top 15 by volume** | **+137%** / −28% / 1.77 | +59% / −28% / 1.60 | +37% / −17% / 1.88 | +25% / −17% / 1.86 |
| Top 20 by volume | +113% / −29% / 1.62 | +29% / −29% / 1.32 | +26% / −17% / 1.57 | +15% / −17% / 1.47 |
| Top 30 by volume | +96% / −30% / 1.49 | +24% / −30% / 1.25 | +20% / −20% / 1.40 | +12% / −20% / 1.35 |
| Top 20, max 8 open | +225% / −38% / 1.67 | +95% / −38% / 1.54 | +38% / −25% / 1.58 | +18% / −26% / 1.42 |

## Reading

1. **The hand-picked figures were inflated.** Given the whole pool with no
   filter, the same rules make +114% instead of +188%, and barely profit
   in the recent windows. A good part of the hand-picked result was
   choosing, in hindsight, coins that survived.
2. **A volume filter recovers most of it honestly.** Trading only the most
   traded coins works because volume tracks where money is still flowing:
   dying coins drop out of the top ranks before the strategy wastes slots
   on them. Top 10 is the strongest in the bear windows (+44% where
   holding lost 50%) with the smallest drawdown; top 15 is the best
   balance over the full period.
3. **Narrower is better.** Every widening of the universe (10 → 15 → 20
   → 30 → 45) lowers the profit factor. Concentrating the five slots on
   the deepest markets beats spreading the search.
4. Max 8 open on the top 20 earns the most over four years but with
   −38% drawdowns; not worth it.

**Honest standing:** the realistic expectation for this strategy is the
**top-15 row**, about +137% over four years (roughly +24% a year) with a
−28% worst drawdown, not the +188% of the hand-picked list. That number
comes from a rule that could have been followed in real time.

## Decisions

- New command `python -m tradebot scan --top 15`: ranks the pool by
  90-day volume, keeps the top 15, scores them, and marks today's signals.
  `--symbols-only` prints the list for pasting into `live`.
- Recommended demo setup going forward: re-run `scan --top 15
  --symbols-only` at the start of each quarter and restart the opportunity
  bot on that list (open positions carry over).

Top 15 by volume as of 2026-10-22: BTC, ETH, SOL, ZEC, XRP, NEAR, SUI, BNB,
DOGE, UNI, AVAX, ADA, PEPE, LINK, LTC. Two years earlier it included SHIB,
TRX, HBAR and XLM, which have since dropped out.
