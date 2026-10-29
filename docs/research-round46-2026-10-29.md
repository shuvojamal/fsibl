# Research round 46: what missed days cost (scheduled daily run)

**Prompt.** The OKX demo has not run since 2026-10-25 (GitHub stopped
starting its jobs over a billing block). Round 23 measured running hours
late; this measures whole days with no run: no stop checks, no trailing, no
buys; after the outage only that day's candle is seen.

**Method.** Seeded random outage patterns, steady set-up (8 × 0.5%, 6 of 8,
top 15), round 12's simulator and costs, round 21's 12 cells, no backstop.
Pass bar (set first): tolerable if 2022-26 median return is at most 3 points
lower and the median worst drop at most 5 points deeper than no outages.

**Result** (`research/results/research46.out`, 2022-26 medians):

| outages | days missed | return/yr | Sharpe | worst drop | avg losing trade |
|---|---|---|---|---|---|
| none | 0% | +15.7% | 1.03 | −16.4% | −0.88R |
| 5% of days at random | 5% | +14.5% | 0.92 | −17.0% | −0.88R |
| 3 days every month | 10% | +14.9% | 0.99 | −16.6% | −0.92R |
| 7 days every month | 23% | +12.8% | 0.84 | −14.6% | −0.97R |
| 30 days every year | 8% | +15.8% | 1.03 | −15.9% | −0.85R |

All patterns tolerable by the bar.

**Meaning.** The strategy is slow (daily candles, trades lasting weeks), so
missing days costs little on average: even a week lost every month cost
about 3 points a year, and losing trades got only slightly worse. The real
danger is not in these averages: a sharp crash during an outage, when no stop
is checked. On OKX the resting backstop order covers that; the Binance
accounts have none (round 45). So: fix outages promptly, but a few missed
days are not a crisis, and a Binance backstop matters more than uptime.
