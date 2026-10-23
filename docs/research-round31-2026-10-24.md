# Research round 31: pyramiding (adding to winners)

**Question.** Can the bot earn more by adding to positions that are
already winning, instead of risking more on every new entry? A losing
trade would stay one small bet; only trades that work would get bigger.

**Method.** Round 12's simulator on round 21's six close times x two
halves (12 cells), top 15, 6 of 8 checks, 8 slots, for both recommended
set-ups (steady 0.5% and growth 1% risk). An open position gets an "add"
at the next day's open once its close is +1R (and/or +2R) above its entry
(R = the entry's initial risk per coin). Each add risks the same % of
equity as an entry, measured to the current trailing stop, uses free cash
only, and takes no new slot. New entries are filled first.

**Pass bar (set before running).** Higher Sharpe than the same set-up
without adds in at least 9 of 12 cells, and a 2022-26 median worst drop no
more than 3 points deeper.

**Result** (`research/results/research31.out`, medians over six close times):

| set-up | adds | 2022-26 return/yr | Sharpe | worst drop | Sharpe wins |
|---|---|---|---|---|---|
| steady | none | +15.7% | 1.03 | -16.4% | ref |
| steady | 1 at +1R | +21.8% | 1.04 | -21.9% | 6 of 12 |
| steady | 1 at +2R | +19.6% | 1.00 | -20.7% | 4 of 12 |
| steady | 2 (+1R, +2R) | +24.2% | 1.01 | -25.2% | 4 of 12 |
| growth | none | +25.9% | 0.97 | -28.3% | ref |
| growth | 1 at +1R | +19.9% | 0.74 | -33.1% | 7 of 12 |
| growth | 1 at +2R | +19.5% | 0.74 | -33.0% | 2 of 12 |
| growth | 2 (+1R, +2R) | +18.5% | 0.69 | -33.9% | 5 of 12 |

**Verdict: rejected, no change.** Every variant fails. On the steady
set-up, adds raise the return only by adding risk: the return per unit of
risk (Sharpe) stays flat and drops get deeper, so it's just a roundabout way
of using a higher risk setting. On the growth set-up, adds hurt in 2022-26:
the cash goes to winners that then give back their gains in choppy markets.
Note: "steady + 1 add at +1R" (+21.8%, -21.9%) is no better than simply
choosing a risk level between steady and growth.

Ran on code at the commit in `research/README.md`.
