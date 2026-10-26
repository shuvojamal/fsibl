"""Research round 43: does capping each position's size help? (50 / 33 / 20% of equity)

Risk-based sizing buys more of a coin when its stop is close. In quiet
markets that can put a large share of the account into one coin: with 1%
risk and a stop 3% away, one position is a third of the account, and a
gap through the stop (an exchange outage, a crash between daily closes)
would hurt far more than 1%. A cap on each position's value limits that
tail risk; the question is what it costs.

Cases: no cap (live), and caps at 50%, 33% and 20% of equity per position,
for steady (8 x 0.5%) and growth (8 x 1%), 6 of 8 checks, top 15; round 12's
simulator and costs; round 21's six close times x two halves (12 cells).
(A quick version ran in an earlier scheduled session that failed before
saving; this is the proper record.)

Pass bar, decided before running: a cap is recommended only if it has a
higher Sharpe than no cap in at least 9 of 12 cells, OR it costs no more
than 1 point of 2022-26 median return while making the worst drop shallower.
"""
import os as _os
import pickle
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns21 = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r43'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns21)
raw, unpack, OFFSETS, H, ROOT = ns21['raw'], ns21['unpack'], ns21['OFFSETS'], ns21['H'], ns21['ROOT']
from tradebot.opportunity import Opportunity, OppParams

src12 = open(_os.path.join(HERE, 'research12.py')).read()
head = src12[:src12.index('\nL = []')]
old = "qty = min(eq_now * risk / (entry - plan.stop), cash * (1 - fee) / entry)"
assert old in head
head = head.replace(old, "qty = min(eq_now * risk / (entry - plan.stop), cash * (1 - fee) / entry, eq_now * CAP / entry)")


def simulate(data):
    pk = _os.path.join(ROOT, 'research', 'data', '_r43_tmp.pkl')
    pickle.dump(data, open(pk, 'wb'))
    ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r43b', 'CAP': 1e9}
    exec(head.replace("cache = _os.path.join(OUT, 'daily_long.pkl')", f"cache = {pk!r}"), ns)
    _os.remove(pk)
    return ns


START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("steady 8 x 0.5%", 0.005), ("growth 8 x 1%", 0.01)]
CAPS = [("no cap (live)", 1e9), ("cap 50%", 0.50), ("cap 33%", 0.33), ("cap 20%", 0.20)]
res = {}
for o in OFFSETS:
    ns = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for sname, r in SETUPS:
            for cname, cap in CAPS:
                ns['CAP'] = cap
                curve, trades = ns['run'](make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=r, start=s, end=e)
                res[(o, half, sname, cname)] = ns['metrics'](curve, trades)

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
med = lambda xs: sorted(xs)[len(xs) // 2]
L = ["Per-position size cap (share of equity); 8 slots, 6 checks, top 15; medians over six close times\n"]
for sname, _ in SETUPS:
    ref = CAPS[0][0]
    rb = med([res[(o, "2022-26", sname, ref)]['cagr'] for o in OFFSETS]); rd = med([res[(o, "2022-26", sname, ref)]['dd'] for o in OFFSETS])
    L += [sname, f"  {'cap':14s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 18-21':>9s} {'DD 22-26':>9s} {'wins vs no cap':>15s} verdict"]
    for cname, _ in CAPS:
        a = [res[(o, "2018-21", sname, cname)] for o in OFFSETS]; b = [res[(o, "2022-26", sname, cname)] for o in OFFSETS]
        w = sum(res[(o, h, sname, cname)]['sharpe'] > res[(o, h, sname, ref)]['sharpe'] for o, h in cells)
        ret, dd = med([m['cagr'] for m in b]), med([m['dd'] for m in b])
        ok = cname != ref and (w >= 9 or (ret >= rb - 0.01 and dd > rd))
        L.append(f"  {cname:14s} {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f} {ret:+8.1%} / {med([m['sharpe'] for m in b]):4.2f} "
                 f"{med([m['dd'] for m in a]):9.1%} {dd:9.1%} {'' if cname == ref else f'{w} of 12':>15s} {'REF' if cname == ref else ('PASS' if ok else '')}")
    L.append("")
print("\n".join(L))
