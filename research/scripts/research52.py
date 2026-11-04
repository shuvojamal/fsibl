"""Research round 52: does a 300-500 USDT account still trade like the backtest?

The owner plans to start real money with 300-500 USDT. Risk-based sizing at
0.5-1% risk makes small positions (median ~5-9% of equity, round 45): 15-45
USDT on 300. Binance refuses orders below its minimum notional (5 USDT on
most USDT pairs), and the bot then skips the buy ("risk-sized order below
the exchange minimum"). This measures how often that happens and what it
costs.

Method: round 12's simulator with a starting capital of 300 / 500 USDT and
a rule that skips any buy below MIN_NOTIONAL (5 USDT; also 10 USDT as a
stricter check). Steady (8 x 0.5%) and growth (8 x 1%), 6 of 8 checks, top
15, round 21's six close times x two halves. Compared with the same set-up
without a minimum (equal to any large account).

Pass bar, decided before running: a 300 USDT start is "fine" for a set-up if
at most 5% of buys are skipped AND its 2022-26 median yearly return is
within 1 point of the no-minimum run.
"""
import os as _os
import pickle
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns21 = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r52'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns21)
raw, unpack, OFFSETS, H, ROOT = ns21['raw'], ns21['unpack'], ns21['OFFSETS'], ns21['H'], ns21['ROOT']
from tradebot.opportunity import Opportunity, OppParams

src12 = open(_os.path.join(HERE, 'research12.py')).read()
head = src12[:src12.index('\nL = []')]
a = "            if qty > 0:\n"
assert head.count(a) == 1
head = head.replace(a, "            if qty * entry < MINN:\n                SKIPPED[0] += 1; continue\n            TAKEN[0] += 1\n" + a)


def simulate(data):
    pk = _os.path.join(ROOT, 'research', 'data', '_r52_tmp.pkl')
    pickle.dump(data, open(pk, 'wb'))
    ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r52b', 'MINN': 0.0, 'SKIPPED': [0], 'TAKEN': [0]}
    exec(head.replace("cache = _os.path.join(OUT, 'daily_long.pkl')", f"cache = {pk!r}"), ns)
    _os.remove(pk)
    return ns


START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("steady 8 x 0.5%", 0.005), ("growth 8 x 1%", 0.01)]
CASES = [("no minimum (large account)", 10000.0, 0.0), ("300 USDT, min 5", 300.0, 5.0), ("300 USDT, min 10", 300.0, 10.0),
         ("500 USDT, min 5", 500.0, 5.0)]
res, skip = {}, {}
for o in OFFSETS:
    ns = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for sname, r in SETUPS:
            for cname, cap, mn in CASES:
                ns['MINN'] = mn; ns['SKIPPED'][0] = 0; ns['TAKEN'][0] = 0
                curve, trades = ns['run'](make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=r, capital=cap, start=s, end=e)
                res[(o, half, sname, cname)] = ns['metrics'](curve, trades, capital=cap)
                k = (sname, cname); a_, b_ = skip.get(k, (0, 0)); skip[k] = (a_ + ns['SKIPPED'][0], b_ + ns['TAKEN'][0] + ns['SKIPPED'][0])

med = lambda xs: sorted(xs)[len(xs) // 2]
L = ["Small accounts vs Binance's minimum order (skipped buys below it); 8 slots, 6 checks, top 15; medians over six close times\n"]
verdict = {}
for sname, _ in SETUPS:
    ref = CASES[0][0]; rb = med([res[(o, "2022-26", sname, ref)]['cagr'] for o in OFFSETS])
    L += [sname, f"  {'account':28s} {'buys skipped':>13s} {'2018-21 ret':>12s} {'2022-26 ret / Sh':>17s} {'DD 22-26':>9s}"]
    for cname, cap, mn in CASES:
        b = [res[(o, "2022-26", sname, cname)] for o in OFFSETS]; a = [res[(o, "2018-21", sname, cname)] for o in OFFSETS]
        sk, tot = skip[(sname, cname)]
        L.append(f"  {cname:28s} {sk / max(1, tot):13.1%} {med([m['cagr'] for m in a]):+12.1%} {med([m['cagr'] for m in b]):+8.1%} / {med([m['sharpe'] for m in b]):4.2f} {med([m['dd'] for m in b]):9.1%}")
        if cname == "300 USDT, min 5":
            verdict[sname] = sk / max(1, tot) <= 0.05 and med([m['cagr'] for m in b]) >= rb - 0.01
    L.append(f"  -> 300 USDT start {'FINE' if verdict[sname] else 'NOT fine by the bar'}\n")
print("\n".join(L))
