# Research round 58: tighten the trailing stop once a trade is well in profit? (scheduled daily run)

**Question.** Keep the 3 × ATR trail while a trade is young, then tighten it
once the trade is +3R or +5R in profit (R = the entry's initial risk), to
keep more of big winners when a trend breaks?

**Method.** Live vs 2 × ATR after +3R, 2 × ATR after +5R, 2.5 × ATR after
+3R; steady and growth, 6 of 8 checks, top 15, round 12's simulator, round
21's 12 cells. Pass bar (set first, with effect-size floor): higher Sharpe in
at least 9 of 12 cells and +0.5 points of 2022-26 return or a 1-point
shallower drop, on both set-ups.

**Result** (`research/results/research58.out`, 2022-26 medians):

| | steady return / Sharpe / avg R | growth return / Sharpe / avg R |
|---|---|---|
| live (3 × ATR always) | +15.7% / 1.03 / +0.64 | +25.9% / 0.97 / +0.66 |
| 2 × ATR after +3R | +12.2% / 0.91 / +0.45 | +18.7% / 0.80 / +0.45 |
| 2 × ATR after +5R | +12.3% / 0.89 / +0.47 | +18.4% / 0.78 / +0.48 |
| 2.5 × ATR after +3R | +14.9% / 0.98 / +0.54 | +21.8% / 0.86 / +0.57 |

**Verdict: fails; keep the 3 × ATR trail for the whole trade.** Tightening
cuts the average trade from about +0.65R to +0.45R: a tighter trail gets
shaken out of big trends during normal pullbacks, and those big winners pay
for all the small losses. Drops are only about 1 point shallower. Together
with round 10 (partial profit-taking) and round 27 (trail width), this
confirms: let winners run with the same wide trail.

**Also today:** the VPS testnet couldn't buy PEPE ("order book liquidity is
less than LOT_SIZE minimum"): the testnet's thin order book, not a bot
problem; real Binance is deep in PEPE. The bot logged it and carried on.
