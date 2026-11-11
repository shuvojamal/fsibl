"""Research round 59: how far past the stop do losing exits land?

Stops act at the daily close and sell at the next open, so a losing exit
usually fills below the stop: ZEC on 2026-11-11 sold at 1042.95 against a
1062.46 stop, TRX on 2026-10-31 at 0.3248 against 0.3352. The planned loss
of a stop-out is 1R (the initial risk); anything beyond is overshoot. This
measures how big that overshoot is in the backtest, so live losses can be
judged against it (and as a further input on the value of a resting
backstop order, rounds 45/49).

Method: every trade of the steady set-up (8 x 0.5%, 6 of 8, top 15), round
12's simulator and costs, round 21's six close times, 2018-03 .. 2026-10.
Losing trades' results in R: median, share worse than -1.2R / -1.5R / -2R,
and the worst.

Pass bar (an acceptability test, decided before running): daily-close stops
are acceptable if the median losing trade is no worse than -1.1R and fewer
than 5% of losing trades are worse than -1.5R.
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r59'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams

START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
losers = []
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    _, trades = run(make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=0.005, start=START + o * H)
    losers += [x['r'] for x in trades if x['r'] <= 0]

losers.sort()
n = len(losers)
med = losers[n // 2]
share = lambda k: sum(r < k for r in losers) / n
ok = med >= -1.1 and share(-1.5) < 0.05
L = [f"Losing trades (steady set-up, six close times pooled): {n}",
     f"  median {med:+.2f}R; 10th percentile {losers[int(.1 * n)]:+.2f}R; 1st percentile {losers[int(.01 * n)]:+.2f}R; worst {losers[0]:+.2f}R",
     f"  worse than -1.2R: {share(-1.2):.1%}; worse than -1.5R: {share(-1.5):.1%}; worse than -2R: {share(-2.0):.1%}",
     f"  (includes trades whose trail had risen: those lose less than 1R)",
     f"\nverdict: {'ACCEPTABLE: overshoot past the stop is small and rare' if ok else 'NOT acceptable by the pre-set bar'}"]
print("\n".join(L))
