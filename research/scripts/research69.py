"""Research round 69: would a much smaller coin list (top 2 or top 5) do as well?

A first real account might be simpler and safer trading only the biggest,
most liquid coins (fewer odd coins, deeper order books). Round 29 tested
lists of 10-25 coins; this tests the top 2 (usually BTC and ETH) and top 5
by traded volume (re-ranked quarterly as live), against the live top 15.

Steady and growth, 8 slots, 6 of 8 checks, round 12's simulator and costs,
round 21's six close times x two halves.

Pass bar, decided before running: a smaller list is recommended if its
Sharpe is at least as high as the top 15's in 9 of 12 cells AND its 2022-26
median return is no more than 2 points lower (simplicity is worth a little).
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r69'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams

START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("steady 8 x 0.5%", 0.005), ("growth 8 x 1%", 0.01)]
TOPS = [("top 15 (live)", 15), ("top 5", 5), ("top 2", 2)]
res = {}
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for sname, r in SETUPS:
            for tname, k in TOPS:
                res[(o, half, sname, tname)] = metrics(*run(make=lambda: Opportunity(OppParams(min_score=6)), top=k, max_open=8, risk=r, start=s, end=e))

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
med = lambda xs: sorted(xs)[len(xs) // 2]
L = ["Coin list size; 8 slots, 6 checks; medians over six close times\n"]
ok_all = {t[0]: True for t in TOPS[1:]}
for sname, _ in SETUPS:
    ref = TOPS[0][0]
    rb = med([res[(o, "2022-26", sname, ref)]['cagr'] for o in OFFSETS])
    L += [sname, f"  {'list':14s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 22-26':>9s} {'trades 22-26':>12s} {'Sharpe >= live':>15s} pass?"]
    for tname, _ in TOPS:
        a = [res[(o, "2018-21", sname, tname)] for o in OFFSETS]; b = [res[(o, "2022-26", sname, tname)] for o in OFFSETS]
        w = sum(res[(o, h, sname, tname)]['sharpe'] >= res[(o, h, sname, ref)]['sharpe'] for o, h in cells)
        ret = med([m['cagr'] for m in b])
        ok = tname != ref and w >= 9 and ret >= rb - 0.02
        if tname != ref:
            ok_all[tname] = ok_all[tname] and ok
        L.append(f"  {tname:14s} {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f} {ret:+8.1%} / {med([m['sharpe'] for m in b]):4.2f} "
                 f"{med([m['dd'] for m in b]):9.1%} {med([m['n'] for m in b]):12d} {'' if tname == ref else f'{w} of 12':>15s} {'' if tname == ref else ('yes' if ok else 'no')}")
    L.append("")
L.append("verdict: " + "; ".join(f"{t}: {'PASS' if ok else 'fail'}" for t, ok in ok_all.items()))
print("\n".join(L))
