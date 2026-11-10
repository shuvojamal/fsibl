"""Research round 58: tighten the trailing stop once a trade is well in profit?

Round 27 tested one trail width for every trade (3 x ATR is fine). A common
refinement: keep the wide 3 x ATR trail while a trade is young, then tighten
it once the trade is well in profit, to keep more of big winners when a
trend finally breaks. Profit is measured in R (multiples of the initial
risk, entry minus the 2 x ATR stop).

Cases: live (3 x ATR always); tighten to 2 x ATR after +3R; to 2 x ATR after
+5R; to 2.5 x ATR after +3R. Steady (8 x 0.5%) and growth (8 x 1%), 6 of 8
checks, top 15, round 12's simulator and costs, round 21's six close times x
two halves.

Pass bar, decided before running (with round 53's effect-size floor): a
variant is recommended only if it has a higher Sharpe than live in at least
9 of 12 cells AND adds at least 0.5 points of 2022-26 median return or makes
the median worst drop at least 1 point shallower, on both set-ups.
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r58'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams


class Ratchet(Opportunity):
    """3 x ATR trail until the best close is `after_r` R above entry, then `tight` x ATR."""
    def __init__(self, after_r, tight):
        super().__init__(OppParams(min_score=6)); self.after_r, self.tight = after_r, tight

    def signal(self, i):
        plan = super().signal(i)
        if plan:
            self.entry_px, self.r0 = self.closes[i], self.closes[i] - plan.stop
        return plan

    def update_stop(self, i, stop):
        if self.atr[i] is None:
            return stop
        self.peak = max(self.peak or 0.0, self.closes[i])
        mult = self.p.trail_atr
        if getattr(self, "r0", 0) > 0 and self.peak >= self.entry_px + self.after_r * self.r0:
            mult = self.tight
        return max(stop, self.peak - mult * self.atr[i])


START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("steady 8 x 0.5%", 0.005), ("growth 8 x 1%", 0.01)]
CASES = [("live (3 x ATR always)", None), ("2 x ATR after +3R", (3, 2.0)), ("2 x ATR after +5R", (5, 2.0)), ("2.5 x ATR after +3R", (3, 2.5))]
res = {}
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for sname, r in SETUPS:
            for cname, c in CASES:
                make = (lambda: Opportunity(OppParams(min_score=6))) if c is None else (lambda c=c: Ratchet(*c))
                res[(o, half, sname, cname)] = metrics(*run(make=make, max_open=8, risk=r, start=s, end=e))

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
med = lambda xs: sorted(xs)[len(xs) // 2]
L = ["Tighter trail once in profit; 8 slots, 6 checks, top 15; medians over six close times\n"]
ok_all = {c[0]: True for c in CASES[1:]}
for sname, _ in SETUPS:
    ref = CASES[0][0]
    rb = med([res[(o, "2022-26", sname, ref)]['cagr'] for o in OFFSETS]); rd = med([res[(o, "2022-26", sname, ref)]['dd'] for o in OFFSETS])
    L += [sname, f"  {'exit':24s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 22-26':>9s} {'avg R 22-26':>11s} {'wins vs live':>13s} pass?"]
    for cname, _ in CASES:
        a = [res[(o, "2018-21", sname, cname)] for o in OFFSETS]; b = [res[(o, "2022-26", sname, cname)] for o in OFFSETS]
        w = sum(res[(o, h, sname, cname)]['sharpe'] > res[(o, h, sname, ref)]['sharpe'] for o, h in cells)
        ret, dd = med([m['cagr'] for m in b]), med([m['dd'] for m in b])
        ok = cname != ref and w >= 9 and (ret >= rb + 0.005 or dd >= rd + 0.01)
        if cname != ref:
            ok_all[cname] = ok_all[cname] and ok
        L.append(f"  {cname:24s} {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f} {ret:+8.1%} / {med([m['sharpe'] for m in b]):4.2f} "
                 f"{dd:9.1%} {med([m['exp_r'] for m in b]):+11.2f} {'' if cname == ref else f'{w} of 12':>13s} {'' if cname == ref else ('yes' if ok else 'no')}")
    L.append("")
passed = [c for c, ok in ok_all.items() if ok]
L.append(f"verdict: {'PASS: ' + ', '.join(passed) if passed else 'FAIL: keep the 3 x ATR trail for the whole trade'}")
print("\n".join(L))
