"""Research round 28: portfolio sizing, max positions x risk per trade.

The two settings the owner controls in the app that change the shape of
the results most: how many positions may be open at once (max_open) and
how much of the account each trade risks (risk). Round 16 hinted that 8
slots beat 5 (Sharpe 1.13 vs 0.97) on one data set. Tested here on round
21's six close times x two halves (12 cells), with max_open 3/5/8/10 and
risk 0.5/1/1.5%.

Pass bar, decided before running: a combination is recommended over the
live (5 slots, 1%) only if it has the higher Sharpe in at least 9 of 12
cells AND its median worst drawdown in 2022-26 is no deeper than live's
plus 5 points. Same simulator, universe and costs as round 12. Note: more
slots and more risk mean more capital at work, so higher returns with
higher risk are expected; the Sharpe and drawdown columns are the point.
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r28'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']

START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
COMBOS = [(n, r) for n in (3, 5, 8, 10) for r in (0.005, 0.01, 0.015)]
LIVE = (5, 0.01)

res = {}
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for n, r in COMBOS:
            curve, trades = run(max_open=n, risk=r, start=s, end=e)
            res[(o, half, n, r)] = metrics(curve, trades)

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
med = lambda xs: sorted(xs)[len(xs) // 2]
live_dd = med([res[(o, "2022-26") + LIVE]['dd'] for o in OFFSETS])
L = ["Max positions x risk per trade, six close times x two halves (30 coins, costs included); medians over the six close times\n",
     f"{'slots':>5s} {'risk':>5s}  {'2018-21 ret / Sh':>17s}  {'2022-26 ret / Sh':>17s}  {'DD 22-26':>9s}  {'Sharpe wins vs live':>20s}  verdict"]
for n, r in COMBOS:
    a = [res[(o, "2018-21", n, r)] for o in OFFSETS]; b = [res[(o, "2022-26", n, r)] for o in OFFSETS]
    w = sum(res[(o, h, n, r)]['sharpe'] > res[(o, h) + LIVE]['sharpe'] for o, h in cells)
    dd = med([m['dd'] for m in b])
    live = (n, r) == LIVE
    verdict = "LIVE" if live else ("PASS" if w >= 9 and dd >= live_dd - 0.05 else "")
    L.append(f"{n:5d} {r:5.1%}  {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f}  "
             f"{med([m['cagr'] for m in b]):+8.1%} / {med([m['sharpe'] for m in b]):4.2f}  {dd:9.1%}  "
             f"{'' if live else f'{w} of 12':>20s}  {verdict}")
print("\n".join(L))
