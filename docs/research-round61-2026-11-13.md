# Research round 61: pause new buys after a losing streak? (scheduled daily run)

**Prompt.** The VPS testnet sold UNI at its stop on 2026-11-13 (−45.86
USDT): six losers in seven trades since 2026-10-23 (realised −304.65).
Losses cluster (round 48). Would a cool-off help: after K losing exits in a
row, no new positions for D days (exits keep working)?

**Method.** No pause vs K = 3 or 5, D = 7 or 14 days; steady and growth, 6 of
8 checks, top 15, round 12's simulator, round 21's 12 cells. Pass bar (set
first, with effect-size floor): higher Sharpe in 9 of 12 cells and +0.5
points of 2022-26 return or a 1-point shallower drop, on both set-ups.

**Result** (`research/results/research61.out`, 2022-26 medians):

| | steady return / Sharpe | growth return / Sharpe | Sharpe wins (steady / growth) |
|---|---|---|---|
| no pause (live) | +15.7% / 1.03 | +25.9% / 0.97 | ref |
| 3 losses → 7 days | +11.7% / 0.81 | +22.0% / 0.87 | 3 / 3 |
| 3 losses → 14 days | +10.1% / 0.73 | +19.9% / 0.82 | 1 / 2 |
| 5 losses → 7 days | +15.7% / 1.04 | +26.4% / 0.98 | 6 / 6 |
| 5 losses → 14 days | +16.3% / 1.05 | +24.3% / 0.93 | 4 / 4 |

**Verdict: fails; no pause.** Short-trigger pauses (after 3 losses) cost
4-6 points a year: they sit out the first signals of the next trend, which
are often the big winners. Longer-trigger pauses are roughly neutral and
also fail the bar. Losing streaks are noise to sit through, not a signal
to stop.

**Bot check:** the testnet now holds no positions; its trades still match
the backtest (11 matched). The OKX demo has not run since Nov 4 (VPS setup
pending); its UNI position is likely below its stop with only the OKX
backstop (4.84) protecting it.
