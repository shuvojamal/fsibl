# Research round 44: "skip the 200-day trend check" on the growth set-up (scheduled daily run)

**Question.** Round 33's only passing idea, treating the trend_up check as
always passed, was tested on the steady set-up (8 × 0.5%). Does it also hold
at the growth set-up's 1% risk, which the VPS testnet runs?

**Method / pass bar.** As round 33 (set before running): higher Sharpe than
live in at least 10 of 12 cells (round 21's six close times × two halves),
a 2022-26 median worst drop no more than 3 points deeper, and higher Sharpe
in both halves of round 12's 55-coin pool.

**Result** (`research/results/research44.out`):

| | 2018-21 | 2022-26 | trades 22-26 |
|---|---|---|---|
| live, 30 coins | +61.7% / Sharpe 1.66, drop −22% | +25.9% / 0.97, −28% | 249 |
| trend check skipped | +75.3% / 1.77, −25% | +25.6% / 0.90, −30% | 320 |
| live, 55-coin pool | +59.7% / 1.67 | +14.8% / 0.65 | |
| trend check skipped, 55 coins | +76.6% / 1.83 | +26.0% / 0.90 | |

Sharpe wins: 9 of 12 (6 of 6 in 2018-21, 3 of 6 in 2022-26). Drop test and
55-coin test pass. **Fails narrowly** on the cell count.

**Meaning.** Two rounds now point the same way: skipping the trend check
clearly helps in strong bull markets and in the wider coin pool, but on the
main data it is a coin toss in 2022-26 conditions. Not recommended for the
growth account as a default. It stays an off-by-default switch; if the owner
wants to try it live, the steady (OKX) account, where it passed, is the
better place, once the OKX demo is running again.
