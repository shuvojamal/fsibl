# Research round 47: a minimum stop distance for very calm coins (scheduled daily run)

**Question.** Big positions come only from very calm coins (round 45: TRX,
whose 2 × ATR stop can sit ~2% below the entry). Instead of a size cap
(rounds 43/45, no effect), would a floor on the initial stop distance (never
closer than 3% or 5% below the entry) help? It shrinks positions in calm
coins and gives those trades more room; normal coins are unaffected.

**Method.** Growth and steady set-ups, 6 of 8 checks, top 15, round 12's
simulator and costs, round 21's 12 cells; trailing stop unchanged. Pass bar
(set first): higher Sharpe in at least 9 of 12 cells, or at most 1 point
less 2022-26 return with a shallower worst drop.

**Result** (`research/results/research47.out`): practically no effect.
Growth: floor 3% identical (+25.8% vs +25.9%); floor 5% +27.4% in 2022-26
but a slightly deeper drop, 3 of 12 wins. Steady: identical or within 0.3
points. **No pass, no change.**

**Meaning.** Calm-coin trades are too few to move the results either way,
which matches round 45 (big positions were 1.6% of trades and profitable).
The live rules stay as they are. The one protection still missing for big
positions is a resting backstop order on Binance (rounds 45/46).

**Also today (bug fix):** the live-vs-backtest check listed every trade the
live bot made that morning as "only live" for a day, because the replay
could not fill orders decided at the latest close (their fill day's candle
hadn't closed). It now fills them at the last close, marked as estimated.
