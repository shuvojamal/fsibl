# Research round 23: the cost of a late run, and the 2% price guard (2026-10-23)

**Question.** Both live bots decide on the 00:00 UTC daily close but run
later. The GitHub job is often about 4 hours late, and a manual run can be
up to 17 hours late; the VPS runs within minutes. The bot also skipped any
buy whose exchange price had moved more than 2% from the signal close (the
bad-data guard). How much does lateness cost, and does that guard help?

Pass bar, set before running: at the real delays (0 and 4 h), the 2% guard
must cost no more than 1 percentage point a year against no guard, in both
halves.

Script: `research/scripts/research23.py`. Output: `research/results/research23.out`.
Data: round 21's 30-coin daily candles rebuilt from hourly data. Signals,
universe and exits come from the 00:00 candles, exactly as in round 12;
only the entry changes. A run d hours late buys at the price d hours into
the day. Costs as usual. With 0 h and no guard it reproduces round 21's
00:00 result (+25.4%/yr, 476 trades).

## Results

| Entry delay | No guard | With the 2% guard (buys skipped) |
|---|---|---|
| **0 h (VPS)** | **+25.4%/yr, Sh 1.03** | same (0 skipped) |
| **4 h (typical GitHub)** | +23.2%/yr, Sh 0.97 | +22.5%/yr, Sh 0.94 (75) |
| 8 h | +20.8% | +19.6% (141) |
| 12 h | +20.9% | +21.0% (163) |
| 16 h | +20.1% | +20.5% (190) |

At 4 h late, the 2% guard cost **+0.4 points in 2018–21 but −1.4 points
in 2022–26**, so it fails the pass bar. Guards of 1% and 3% weren't better
(1% cost 2.2 points a year); 5% cost almost nothing.

## What it means

1. **Running on time matters.** Entering 4 hours after the close costs
   about 2 points a year, and 8–16 hours costs 4–5. The VPS (runs minutes
   after the close) is worth that much against the late-starting GitHub job.
2. **Don't skip a coin because it kept rising.** The guard's second job,
   not chasing, loses money. Coins that had already moved more than 2% by
   the time of the run tended to keep going, which is what a trend strategy
   is built on.
3. The guard's real job is **catching bad data**: Binance's data saying
   one thing while the exchange shows another. A coin that rose since the
   close isn't bad data.

## Change made

The bad-data guard now compares the exchange's price with **Binance's live
price** (the source of the signals), not with the signal candle's close.
It still skips a buy when the two disagree by more than 2% (a data or
exchange problem, or an artificial testnet price), and it no longer skips
coins that simply moved since the close. The stale-candle check is
unchanged. Tests cover all three cases.

Recommendation for the owner: treat the VPS bot as the timely one. The
GitHub job's frequent multi-hour delays cost about 2%/yr in this test.
