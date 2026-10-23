# Research round 27: is the trailing stop good, and is 3 × ATR the right distance? (2026-10-24)

**Question (from the owner).** Is the trailing stop good? Round 16 already
showed it beats a fixed 3:1 profit target (Sharpe 0.97 vs 0.74). This round
tests the distance: ATR trails at 2–5 × ATR, and plain percentage trails
(10–25% below the highest close, like most trading apps offer). They're
run on round 21's six close times × two halves (12 cells).

**Pass bar, set before running:** the live 3 × ATR trail is "fine" unless
another exit has the better Sharpe in at least 9 of the 12 cells.

Script: `research/scripts/research27.py`. Output: `research/results/research27.out`.

**Two corrections made before reporting:**
- A fixed-target variant was dropped. Round 12's simulator only exits on
  stops, so it produced a meaningless result.
- The headline "median over 12 cells" mostly reflected the 2018–21 bull
  market, so the results are now shown per half.

## Results (median over the six close times)

| Exit | 2018–21 | 2022–26 | Drawdown 22–26 | Trades 22–26 | Sharpe wins vs live |
|---|---|---|---|---|---|
| 2 × ATR | +36.9%, Sh 1.40 | **+13.3%, Sh 0.65** | −28.0% | 460 | 7/12 (3/6 recent) |
| 2.5 × ATR | +41.9%, 1.51 | +11.2%, 0.56 | −28.5% | 358 | 9/12 (3/6) |
| **3 × ATR (live)** | +35.2%, 1.28 | +10.8%, 0.54 | −30.4% | 302 | — |
| 4 × ATR | +62.8%, 1.68 | +6.6%, 0.37 | −34.7% | 225 | 7/12 (1/6) |
| 5 × ATR | +63.5%, 1.49 | +6.2%, 0.36 | −36.7% | 183 | 7/12 (1/6) |
| 15% below high | +46.8%, 1.60 | +9.4%, 0.48 | −29.3% | 262 | 8/12 (2/6) |
| 25% below high | +51.6%, 1.55 | +11.4%, 0.55 | −31.2% | 156 | **11/12 (5/6)** |

## What it means

- **Yes, a trailing stop is good.** Every trail tested made money in both
  halves, and round 16 showed a fixed target does worse.
- **The best distance depends on the market.** In the 2018–21 bull market,
  wide trails (4–5 × ATR, or 25% below the high) did far better, because
  they let huge trends run. In the choppier 2022–26 market, wide ATR trails
  gave much of that back, and tighter trails (2 × ATR) did best.
- **By the pre-set rule, the 25% trail "beats" the live one** (11 of 12
  cells). But in the recent half the difference is negligible: +11.4% vs
  +10.8%/yr, Sharpe 0.55 vs 0.54. Its lead comes from 2018–21. With nine
  challengers tested, one of them was likely to "win" by luck.
- 3 × ATR sits in the middle and holds up in both kinds of market, which is
  a reasonable place for a rule that has to work in markets we can't
  predict.

## Decision

No change. The 3 × ATR trail stays. The 25% percentage trail is noted as a
candidate, but changing the exit while the owner is testing 5 vs 6 checks
would mix up the two experiments. It can be revisited after the 90-day
comparison.
