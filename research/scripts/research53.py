"""Research round 53: limit new buys per day (spread entries over time)?

The VPS testnet bought ETH and ZEC on the same day (2026-11-05). Crypto
coins move together, so several entries on one day are partly one bet on
that day's market; if it turns, they stop out together (round 48: losses
cluster). Capping new entries per day spreads them over time, at the cost
of skipping or delaying some signals (a skipped coin can still enter on a
later day if it signals again).

Cases: no limit (live), at most 1, 2 or 3 new buys per day (highest score
first, as live); steady (8 x 0.5%) and growth (8 x 1%), 6 of 8 checks, top
15, round 12's simulator and costs, round 21's six close times x two halves.

Pass bar, decided before running (as for caps and floors): a limit is
recommended only if it has a higher Sharpe than no limit in at least 9 of
12 cells, OR costs at most 1 point of 2022-26 median return while making
the median worst drop shallower.
"""
import os as _os
import pickle
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns21 = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r53'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns21)
raw, unpack, OFFSETS, H, ROOT = ns21['raw'], ns21['unpack'], ns21['OFFSETS'], ns21['H'], ns21['ROOT']
from tradebot.opportunity import Opportunity, OppParams

src12 = open(_os.path.join(HERE, 'research12.py')).read()
head = src12[:src12.index('\nL = []')]
a = "        for s, plan in buys:\n"
assert head.count(a) == 1
head = head.replace(a, "        new_today = 0\n" + a + "            if new_today >= PER_DAY:\n                break\n")
b = "                cash -= qty * entry / (1 - fee)\n"
assert head.count(b) == 1
head = head.replace(b, b + "                new_today += 1\n")


def simulate(data):
    pk = _os.path.join(ROOT, 'research', 'data', '_r53_tmp.pkl')
    pickle.dump(data, open(pk, 'wb'))
    ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r53b', 'PER_DAY': 99}
    exec(head.replace("cache = _os.path.join(OUT, 'daily_long.pkl')", f"cache = {pk!r}"), ns)
    _os.remove(pk)
    return ns


START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("steady 8 x 0.5%", 0.005), ("growth 8 x 1%", 0.01)]
LIMITS = [("no limit (live)", 99), ("max 1 per day", 1), ("max 2 per day", 2), ("max 3 per day", 3)]
res = {}
for o in OFFSETS:
    ns = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for sname, r in SETUPS:
            for lname, k in LIMITS:
                ns['PER_DAY'] = k
                res[(o, half, sname, lname)] = ns['metrics'](*ns['run'](make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=r, start=s, end=e))

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
med = lambda xs: sorted(xs)[len(xs) // 2]
L = ["New buys per day limited; 8 slots, 6 checks, top 15; medians over six close times\n"]
for sname, _ in SETUPS:
    ref = LIMITS[0][0]
    rb = med([res[(o, "2022-26", sname, ref)]['cagr'] for o in OFFSETS]); rd = med([res[(o, "2022-26", sname, ref)]['dd'] for o in OFFSETS])
    L += [sname, f"  {'limit':16s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 18-21':>9s} {'DD 22-26':>9s} {'trades 22-26':>12s} {'wins vs live':>13s} verdict"]
    for lname, _ in LIMITS:
        a = [res[(o, "2018-21", sname, lname)] for o in OFFSETS]; b = [res[(o, "2022-26", sname, lname)] for o in OFFSETS]
        w = sum(res[(o, h, sname, lname)]['sharpe'] > res[(o, h, sname, ref)]['sharpe'] for o, h in cells)
        ret, dd = med([m['cagr'] for m in b]), med([m['dd'] for m in b])
        ok = lname != ref and (w >= 9 or (ret >= rb - 0.01 and dd > rd))
        L.append(f"  {lname:16s} {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f} {ret:+8.1%} / {med([m['sharpe'] for m in b]):4.2f} "
                 f"{med([m['dd'] for m in a]):9.1%} {dd:9.1%} {med([m['n'] for m in b]):12d} {'' if lname == ref else f'{w} of 12':>13s} {'REF' if lname == ref else ('PASS' if ok else '')}")
    L.append("")
print("\n".join(L))
