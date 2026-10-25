"""Research round 35: what does living with each set-up feel like? A risk profile.

Before real money the owner should know not just the yearly return but how
the bad stretches look: the worst day, week and month, how long the account
stays below its previous high, and how often a month or a year loses money.
Steady (8 slots x 0.5% risk) and growth (8 x 1%), both 6 of 8 checks, top 15,
round 12's simulator and costs, on round 21's six close times x two halves
(12 cells). Reported as the median cell and the worst cell, because the worst
is what a new account could get.

Pass bar, decided before running (a suitability test, not a rule change):
a set-up is "fit for a first real-money account" if, in its WORST cell of the
12, the worst 30-day loss is no deeper than -20%, the longest time below a
previous high is no more than 18 months, and no calendar year loses more
than 15%.
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r35'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams

START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("steady 8 x 0.5%", 0.005), ("growth 8 x 1%", 0.01)]


def profile(curve):
    eq = [e for _, e in curve]; ts = [t for t, _ in curve]
    worst = lambda n: min(eq[i] / eq[i - n] - 1 for i in range(n, len(eq)))
    peak, start, longest, under10 = eq[0], 0, 0, 0
    for i, e in enumerate(eq):
        if e >= peak:
            peak, start = e, i
        else:
            longest = max(longest, i - start)
            under10 += e < peak * 0.9
    months, years = {}, {}
    for t, e in curve:
        d = datetime.fromtimestamp(t / 1000, timezone.utc)
        months.setdefault((d.year, d.month), [e, e])[1] = e
        years.setdefault(d.year, [e, e])[1] = e
    mret = [b / a - 1 for a, b in months.values()]
    # a year's return runs from the previous year's last value
    ylist = sorted(years.items()); yret = []
    prev = eq[0]
    for y, (a, b) in ylist:
        yret.append(b / prev - 1); prev = b
    return dict(day=worst(1), week=worst(7), month=worst(30), longest=longest, under10=under10 / len(eq),
                lose_m=sum(r < 0 for r in mret) / len(mret), worst_year=min(yret), years=dict(zip([y for y, _ in ylist], yret)))


res = {}
full = {}
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    for sname, r in SETUPS:
        make = lambda: Opportunity(OppParams(min_score=6))
        for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
            curve, _ = run(make=make, max_open=8, risk=r, start=s, end=e)
            res[(o, half, sname)] = profile(curve)
        curve, _ = run(make=make, max_open=8, risk=r, start=START + o * H)
        full[(o, sname)] = profile(curve)

med = lambda xs: sorted(xs)[len(xs) // 2]
cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
L = ["Risk profile, 8 slots, 6 checks, top 15; per half: median cell / worst cell of the six close times\n"]
for sname, _ in SETUPS:
    L.append(sname)
    L.append(f"  {'':18s} {'2018-21 med / worst':>22s} {'2022-26 med / worst':>22s}")
    rows = [("worst day", "day", "%"), ("worst 7 days", "week", "%"), ("worst 30 days", "month", "%"),
            ("longest under high", "longest", "d"), ("time >10% under", "under10", "%"), ("losing months", "lose_m", "%")]
    for label, k, u in rows:
        cols = []
        for h in ("2018-21", "2022-26"):
            vs = [res[(o, h, sname)][k] for o in OFFSETS]
            bad = max(vs) if k in ("longest", "under10", "lose_m") else min(vs)
            f = (lambda v: f"{v:.0f} d") if u == "d" else (lambda v: f"{v:+.1%}" if k in ("day", "week", "month") else f"{v:.0%}")
            cols.append(f"{f(med(vs))} / {f(bad)}")
        L.append(f"  {label:18s} {cols[0]:>22s} {cols[1]:>22s}")
    # calendar years over the whole period, median and worst across close times
    yrs = sorted(full[(OFFSETS[0], sname)]['years'])
    L.append("  calendar years (whole run 2018-03 to now; median / worst close time):")
    L.append("   " + "  ".join(f"{y}: {med([full[(o, sname)]['years'].get(y, 0) for o in OFFSETS]):+.0%}/{min(full[(o, sname)]['years'].get(y, 0) for o in OFFSETS):+.0%}" for y in yrs))
    w_month = min(res[c + (sname,)]['month'] for c in cells)
    w_long = max(res[c + (sname,)]['longest'] for c in cells)
    w_year = min(full[(o, sname)]['worst_year'] for o in OFFSETS)
    ok = w_month >= -0.20 and w_long <= 548 and w_year >= -0.15
    L.append(f"  worst cell: 30-day {w_month:+.1%}, longest under high {w_long} days ({w_long / 30.4:.0f} months), worst year {w_year:+.1%}"
             f" -> {'FIT for a first real-money account' if ok else 'NOT fit by the pre-set bar'}")
    L.append("")
print("\n".join(L))
