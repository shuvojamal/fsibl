# Strategy research, round 11 (2026-10-23): slot order and stop execution

Two questions raised by the first live run on GitHub Actions. Universe:
top 15 by trailing-90-day volume, re-ranked quarterly; max 5 open; 1% risk.
Cells: return / max drawdown / profit factor.

## A. When more coins signal than there are free slots, which first?

On its first day the live bot had 10 signals for 5 slots and would have
filled them alphabetically.

| Order | Full 4y | from 2024-10 | from 2025-07 | from 2025-12 |
|---|---|---|---|---|
| Pool order (earlier backtests) | +137% / −28% / 1.62 | +59% / −28% | +37% / −17% | +25% / −17% |
| Alphabetical (live bot until now) | +172% / −28% / 1.73 | +60% / −28% | +40% / −15% | +28% / −15% |
| **Highest score first** | +161% / −29% / 1.68 | +55% / −29% | +39% / −15% | +27% / −15% |
| Most-traded first | +151% / −30% / 1.63 | +57% / −30% | +33% / −17% | +26% / −17% |
| Strongest 20-day trend first | +134% / −30% / 1.54 | +55% / −30% | +35% / −17% | +30% / −15% |
| Random order, 10 seeds: mean [min..max] | +134% [+111..+165] | +54% [+44..+65] | +34% [+29..+42] | +24% [+21..+28] |

Reading: the order matters less than it looks. Ten random orders spread
from +111% to +165% over four years, so differences of that size between
rules are mostly luck about which coin happened to get a slot.
Alphabetical came out on top, but there is no reason the letter A should
predict returns; that is the luck. Highest-score-first is above the
random average in every window and has a reason behind it (more checks
agreeing). **Adopted** for the live bot, as a principled tie-breaker
rather than an edge. Realistic expectation stays the random-order mean:
about +134% over four years.

## B. Does checking stops once a day cost money?

Earlier backtests filled a stop at the stop price, as an exchange-side
stop order would. The GitHub bot checks once a day after the close.

| Stop execution | Full 4y | from 2024-10 | from 2025-07 | from 2025-12 |
|---|---|---|---|---|
| Exchange stop order (fills at the stop) | +172% / −28% | +60% / −28% | +40% / −15% | +28% / −15% |
| Checked at the daily close | +214% / −23% | +77% / −23% | +37% / −19% | +23% / −19% |
| Checked next morning, sells at open | +214% / −23% | +77% / −23% | +37% / −19% | +23% / −19% |

Reading: no clear cost. Acting on the daily close ignores intraday wicks
that would have stopped an exchange order out of a trade that then
recovered; that helped over four years and in the 2024 window. In the two
recent windows it was slightly worse, because on a genuine crash day the
loss runs to the close instead of stopping at the stop price (deeper
drawdowns, −19% vs −15%). Net: roughly a wash, with a fatter tail on bad
days. **The once-a-day GitHub setup is fine; exchange-side stop orders are
not needed.**

## Decisions

- Live bot: exits are processed first, then free slots go to the
  highest-scoring signals (test added).
- Keep the daily GitHub Actions schedule.
