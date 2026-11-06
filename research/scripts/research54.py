"""Research round 54: wait for a second day's confirmation before buying?

The VPS testnet bought ETH on 2026-11-05 and was stopped out the next day
(-49.02 USDT). A common idea: only buy if the signal still holds at the
next daily close, filtering out one-day blips. The cost: entries one day
later (higher prices in real trends) and some missed trades.

Cases: live (buy at the open after the first signal); "confirm 2 days"
(buy only when the coin also passed 6 of 8 checks on the previous close,
i.e. two signal closes in a row). Steady and growth, top 15, round 12's
simulator and costs, round 21's six close times x two halves.

Pass bar, decided before running, with the effect-size floor round 53
called for: recommended only if it has a higher Sharpe in at least 9 of 12
cells AND either adds at least 0.5 points of 2022-26 median return or makes
the median worst drop at least 1 point shallower.
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r54'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams


class Confirm2(Opportunity):
    """Signal only when the previous close also scored 6+ (two signal closes in a row)."""
    def signal(self, i):
        plan = super().signal(i)
        if plan is None or i < 1:
            return None
        prev = self.checks(i - 1)
        if prev is None or sum(ok for _, ok in prev) < self.p.min_score:
            return None
        return plan


START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("steady 8 x 0.5%", 0.005), ("growth 8 x 1%", 0.01)]
CASES = [("live (first signal)", Opportunity), ("confirm 2 days", Confirm2)]
res = {}
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for sname, r in SETUPS:
            for cname, cls in CASES:
                curve, trades = run(make=lambda cls=cls: cls(OppParams(min_score=6)), max_open=8, risk=r, start=s, end=e)
                res[(o, half, sname, cname)] = metrics(curve, trades)

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
med = lambda xs: sorted(xs)[len(xs) // 2]
L = ["Second-day confirmation before buying; 8 slots, 6 checks, top 15; medians over six close times\n"]
for sname, _ in SETUPS:
    ref = CASES[0][0]
    rb = med([res[(o, "2022-26", sname, ref)]['cagr'] for o in OFFSETS]); rd = med([res[(o, "2022-26", sname, ref)]['dd'] for o in OFFSETS])
    L += [sname, f"  {'entry':22s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 22-26':>9s} {'trades 22-26':>12s} {'win 22-26':>9s} {'wins vs live':>13s} verdict"]
    for cname, _ in CASES:
        a = [res[(o, "2018-21", sname, cname)] for o in OFFSETS]; b = [res[(o, "2022-26", sname, cname)] for o in OFFSETS]
        w = sum(res[(o, h, sname, cname)]['sharpe'] > res[(o, h, sname, ref)]['sharpe'] for o, h in cells)
        ret, dd = med([m['cagr'] for m in b]), med([m['dd'] for m in b])
        ok = cname != ref and w >= 9 and (ret >= rb + 0.005 or dd >= rd + 0.01)
        L.append(f"  {cname:22s} {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f} {ret:+8.1%} / {med([m['sharpe'] for m in b]):4.2f} "
                 f"{dd:9.1%} {med([m['n'] for m in b]):12d} {med([m['win'] for m in b]):9.0%} {'' if cname == ref else f'{w} of 12':>13s} {'REF' if cname == ref else ('PASS' if ok else 'FAIL')}")
    L.append("")
print("\n".join(L))
