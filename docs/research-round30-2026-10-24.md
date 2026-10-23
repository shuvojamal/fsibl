# Research round 30: bet bigger in bull markets? Regime-based risk per trade (2026-10-24)

**Question.** The owner wants more than ~15%/yr. Most losses come in bear
markets, so: risk 1% (or 1.5%) per trade while BTC is above its 200-day
EMA, and 0.5% (or 0.25%) while it's below. Every entry is kept; only the
size changes. All cases use 8 slots, 6 checks and the top-15 universe
(round 29), on round 21's six close times × two halves.

**Pass bar, set before running:** beat flat 1% on Sharpe in at least 9 of
12 cells, with a 2022–26 drawdown at least 5 points shallower and a return
no more than 2 points lower.

Script: `research/scripts/research30.py`. Output: `research/results/research30.out`.

## Results (median over six close times)

| Case | 2018–21 | 2022–26 | Drawdown 18–21 | Drawdown 22–26 | Wins vs flat 1% |
|---|---|---|---|---|---|
| flat 0.5% | +29.5%, Sh 1.57 | +15.7%, 1.03 | −12.8% | −16.4% | 3/12 |
| **flat 1%** | **+61.7%, 1.66** | **+25.9%, 0.97** | −21.8% | **−28.3%** | — |
| bull 1% / bear 0.5% | +54.3%, 1.60 | +23.6%, 0.94 | −21.8% | −26.5% | 1/12 |
| bull 1.5% / bear 0.5% | +79.8%, 1.66 | +17.8%, 0.73 | −26.4% | −33.2% | 3/12 |
| bull 1% / bear 0.25% | +50.5%, 1.53 | +22.0%, 0.91 | −21.8% | −26.8% | 1/12 |

## What it means

- **Regime sizing fails.** Cutting size when BTC is below its 200-day EMA
  barely reduces the drawdown (−26.5% vs −28.3%) and costs return. The
  bot's own checks already keep it mostly out of bear markets, so there's
  little left to save. That matches round 11, where a BTC filter on
  entries didn't help either.
- **The useful finding: with 6 checks and 8 slots, flat 1% risk is a
  strong "growth" setting.** It made +25.9%/yr in 2022–26 and +61.7% in
  2018–21 (backtest), with a worst drop of about −28%. That's no deeper
  than today's live setting (5 × 1%, 5 checks: +10.8%, −30%) for more than
  twice the return. Round 28 showed the same 8 × 1% with 5 checks dropped
  −40%. The stricter 6-check filter is what makes the bigger bets
  affordable.
- Realistic expectation for 8 × 1% with 6 checks, after the usual haircuts:
  roughly **+18–25% a year**, with drops of 25–35%. 8 × 0.5% is about half
  of both.

## Recommendation (the owner decides; nothing was changed)

Two settings to compare over the 90 days, both with **8 positions and 6
checks**:
- **steady:** risk 0.5%
- **growth:** risk 1%

Regime sizing isn't worth adding.
