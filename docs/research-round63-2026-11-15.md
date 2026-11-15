# Research round 63: is the current market unusually hard for the strategy? (scheduled daily run)

**Question.** The live accounts started badly (testnet −6.1% since
2026-10-23). How did the strategy do in the most recent months of the
backtest data, and was that unusual?

**Method.** Steady and growth, round 12's simulator, round 21's six close
times up to the end of the cached data (2026-10-21); returns over the last
3, 6 and 12 months, placed among all windows of the same length since
2018-03. Pass bar (descriptive, set first): "normal" if the last 6 months
sit between the 10th and 90th percentile.

**Result** (`research/results/research63.out`, medians):

| | last 3 months | last 6 months | last 12 months |
|---|---|---|---|
| steady | +17.2% (85th pct) | +15.4% (69th) | +14.6% (41st) |
| growth | +33.2% (83rd) | +30.4% (71st) | +27.7% (46th) |

**Verdict: normal.** In fact the strategy had a strong summer: the last
quarter before the live accounts started was in its top ~15%.

**Meaning.** The live accounts began just as a strong run ended. Trend
following typically gives some back when a run turns (a cluster of
stop-outs, round 48), which is what the testnet has seen since late
October. The cached data stops on 2026-10-21, so November itself isn't in
this test; the live-vs-backtest check confirms the bot is trading exactly
as the backtest would. No change.

**Bot check note:** the testnet's third "only in the backtest" trade (PEPE
sold on 2026-11-15) is the backtest closing the PEPE position it opened on
2026-10-24, which the testnet never bought (its price check blocked it).
Explained, not a fault.
