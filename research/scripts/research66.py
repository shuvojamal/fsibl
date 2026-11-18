"""Research round 66: how long does the bot normally sit with no positions?

The VPS testnet has held nothing since 2026-11-13 and had no buy signal
for five days (six coins stopped out since late October). The owner has
asked before why the bot isn't buying. This measures, in the backtest, how
often the account is completely flat, how long flat spells last, and how
much of the time it holds 0, 1-3, 4-7 or all 8 positions.

Method: steady (8 x 0.5%), 6 of 8 checks, top 15, round 12's simulator,
round 21's six close times, 2018-03 .. 2026-10; the number of open positions
recorded each day.

Pass bar (an expectation test, decided before running): a flat spell of
5 days counts as "normal" if at least 25% of all flat spells last 5 days or
longer.
"""
import os as _os
import pickle
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns21 = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r66'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns21)
raw, unpack, OFFSETS, H, ROOT = ns21['raw'], ns21['unpack'], ns21['OFFSETS'], ns21['H'], ns21['ROOT']
from tradebot.opportunity import Opportunity, OppParams

src12 = open(_os.path.join(HERE, 'research12.py')).read()
head = src12[:src12.index('\nL = []')]
a = "        curve.append((t, eq_of(t)))\n"
assert head.count(a) == 1
head = head.replace(a, a + "        COUNTS.append(len(pos))\n")


def simulate(data):
    pk = _os.path.join(ROOT, 'research', 'data', '_r66_tmp.pkl')
    pickle.dump(data, open(pk, 'wb'))
    ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r66b', 'COUNTS': []}
    exec(head.replace("cache = _os.path.join(OUT, 'daily_long.pkl')", f"cache = {pk!r}"), ns)
    _os.remove(pk)
    return ns


START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
counts, spells = [], []
for o in OFFSETS:
    ns = simulate(unpack(raw[o]))
    ns['run'](make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=0.005, start=START + o * H)
    c = ns['COUNTS']; counts += c
    run_len = 0
    for x in c + [1]:
        if x == 0:
            run_len += 1
        elif run_len:
            spells.append(run_len); run_len = 0

n = len(counts)
band = lambda lo, hi: sum(lo <= x <= hi for x in counts) / n
spells.sort()
ge5 = sum(s >= 5 for s in spells) / len(spells)
L = [f"Open positions per day, steady set-up, six close times pooled ({n} days)\n",
     f"  no positions (flat): {band(0, 0):.0%} of days",
     f"  1-3 positions: {band(1, 3):.0%};  4-7: {band(4, 7):.0%};  all 8: {band(8, 8):.0%}",
     f"\nFlat spells: {len(spells)}; median {spells[len(spells) // 2]} days; 75th percentile {spells[int(.75 * len(spells))]}; "
     f"90th {spells[int(.9 * len(spells))]}; longest {spells[-1]} days",
     f"  spells lasting 5 days or more: {ge5:.0%}; 30 days or more: {sum(s >= 30 for s in spells) / len(spells):.0%}",
     f"\nverdict: a 5-day flat spell is {'NORMAL' if ge5 >= 0.25 else 'unusual'}"]
print("\n".join(L))
