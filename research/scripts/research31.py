"""Research round 31: pyramiding, add to positions that are already winning.

The owner wants more than ~15%/yr. Trend followers often add to winners
instead of risking more on every new entry: a losing trade stays a single
small bet, and only trades that are already working get bigger. Here an
open position may get one or two "adds" at the next day's open, once its
close is +1R (and +2R) above the entry, where R is the entry's initial
risk per coin (entry - 2xATR stop). Each add risks the same % of equity as
an entry, measured to the position's current trailing stop; it needs free
cash and no new slot. The stop stays the single trailing stop for the
whole position. New entries are filled first; adds use what cash is left.

Cases, on round 21's six close times x two halves (12 cells), top 15,
6 of 8 checks, for both recommended set-ups (steady 8 x 0.5%, growth
8 x 1%):
  no adds (reference)
  1 add at +1R
  1 add at +2R
  2 adds at +1R and +2R

Pass bar, decided before running: an add rule is recommended over the
same set-up without adds only if it has the higher Sharpe in at least 9 of
12 cells AND a 2022-26 median worst drop no more than 3 points deeper.
Same costs as round 12.
"""
import os as _os
import pickle
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns21 = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r31'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns21)
raw, unpack, OFFSETS, H, ROOT = ns21['raw'], ns21['unpack'], ns21['OFFSETS'], ns21['H'], ns21['ROOT']
from tradebot.opportunity import Opportunity, OppParams

src12 = open(_os.path.join(HERE, 'research12.py')).read()
head = src12[:src12.index('\nL = []')]


def patch(old, new):
    global head
    assert head.count(old) == 1, old
    head = head.replace(old, new)


# remember the entry and its initial risk per coin
patch("pos[s] = dict(qty=qty, cost=qty * entry / (1 - fee), stop=plan.stop, peak=entry,",
      "pos[s] = dict(qty=qty, cost=qty * entry / (1 - fee), stop=plan.stop, peak=entry, entry=entry, r0=entry - plan.stop, adds=0,")
# execute adds after the new entries, before the pending list is cleared
patch("        pending = {}\n",
      """        for s in [s for s, (a, _) in pending.items() if a == 'add']:
            i = idx[s].get(t)
            if i is None or s not in pos:
                continue
            q = pos[s]; px = data[s][i].open * (1 + slip)
            if px <= q['stop']:
                continue
            add = min(eq_now * risk / (px - q['stop']), cash * (1 - fee) / px)
            if add * px < 10:
                continue
            cash -= add * px / (1 - fee)
            q['qty'] += add; q['cost'] += add * px / (1 - fee); q['risk'] += add * (px - q['stop']); q['adds'] += 1
        pending = {}
""")
# signal an add when the close reaches the next +kR level
patch("                q['stop'] = st.update_stop(i, q['stop'])\n",
      """                q['stop'] = st.update_stop(i, q['stop'])
                if q['adds'] < len(ADD_AT) and c.close >= q['entry'] + ADD_AT[q['adds']] * q['r0']:
                    pending[s] = ('add', None)
""")


def simulate(data):
    pk = _os.path.join(ROOT, 'research', 'data', '_r31_tmp.pkl')
    pickle.dump(data, open(pk, 'wb'))
    ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r31b', 'ADD_AT': ()}
    exec(head.replace("cache = _os.path.join(OUT, 'daily_long.pkl')", f"cache = {pk!r}"), ns)
    _os.remove(pk)
    return ns


START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("steady 8 x 0.5%", 0.005), ("growth 8 x 1%", 0.01)]
ADDS = [("no adds", ()), ("1 add at +1R", (1,)), ("1 add at +2R", (2,)), ("2 adds at +1R, +2R", (1, 2))]
make = lambda: Opportunity(OppParams(min_score=6))

res = {}
for o in OFFSETS:
    ns = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for sname, r in SETUPS:
            for aname, at in ADDS:
                ns['ADD_AT'] = at
                curve, trades = ns['run'](make=make, max_open=8, risk=r, start=s, end=e)
                res[(o, half, sname, aname)] = ns['metrics'](curve, trades)

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
med = lambda xs: sorted(xs)[len(xs) // 2]
L = ["Pyramiding (adds to winning positions); 8 slots, 6 checks, top 15; medians over six close times\n"]
for sname, _ in SETUPS:
    ref_dd = med([res[(o, "2022-26", sname, "no adds")]['dd'] for o in OFFSETS])
    L += [sname, f"  {'adds':20s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 18-21':>9s} {'DD 22-26':>9s} {'wins vs no adds':>16s} verdict"]
    for aname, _ in ADDS:
        a = [res[(o, "2018-21", sname, aname)] for o in OFFSETS]; b = [res[(o, "2022-26", sname, aname)] for o in OFFSETS]
        w = sum(res[(o, h, sname, aname)]['sharpe'] > res[(o, h, sname, "no adds")]['sharpe'] for o, h in cells)
        dd = med([m['dd'] for m in b])
        ref = aname == "no adds"
        ok = not ref and w >= 9 and dd >= ref_dd - 0.03
        L.append(f"  {aname:20s} {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f} "
                 f"{med([m['cagr'] for m in b]):+8.1%} / {med([m['sharpe'] for m in b]):4.2f} {med([m['dd'] for m in a]):9.1%} {dd:9.1%} "
                 f"{'' if ref else f'{w} of 12':>16s} {'REF' if ref else ('PASS' if ok else '')}")
    L.append("")
print("\n".join(L))
