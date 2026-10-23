# Research round 29: with 8 slots × 0.5%, how many coins, and 5 or 6 checks? (2026-10-24)

**Question.** Round 28's winner (8 positions at 0.5% risk) fills more slots,
so it may benefit from a wider coin list, and round 24's "6 of 8 checks"
may combine differently with it. Tested: universe top 10/15/20/25 × 5 or 6
checks, all at 8 × 0.5%, on round 21's six close times × two halves.

**Pass bar, set before running:** beat round 28's base (top 15, 5 checks,
8 × 0.5%) on Sharpe in at least 9 of 12 cells, with a 2022–26 drawdown no
more than 3 points deeper.

Script: `research/scripts/research29.py`. Output: `research/results/research29.out`.

## Results (median over six close times)

| Case | 2018–21 | 2022–26 | Drawdown 22–26 | Trades 22–26 | Wins vs base |
|---|---|---|---|---|---|
| Live: top 15, 5 checks, 5 × 1% | +35.2%, Sh 1.28 | +10.8%, 0.54 | −30.4% | 302 | 0/12 |
| Base: top 15, 5 checks, 8 × 0.5% | +30.7%, 1.46 | +13.5%, 0.76 | −21.7% | 415 | — |
| top 20, 5 checks | +32.7%, 1.50 | +14.7%, 0.80 | −22.2% | 447 | 8/12 |
| top 25, 5 checks | +41.9%, 1.71 | +12.0%, 0.68 | −20.6% | 471 | 6/12 |
| **top 15, 6 checks** | +29.5%, **1.57** | **+15.7%, 1.03** | **−16.4%** | 253 | **9/12 PASS** |
| **top 20, 6 checks** | +36.4%, **1.72** | **+15.6%, 1.00** | −18.2% | 286 | **12/12 PASS** |
| top 25, 6 checks | +44.9%, 1.89 | +14.6%, 0.92 | −17.4% | 307 | 11/12 PASS |

## What it means

- **With more, smaller positions, "6 of 8 checks" now helps in the recent
  half too:** +15.7% vs +13.5%/yr with a shallower drop (−16% vs −22%). In
  round 24, with 5 slots at 1%, the stricter filter lost the live cell.
  Holding fewer but better trades works when the book is spread across 8
  slots.
- **Against today's live set-up,** "top 15, 6 checks, 8 × 0.5%" made
  **+15.7% vs +10.8%/yr in 2022–26 with about half the worst drop (−16% vs
  −30%)**, and more in 2018–21 risk-adjusted.
- **A wider list (top 20/25) passes too, but trust it less.** The 30 coins
  in this data were picked with hindsight, as the coins that filled the
  top-15 slots most often, so widening the list within them mostly adds
  coins that are already known to have done well. That's the bias
  martex-quant measured at about 40% of a selection edge (round 16). Top 15
  is the universe the live bot already uses.
- **Luck bar:** rounds 24, 27, 28 and 29 each added trials. The
  conclusions here rest on consistency across 12 cells, not on the best
  single number.

## Recommendation (the owner decides; nothing was changed)

On the test accounts, in Edit settings:
- **OKX demo:** Max positions **8**, Risk **0.5%**, Checks **5 of 8**
  (round 28's base)
- **VPS testnet:** Max positions **8**, Risk **0.5%**, Checks **6 of 8**
  (this round's best on the live universe)

Over the 90 days that's a clean live comparison of 5 vs 6 checks on the
better sizing. Keep the universe at top 15.
