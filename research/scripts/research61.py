"""Research round 61: pause new buys after a losing streak?

Losses cluster (round 48): when the market turns, several positions stop
out together and new signals often fail too. The VPS testnet has had six
losers in seven trades since 2026-10-23. A "cool-off" rule: after K losing
exits in a row, take no new positions for D days (exits keep working). It
could avoid more losses in a bad patch, or miss the rebound.

Cases: no pause (live); K=3, D=7; K=3, D=14; K=5, D=7; K=5, D=14. Steady and
growth, 6 of 8 checks, top 15, round 12's simulator and costs, round 21's
six close times x two halves.

Pass bar, decided before running (with round 53's effect-size floor): a
rule is recommended only if it has a higher Sharpe than no pause in at
least 9 of 12 cells AND adds at least 0.5 points of 2022-26 median return
or makes the median worst drop at least 1 point shallower, on both set-ups.
"""
import os as _os
import pickle
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns21 = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r61'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns21)
raw, unpack, OFFSETS, H, ROOT = ns21['raw'], ns21['unpack'], ns21['OFFSETS'], ns21['H'], ns21['ROOT']
from tradebot.opportunity import Opportunity, OppParams

src12 = open(_os.path.join(HERE, 'research12.py')).read()
head = src12[:src12.index('\nL = []')]
a = "            trades.append(dict(t=t, pnl=p, r=p / q['risk'], sym=s, bull=q['bull']))\n"
assert head.count(a) == 1
head = head.replace(a, a + "            ST['streak'] = ST['streak'] + 1 if p <= 0 else 0\n"
                           "            if K and ST['streak'] >= K:\n                ST['until'] = t + D * 86_400_000; ST['streak'] = 0\n")
b = "            if i is None or s in pos or len(pos) >= max_open:\n"
assert head.count(b) == 1
head = head.replace(b, "            if t < ST['until']:\n                continue\n" + b)
c = "    cash, pos, pending, curve, trades = capital, {}, {}, [], []\n"
assert head.count(c) == 1
head = head.replace(c, c + "    ST.update(streak=0, until=0)\n")


def simulate(data):
    pk = _os.path.join(ROOT, 'research', 'data', '_r61_tmp.pkl')
    pickle.dump(data, open(pk, 'wb'))
    ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r61b', 'K': 0, 'D': 0, 'ST': {}}
    exec(head.replace("cache = _os.path.join(OUT, 'daily_long.pkl')", f"cache = {pk!r}"), ns)
    _os.remove(pk)
    return ns


START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("steady 8 x 0.5%", 0.005), ("growth 8 x 1%", 0.01)]
CASES = [("no pause (live)", 0, 0), ("3 losses -> 7 days", 3, 7), ("3 losses -> 14 days", 3, 14), ("5 losses -> 7 days", 5, 7), ("5 losses -> 14 days", 5, 14)]
res = {}
for o in OFFSETS:
    ns = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for sname, r in SETUPS:
            for cname, k, d in CASES:
                ns['K'], ns['D'] = k, d
                res[(o, half, sname, cname)] = ns['metrics'](*ns['run'](make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=r, start=s, end=e))

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
med = lambda xs: sorted(xs)[len(xs) // 2]
L = ["Pause new buys after a losing streak; 8 slots, 6 checks, top 15; medians over six close times\n"]
ok_all = {c[0]: True for c in CASES[1:]}
for sname, _ in SETUPS:
    ref = CASES[0][0]
    rb = med([res[(o, "2022-26", sname, ref)]['cagr'] for o in OFFSETS]); rd = med([res[(o, "2022-26", sname, ref)]['dd'] for o in OFFSETS])
    L += [sname, f"  {'rule':22s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 22-26':>9s} {'trades 22-26':>12s} {'wins vs live':>13s} pass?"]
    for cname, _, _ in CASES:
        a = [res[(o, "2018-21", sname, cname)] for o in OFFSETS]; b = [res[(o, "2022-26", sname, cname)] for o in OFFSETS]
        w = sum(res[(o, h, sname, cname)]['sharpe'] > res[(o, h, sname, ref)]['sharpe'] for o, h in cells)
        ret, dd = med([m['cagr'] for m in b]), med([m['dd'] for m in b])
        ok = cname != ref and w >= 9 and (ret >= rb + 0.005 or dd >= rd + 0.01)
        if cname != ref:
            ok_all[cname] = ok_all[cname] and ok
        L.append(f"  {cname:22s} {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f} {ret:+8.1%} / {med([m['sharpe'] for m in b]):4.2f} "
                 f"{dd:9.1%} {med([m['n'] for m in b]):12d} {'' if cname == ref else f'{w} of 12':>13s} {'' if cname == ref else ('yes' if ok else 'no')}")
    L.append("")
passed = [c for c, ok in ok_all.items() if ok]
L.append(f"verdict: {'PASS: ' + ', '.join(passed) if passed else 'FAIL: no pause after losing streaks'}")
print("\n".join(L))
