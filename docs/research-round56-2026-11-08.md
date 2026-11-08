# Research round 56: spread the money over neighbouring settings? (scheduled daily run)

**Question.** Round 55 found the live settings sit on a peak for 2022-26.
The usual remedy for tuning luck: split the capital over a grid of nearby
settings so the result is the average of the hill, not its top.

**Method.** Nine equal sub-accounts (fast EMA 15/20/25 × ATR 10/14/20), each
the steady set-up on a ninth of the capital, summed; vs the live setting
alone. Round 12's simulator, round 21's 12 cells. Pass bar (set first):
2022-26 median return within 1 point of live AND a higher worst-cell Sharpe.

**Result** (`research/results/research56.out`):

| | 2018-21 return / Sharpe | 2022-26 return / Sharpe | worst drop 22-26 | worst-cell Sharpe |
|---|---|---|---|---|
| live (20, 14) | +29.5% / 1.57 | +15.7% / 1.03 | −16.4% | 0.58 |
| nine-setting ensemble | +31.3% / 1.66 | +14.0% / 0.93 | −16.4% | 0.63 |
| median single neighbour | +31.1% / 1.64 | +14.5% / 0.92 | −16.7% | 0.60 |

Ensemble beats live's Sharpe in 8 of 12 cells.

**Verdict: fails narrowly** (1.7 points below live in 2022-26; the bar
allowed 1). It is a little steadier (better worst cell, better 2018-21), but
not by enough to justify running nine sub-accounts.

**Meaning.** The ensemble's +14% is the fairer estimate of what this rule
family earns in 2022-26-like markets; live's +15.7% is the top of the hill.
Combined with the realistic drag (rounds 36/37), it supports the cautious
plan of about 12% a year for steady. No change.
