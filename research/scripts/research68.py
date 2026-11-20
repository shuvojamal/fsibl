"""Research round 68: are buy signals from weekend closes worse?

Crypto trades seven days a week, but weekend markets are thinner: volumes
are lower and moves can be erratic, which may make the volume check and
breakouts on Saturday/Sunday closes less reliable. Calendar effects are a
classic source of false findings, so the bar is strict.

Cases: live; no new entries from Saturday or Sunday closes (exits work as
usual). Steady and growth, 6 of 8 checks, top 15, round 12's simulator,
round 21's six close times x two halves.

Pass bar, decided before running (strict, calendar effect): recommended only
if it has a higher Sharpe in at least 10 of 12 cells AND adds at least 0.5
points of 2022-26 median return or makes the drop 1 point shallower, on
both set-ups.
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r68'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams


class NoWeekend(Opportunity):
    def prepare(self, candles):
        super().prepare(candles)
        self.wd = [datetime.fromtimestamp(c.close_time / 1000, timezone.utc).weekday() for c in candles]
        return self

    def signal(self, i):
        return None if self.wd[i] >= 5 else super().signal(i)


START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("steady 8 x 0.5%", 0.005), ("growth 8 x 1%", 0.01)]
CASES = [("live", Opportunity), ("no weekend entries", NoWeekend)]
res = {}
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for sname, r in SETUPS:
            for cname, cls in CASES:
                res[(o, half, sname, cname)] = metrics(*run(make=lambda cls=cls: cls(OppParams(min_score=6)), max_open=8, risk=r, start=s, end=e))

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
med = lambda xs: sorted(xs)[len(xs) // 2]
L = ["Weekend-close entries; 8 slots, 6 checks, top 15; medians over six close times\n"]
ok_all = True
for sname, _ in SETUPS:
    ref = CASES[0][0]
    rb = med([res[(o, "2022-26", sname, ref)]['cagr'] for o in OFFSETS]); rd = med([res[(o, "2022-26", sname, ref)]['dd'] for o in OFFSETS])
    L += [sname, f"  {'entries':20s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 22-26':>9s} {'trades 22-26':>12s} {'wins vs live':>13s} pass?"]
    for cname, _ in CASES:
        a = [res[(o, "2018-21", sname, cname)] for o in OFFSETS]; b = [res[(o, "2022-26", sname, cname)] for o in OFFSETS]
        w = sum(res[(o, h, sname, cname)]['sharpe'] > res[(o, h, sname, ref)]['sharpe'] for o, h in cells)
        ret, dd = med([m['cagr'] for m in b]), med([m['dd'] for m in b])
        ok = cname != ref and w >= 10 and (ret >= rb + 0.005 or dd >= rd + 0.01)
        if cname != ref:
            ok_all = ok_all and ok
        L.append(f"  {cname:20s} {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f} {ret:+8.1%} / {med([m['sharpe'] for m in b]):4.2f} "
                 f"{dd:9.1%} {med([m['n'] for m in b]):12d} {'' if cname == ref else f'{w} of 12':>13s} {'' if cname == ref else ('yes' if ok else 'no')}")
    L.append("")
L.append(f"verdict: {'PASS: skip weekend entries' if ok_all else 'FAIL: weekend entries are fine'}")
print("\n".join(L))
