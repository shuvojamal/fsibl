"""Research round 47: a minimum stop distance (3% / 5%) for very calm coins.

Round 45 showed big positions come only from very calm coins (TRX), whose
2 x ATR stop can sit ~2% below the entry, so 1% risk buys ~50% of the
account. A size cap didn't help (rounds 43/45). Alternative: never place the
initial stop closer than a floor (3% or 5% below the entry). For calm coins
the stop is wider, so the same risk buys a smaller position, and the trade
has more room before being stopped out; for normal coins nothing changes.

Cases: no floor (live), floor 3%, floor 5%; growth (8 x 1%) and steady
(8 x 0.5%), 6 of 8 checks, top 15, round 12's simulator and costs, round
21's six close times x two halves (12 cells). The trailing stop is unchanged.

Pass bar, decided before running (as for the caps): a floor is recommended
only if it has a higher Sharpe than no floor in at least 9 of 12 cells, OR
costs at most 1 point of 2022-26 median return while making the median
worst drop shallower.
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r47'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams


class Floored(Opportunity):
    """Initial stop no closer than `floor` below the signal close."""
    def __init__(self, floor):
        super().__init__(OppParams(min_score=6)); self.floor = floor

    def signal(self, i):
        plan = super().signal(i)
        if plan and self.floor:
            plan.stop = min(plan.stop, self.closes[i] * (1 - self.floor))
        return plan


START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("growth 8 x 1%", 0.01), ("steady 8 x 0.5%", 0.005)]
FLOORS = [("no floor (live)", 0.0), ("floor 3%", 0.03), ("floor 5%", 0.05)]
res = {}
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for sname, r in SETUPS:
            for fname, f in FLOORS:
                res[(o, half, sname, fname)] = metrics(*run(make=lambda f=f: Floored(f), max_open=8, risk=r, start=s, end=e))

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
med = lambda xs: sorted(xs)[len(xs) // 2]
L = ["Minimum initial stop distance; 8 slots, 6 checks, top 15; medians over six close times\n"]
for sname, _ in SETUPS:
    ref = FLOORS[0][0]
    rb = med([res[(o, "2022-26", sname, ref)]['cagr'] for o in OFFSETS]); rd = med([res[(o, "2022-26", sname, ref)]['dd'] for o in OFFSETS])
    L += [sname, f"  {'floor':16s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 18-21':>9s} {'DD 22-26':>9s} {'wins vs live':>13s} verdict"]
    for fname, _ in FLOORS:
        a = [res[(o, "2018-21", sname, fname)] for o in OFFSETS]; b = [res[(o, "2022-26", sname, fname)] for o in OFFSETS]
        w = sum(res[(o, h, sname, fname)]['sharpe'] > res[(o, h, sname, ref)]['sharpe'] for o, h in cells)
        ret, dd = med([m['cagr'] for m in b]), med([m['dd'] for m in b])
        ok = fname != ref and (w >= 9 or (ret >= rb - 0.01 and dd > rd))
        L.append(f"  {fname:16s} {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f} {ret:+8.1%} / {med([m['sharpe'] for m in b]):4.2f} "
                 f"{med([m['dd'] for m in a]):9.1%} {dd:9.1%} {'' if fname == ref else f'{w} of 12':>13s} {'REF' if fname == ref else ('PASS' if ok else '')}")
    L.append("")
print("\n".join(L))
