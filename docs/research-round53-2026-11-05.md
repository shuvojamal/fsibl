# Research round 53: limit new buys per day? (scheduled daily run)

**Question.** The VPS testnet bought ETH and ZEC on the same day. Coins move
together, so same-day entries are partly one bet on that day's market (round
48: losses cluster). Would capping new buys per day (1, 2 or 3, highest
score first) spread the risk usefully?

**Method.** Steady and growth, 6 of 8 checks, top 15, round 12's simulator,
round 21's 12 cells. Pass bar (set first): higher Sharpe in at least 9 of
12 cells, or at most 1 point less 2022-26 return with a shallower drop.

**Result** (`research/results/research53.out`, 2022-26 medians):

| | steady return / drop | growth return / drop |
|---|---|---|
| no limit (live) | +15.7% / −16.4% | +25.9% / −28.3% |
| max 1 per day | +14.3% / −15.5% | +22.9% / −25.7% |
| max 2 per day | +15.2% / −17.0% | +26.2% / −28.2% |
| max 3 per day | +15.7% / −16.3% | +25.9% / −28.3% |

**Verdict: technical passes, no real effect; no change.** "Max 3" passes on
steady (10 of 12) and growth (9 of 12), and "max 2" on growth (via the drop
rule), but by hairline margins: max 3 almost never binds (identical results
to 0.1 point), and growth's max-2 drop is 0.1 point shallower. These are
ties, not improvements. "Max 1" does spread entries and trims drops by 1-3
points, but costs 1.4-3 points of return a year. Note for future rounds:
the pass bar should require a minimum effect size, since near-identical
variants can "win" most cells by noise.
