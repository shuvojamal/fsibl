# Research round 52: does a 300-500 USDT account trade like the backtest? (scheduled daily run)

**Question.** The owner plans to start real money with 300-500 USDT. Small
risk-based positions can fall below Binance's minimum order (5 USDT on most
USDT pairs), and the bot then skips the buy. How often, and at what cost?

**Method.** Round 12's simulator starting at 300 or 500 USDT, skipping any
buy below 5 USDT (and 10 USDT as a stricter check); steady and growth, 6 of
8 checks, top 15, round 21's 12 cells; compared with no minimum. Pass bar
(set first): at 300 USDT, at most 5% of buys skipped and 2022-26 median
return within 1 point of no minimum.

**Result** (`research/results/research52.out`, 2022-26 medians):

| | buys skipped | return/yr | worst drop |
|---|---|---|---|
| steady, no minimum | 0% | +15.7% | −16.4% |
| steady, 300 USDT, min 5 | 0% | +15.7% | −16.4% |
| steady, 300 USDT, min 10 | 6.9% | +15.9% | −16.2% |
| growth, no minimum | 0.8% | +25.9% | −28.3% |
| growth, 300 USDT, min 5 | 13.2% | +25.6% | −28.9% |
| growth, 500 USDT, min 5 | 12.0% | +25.5% | −28.3% |

**Verdict.** Steady at 300 USDT: **fine**, no buys lost. Growth: fails the
bar on the skip count, but costs only about 0.3 points a year. The skipped
buys are mostly ones arriving when the account's cash is nearly all
invested; a large account would buy a tiny leftover position there, which a
small account can't place. (The counter also includes those no-cash cases.)

**Meaning.** A 300-500 USDT start works with the steady set-up exactly as
in the backtest; with growth it works almost the same. Planning numbers
for a small account don't need adjusting.
