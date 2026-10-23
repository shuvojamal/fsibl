# Research round 24: "6 of 8 checks" vs the live "5 of 8", out of sample (2026-10-24)

**Question.** Round 16 found that requiring 6 of 8 checks had the best
Sharpe of 16 variants (1.25 vs 0.97). It wasn't adopted, because the best
of many variants looks good by luck. This round tests it in a way luck
can't explain: round 21's six versions of history (daily candles closing at
00, 04, 08, 12, 16 and 20 UTC), each split into 2018–21 and 2022–26, for 12
cells.

**Pass bar, set before running:** 6 of 8 replaces 5 of 8 only if it has the
higher Sharpe in at least 10 of the 12 cells **and** doesn't lower the
return in the live cell (00:00 close, 2022–26).

Script: `research/scripts/research24.py`. Output: `research/results/research24.out`.
Same simulator, 30-coin universe, costs and caveats as rounds 12 and 21.

## Results

| | Sharpe wins vs 5 | Return difference vs 5 (median, range) |
|---|---|---|
| 4 of 8 | 4 of 12 | +0.6% (−9.2% to +7.0%) |
| **6 of 8** | **11 of 12** | **+17.1%/yr (−3.0% to +25.4%)** |
| 7 of 8 | 8 of 12 | −5.8% (−23.5% to +14.4%) |

6 of 8 made, for example, +56% vs +35%/yr (00:00, 2018–21), +20% vs +8%
(08:00, 2022–26) and +19% vs +2% (12:00, 2022–26), with about a third
fewer trades. **The one exception is the live cell:** 00:00 in 2022–26,
where it made +15.5% against +18.5% (Sharpe 0.78 vs 0.80).

## Verdict

**FAIL on the pre-set bar**, because of that one cell, even though the rest
of the evidence strongly favours 6 of 8. Round 21 already found that 00:00
in 2022–26 was unusually kind to the live rules, which may be why 5 of 8
holds up there and almost nowhere else.

## What was done instead

- "Checks needed to buy" is now a setting (`min_score`, 4–7; offered as 5
  or 6 in the app's Edit settings), passed to the bot and to the
  live-vs-backtest check. The default stays 5.
- Recommendation for the owner: a live comparison. Set the VPS testnet
  account to 6 and keep the OKX demo on 5. Over the 90-day evaluation the
  two records show which one holds up in real trading. This is a choice
  for the owner; the bots are left as they are.
