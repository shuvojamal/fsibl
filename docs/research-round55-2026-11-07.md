# Research round 55: are the indicator lengths a fragile sweet spot? (scheduled daily run)

**Question.** The checks use 20/50/200-day EMAs, a 14-day ATR and a 20-day
breakout, never perturbed on the current set-up. A real edge should change
gently when they move a little.

**Method.** One parameter at a time moved about 25% down and up (10
variants), steady set-up (8 × 0.5%, 6 of 8, top 15), round 12's simulator,
round 21's 12 cells. Pass bar (set first): robust if every variant's 2022-26
median return is within 4 points of live and Sharpe within 0.15; a variant
is recommended only with 9+ of 12 Sharpe wins plus an effect of at least
0.5 points of return or 1 point of shallower drop.

**Result** (`research/results/research55.out`, 2022-26 medians):
- Gentle (within ~2 points): slow EMA 40/60, trend EMA 150, breakout 15/25,
  trend EMA 250 (−2.0 points).
- Sharper: fast EMA 15 (+12.4%, Sharpe 0.82), ATR 10 (+12.6%, 0.86),
  ATR 20 (+11.9%, 0.84) vs live +15.7%, 1.03. Fast EMA 25 also gives +12.5%.
- In 2018-21 these same variants did as well or better than live.
- Slow EMA 40 technically meets the recommend bar (9 of 12, +0.6 points),
  but with 10 variants tried a bare 9 of 12 is within luck.

**Verdict: fails the robustness bar (moderately fragile in 2022-26).** The
live lengths sit on a peak for recent years: nearby settings earn about 3-4
points a year less in 2022-26, while doing equally well in 2018-21. Part of
the live set-up's recent backtest return is likely tuning luck.

**Meaning.** Nothing to change (no variant is reliably better, and moving
to a neighbour would just pick a different point on the same hill). But
the planning numbers should lean to the cautious end: about 12% a year for
steady rather than 15.7%, which matches the "realistic" figures already
used (rounds 36/37: 10-13% for steady with savings). This is also why the
live demo matters: it shows real results that no amount of tuning can flatter.
