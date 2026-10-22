# Strategy research, round 6 (2026-10-22): pyramiding, throttle, universe

Shared-account simulation from round 4 (10,000 USDT, max 5 open, 1% of
equity risked per trade, trailing-stop scorer, daily candles), with three
additions. "Other 10" = BNB, TRX, ATOM, UNI, NEAR, FIL, ETC, XLM, ALGO,
AAVE, chosen before looking at their results.

| Variant | Full 4 years | from 2024-10 | from 2025-07 | from 2025-12 |
|---|---|---|---|---|
| **A0 baseline** (original 10 coins) | +109% / DD −30% | +71% / −30% | +7.6% / −21% | +18.6% / −11% |
| A1 pyramid: +1 unit at break-even | +140% / −36% | +89% / −35% | +3.5% / −25% | +16.9% / −13% |
| A2 pyramid: up to +2 units | +83% / −41% | +67% / −39% | +2.9% / −29% | +18.1% / −15% |
| B1 drawdown throttle (half risk below −10%) | +41% / −20% | +68% / −22% | +2.9% / −16% | +18.3% / −11% |
| B2 throttle + pyramid 1 | +90% / −23% | +99% / −26% | +6.1% / −18% | +18.6% / −13% |
| **C1 other 10 coins** | **+133% / −25%** | **+94% / −25%** | **+22.5% / −15%** | **+32.4% / −15%** |
| C2 all 20 coins, max 5 open | +154% / −33% | +77% / −33% | +11.7% / −23% | +24.0% / −16% |
| C3 all 20 coins, max 8 open | +151% / −38% | +77% / −38% | +10.5% / −25% | +27.4% / −16% |
| Buy & hold, original 10 | +68% | −4% | −50% | −19% |
| Buy & hold, other 10 | +40% | +8% | −29% | +24% |

(return / maximum drawdown)

## A. Pyramiding: not adopted

Adding a unit once the trail locks in break-even raises the full-history
return (+109% → +140%) but only because of the 2023–24 bull run; in the
two recent windows it earns less and draws down more, and the win rate
falls to about a quarter. A second add is worse everywhere. More size in
a winner is more size in the next reversal.

## B. Drawdown throttle: optional, not default

Halving the risk while the account is more than 10% off its peak cuts the
worst drawdowns by a third (−30% → −20%, −21% → −16%) and costs little in
the recent windows, but it gives up most of the full-period return (+109%
→ +41%) because the bull run started from inside a drawdown. It is a
preference, not an edge: use it if a −30% swing is unacceptable, and
accept a lower long-run return. Not implemented in the live bot yet.

## C. Universe: the strategy is not a lucky pick of coins

This is the useful result. Ten different coins, never used in any earlier
round, do **as well or better**: +133% over four years with a smaller
drawdown, and positive in every window, including +22.5% in the 2025-07
bear window where the original ten made +7.6%. The entry and exit rules
generalise; they were not fitted to BTC/ETH/SOL's history.

All 20 coins with a cap of 5 open positions is the best full-period
result (+154%) and positive in every window, at the cost of a slightly
deeper drawdown than either ten alone (more candidates means the five
slots fill in more crashes). Raising the cap to 8 adds drawdown, not
return.

## Decisions

1. **The live trader now has `--max-open`**, a cap on simultaneous
   positions across all symbols. Until now it could open one position per
   symbol, so a 20-coin list meant up to 20 positions.
2. **Recommended demo setup:** all 20 coins, `--max-open 5`, 1% risk.
   More candidates, same number of bets.
3. Pyramiding: dropped. Throttle: available on request (not built).

## Standing after six rounds

- Daily opportunity scorer, 5 of 8 checks, 2×ATR initial stop, 3×ATR
  trailing stop, 1% of account equity per trade, max 5 open, 20 coins.
- Shared account, full history: roughly +20–25% a year with −25% to −33%
  drawdowns; bear-market windows +8% to +22%; results hold on coins the
  rules never saw.
- Everything above is a backtest. The demo record is the real test, and
  it needs months, not hours.
