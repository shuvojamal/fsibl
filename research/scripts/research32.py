"""Research round 32: what does idle cash earn? Flexible savings on unused USDT.

With 8 slots and 0.5-1% risk, much of the account sits in USDT between
trades. Binance (Simple Earn, flexible) and OKX (Simple Earn) pay interest
on USDT that can be withdrawn at any time; rates have ranged from about 1%
to over 10% a year and move with demand, so this tests 2%, 4% and 6%.

Method: round 12's simulator on round 21's six close times x two halves,
top 15, 6 checks, 8 slots, steady (0.5%) and growth (1%). The cash balance
earns the yearly rate as daily interest (added to cash, so it compounds and
is available for the next entry). Also reports the average share of the
account held as cash.

Pass bar, decided before running: worth building if, at 4%, it adds at
least 1 point a year to the 2022-26 median return without a deeper median
worst drop. Not counted: platform risk of the savings product, and that
neither demo account can test it (the exchanges' demo/testnet have no Earn).
"""
import os as _os
import pickle
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns21 = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r32'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns21)
raw, unpack, OFFSETS, H, ROOT = ns21['raw'], ns21['unpack'], ns21['OFFSETS'], ns21['H'], ns21['ROOT']
from tradebot.opportunity import Opportunity, OppParams

src12 = open(_os.path.join(HERE, 'research12.py')).read()
head = src12[:src12.index('\nL = []')]
old = "        curve.append((t, eq_of(t)))\n"
assert head.count(old) == 1
head = head.replace(old, "        cash *= (1 + YIELD) ** (1 / 365)\n        e = eq_of(t); CASHSHARE.append(cash / e)\n        curve.append((t, e))\n")


def simulate(data):
    pk = _os.path.join(ROOT, 'research', 'data', '_r32_tmp.pkl')
    pickle.dump(data, open(pk, 'wb'))
    ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r32b', 'YIELD': 0.0, 'CASHSHARE': []}
    exec(head.replace("cache = _os.path.join(OUT, 'daily_long.pkl')", f"cache = {pk!r}"), ns)
    _os.remove(pk)
    return ns


START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("steady 8 x 0.5%", 0.005), ("growth 8 x 1%", 0.01)]
YIELDS = (0.0, 0.02, 0.04, 0.06)
make = lambda: Opportunity(OppParams(min_score=6))

res, share = {}, {}
for o in OFFSETS:
    ns = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for sname, r in SETUPS:
            for y in YIELDS:
                ns['YIELD'] = y; ns['CASHSHARE'].clear()
                curve, trades = ns['run'](make=make, max_open=8, risk=r, start=s, end=e)
                res[(o, half, sname, y)] = ns['metrics'](curve, trades)
                if y == 0:
                    share[(o, half, sname)] = sum(ns['CASHSHARE']) / len(ns['CASHSHARE'])

med = lambda xs: sorted(xs)[len(xs) // 2]
L = ["Interest on idle USDT; 8 slots, 6 checks, top 15; medians over six close times\n"]
for sname, _ in SETUPS:
    L.append(f"{sname}: average cash share 2018-21 {med([share[(o, '2018-21', sname)] for o in OFFSETS]):.0%}, "
             f"2022-26 {med([share[(o, '2022-26', sname)] for o in OFFSETS]):.0%}")
    L.append(f"  {'yield':>6s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 22-26':>9s} {'gain 22-26':>11s} verdict")
    b0 = med([res[(o, '2022-26', sname, 0.0)]['cagr'] for o in OFFSETS]); d0 = med([res[(o, '2022-26', sname, 0.0)]['dd'] for o in OFFSETS])
    for y in YIELDS:
        a = [res[(o, "2018-21", sname, y)] for o in OFFSETS]; b = [res[(o, "2022-26", sname, y)] for o in OFFSETS]
        rb, dd = med([m['cagr'] for m in b]), med([m['dd'] for m in b])
        v = "REF" if y == 0 else ("PASS" if y == 0.04 and rb - b0 >= 0.01 and dd >= d0 else "")
        L.append(f"  {y:6.0%} {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f} "
                 f"{rb:+8.1%} / {med([m['sharpe'] for m in b]):4.2f} {dd:9.1%} {'' if y == 0 else f'{(rb - b0) * 100:+.1f} pts':>11s} {v}")
    L.append("")
print("\n".join(L))
