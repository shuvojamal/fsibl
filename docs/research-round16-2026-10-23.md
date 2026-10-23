# Research round 16: deflated Sharpe ratio of the live rules (2026-10-23)

**Question.** This project has tried hundreds of rule variants over 15
rounds and kept the best. The best of many tries looks good partly by luck.
How likely is it that the live rules have a real edge rather than being the
lucky winner? (The method comes from martex-dev/martex-quant, which applies
it to every trial.)

Script: `research/scripts/research16.py`. Output: `research/results/research16.out`.
Method: the deflated Sharpe ratio (Bailey & López de Prado, 2014). It
compares the backtest Sharpe with the Sharpe that the best of N worthless
strategies would reach by chance, and adjusts for sample length, skew and
fat tails.

## Results

- **Live rules, 2017-08 to 2026-10:** Sharpe 0.97 a year, 3,352 days,
  kurtosis 11 (fat tails, as expected for crypto). Before correcting for
  the number of tries, the probability that the true Sharpe is above zero
  is 0.998.
- **Spread across 16 variants of the same rules** (costs, risk, universe,
  slots, ADX, score threshold, trail width, fixed target): annualised
  Sharpe from 0.74 to 1.25, standard deviation 0.13.

| Trials looked at (N) | Luck bar | DSR | Luck bar if the whole project's spread is 2x wider | DSR |
|---|---|---|---|---|
| 50 | 0.29 | 0.98 | 0.57 | 0.89 |
| 300 (about this project's count) | 0.36 | **0.97** | 0.73 | **0.77** |
| 1000 | 0.41 | 0.96 | 0.82 | 0.68 |

## What it means

- If the relevant competition is the family of trend rules, the live rules
  clear the bar comfortably (DSR about 0.97). If the competition is
  everything the project tried (hourly bars, arbitrage, rotation and more,
  whose Sharpes spread much wider), it's about 0.77: probably real, but
  not proven.
- These numbers are an **upper bound**. martex-quant measured that picking
  the coin pool at the end of the sample inflates a selection strategy's
  Sharpe by about 40% (their H71). Our pool of 55 coins is today's list,
  with LUNA and FTT missing. A 40% haircut takes the Sharpe to about 0.58,
  and the DSR at N=300 to roughly 0.75 (narrow spread) or under 0.5 (wide
  spread).
- **Don't switch to "min score 6"** even though it shows 1.25. Picking the
  best variant after the fact is exactly the selection this test penalises.
  The live rules were fixed in round 7–9 before these variants were
  compared.

## Decision

No rule change. Expectations stay as `docs/STRATEGY.md` states them (about
+15–25% a year, 20–30% drawdowns, roughly one losing year in three), with
added emphasis that the edge is likely but not proven. The demo record over
the coming months is the real test. From now on, each research round adds
to the trial count, so the bar keeps rising.
