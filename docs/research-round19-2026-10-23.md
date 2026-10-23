# Research round 19: execution: how the bot buys and how its stops fire (2026-10-23)

**Question.** Same signals, different order handling. Could the bot make
more just by executing better?

- **A. Stops.** Live today, the bot looks once a day; if the day's low
  touched the stop, it sells at the next run (about the next open). The
  alternative is a real stop order resting on OKX that fires the moment
  price touches it.
- **A2. Backstop.** Keep the daily-close stop, and also rest an exchange
  stop order x% below it. That protects against a crash, or against the bot
  not running for days.
- **B. Entries.** Live today, the bot market-buys right after the signal
  close. The alternative is a limit buy k×ATR below the signal close, valid
  for N days: a better price, but it misses trades that never dip back.

Script: `research/scripts/research19.py` (round 12's simulator rebuilt with
these switches; with live settings it reproduces round 12 exactly,
+22.67%/yr and 487 trades). Output: `research/results/research19.out`.

## Results (2017-08 to 2026-10, then the two halves)

| | Whole period | 2017–21 | 2022–26 |
|---|---|---|---|
| **Live: stop checked at close, market buy** | **+22.7%/yr, DD −31%, Sh 0.97** | +26.9% | +19.3% |
| A. Exchange stop order | +18.9%, DD −32%, Sh 0.84 | +22.5% | +16.1% |
| A2. + backstop 5% lower | +18.7%, Sh 0.82 | +22.5% | +15.7% |
| A2. + backstop 10% lower | +20.2%, Sh 0.87 | +25.5% | +16.0% |
| A2. + backstop 20% lower | +22.1%, Sh 0.95 | +26.7% | +18.4% |
| B. Limit 0.25 ATR, 1 day | +21.1%, DD −40% | +36.6% | +9.0% |
| B. Limit 0.5 ATR, 1 day | +17.3%, DD −39% | +41.4% | −0.7% |
| B. Limit 0.5 ATR, 3 days | +33.1%, DD −45% | +71.5% | +6.1% |
| B. Limit 1 ATR, 3 days | +27.9%, DD −52% | +64.9% | +0.9% |

## What it means

1. **Checking stops at the daily close beats real stop orders,** in both
   halves. Crypto's daily lows often spike through a stop and recover by the
   close (the "wick"). A resting stop order sells at the bottom of the wick;
   the close check usually sells a day later, higher. The current design is
   right, and that's worth knowing, because "always use a stop order" is the
   textbook advice.
2. **A backstop costs money too,** and less the further away it sits. At 5%
   below the stop it costs about 4%/yr, at 20% about 0.6%/yr. A 20%
   backstop is cheap insurance against the scenario the backtest can't see:
   the GitHub job not running for several days during a crash.
3. **Limit entries are unstable,** so they're rejected. They were brilliant
   in 2017–21 (+65 to +72%/yr) and poor in 2022–26 (−1 to +9%/yr), with
   deeper drawdowns every time. The pattern makes sense: dips got bought
   back in the bull years, and in later years a dip often kept going. The
   whole-period +33% is a 2017–21 artefact. That's the overfitting pattern
   from rounds 2 and 14.

## Decision

- No change to entries or to how stops are checked.
- Option for the owner, not implemented: a resting exchange backstop 20%
  below each position's stop, moved up as the stop trails. It costs about
  0.6%/yr in the backtest and protects against several days of bot downtime
  in a crash. It needs OKX conditional (algo) orders: place, amend and
  cancel them as the stop moves.
