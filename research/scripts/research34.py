"""Research round 34: is 2 x ATR the right distance for the stop at entry?

The initial stop (entry - 2 x ATR(14)) was picked in round 1 on hourly
candles and never re-tested on the daily set-up the bot runs now. It sets
two things at once: where a failed trade is cut, and the position size
(risk-based sizing buys less when the stop is further away). The 3 x ATR
trailing stop takes over as soon as it is higher, so initial stops of
3 x ATR or wider are mostly cut back by the trail at the first close
(4 x is included to show that).

Cases: initial stop 1.5 / 2 (live) / 2.5 / 3 / 4 x ATR, trail fixed at
3 x ATR, steady set-up (8 slots, 0.5% risk, 6 of 8 checks, top 15), round
12's simulator and costs, round 21's six close times x two halves (12 cells).

Pass bar, decided before running: a different multiple is recommended
only if it has a higher Sharpe than 2 x ATR in at least 9 of 12 cells AND
a 2022-26 median worst drop no more than 3 points deeper. Four challengers,
so one pass at exactly 9/12 would be weak evidence (luck bar).
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r34'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams

START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
MULTS = (1.5, 2.0, 2.5, 3.0, 4.0)
REF = 2.0

res = {}
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for m in MULTS:
            curve, trades = run(make=lambda m=m: Opportunity(OppParams(min_score=6, stop_atr=m)), max_open=8, risk=0.005, start=s, end=e)
            res[(o, half, m)] = metrics(curve, trades)

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
med = lambda xs: sorted(xs)[len(xs) // 2]
ref_dd = med([res[(o, "2022-26", REF)]['dd'] for o in OFFSETS])
L = ["Initial stop distance (trail fixed at 3 x ATR); 8 slots, 0.5% risk, 6 checks, top 15; medians over six close times\n",
     f"{'stop':>8s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 18-21':>9s} {'DD 22-26':>9s} {'trades 22-26':>12s} {'win 22-26':>9s} {'avg R':>6s} {'wins vs 2x':>11s} {'(18-21/22-26)':>13s} verdict"]
for m in MULTS:
    a = [res[(o, "2018-21", m)] for o in OFFSETS]; b = [res[(o, "2022-26", m)] for o in OFFSETS]
    w1 = sum(res[(o, "2018-21", m)]['sharpe'] > res[(o, "2018-21", REF)]['sharpe'] for o in OFFSETS)
    w2 = sum(res[(o, "2022-26", m)]['sharpe'] > res[(o, "2022-26", REF)]['sharpe'] for o in OFFSETS)
    dd = med([x['dd'] for x in b])
    v = "REF (live)" if m == REF else ("PASS" if w1 + w2 >= 9 and dd >= ref_dd - 0.03 else "")
    L.append(f"{m:6.1f} x {med([x['cagr'] for x in a]):+8.1%} / {med([x['sharpe'] for x in a]):4.2f} "
             f"{med([x['cagr'] for x in b]):+8.1%} / {med([x['sharpe'] for x in b]):4.2f} {med([x['dd'] for x in a]):9.1%} {dd:9.1%} "
             f"{med([x['n'] for x in b]):12d} {med([x['win'] for x in b]):9.0%} {med([x['exp_r'] for x in b]):+6.2f} "
             f"{'' if m == REF else f'{w1 + w2} of 12':>11s} {'' if m == REF else f'{w1}/{w2}':>13s} {v}")
print("\n".join(L))
