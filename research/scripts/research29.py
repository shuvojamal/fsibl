"""Research round 29: with 8 slots x 0.5% risk, how many coins, and 5 or 6 checks?

Round 28's winner (8 positions at 0.5% risk) fills more slots, so it may
benefit from a wider list of coins to choose from, and round 24's "6 of 8
checks" may combine differently with it. Tested on round 21's six close
times x two halves (12 cells):
  universe top 10 / 15 / 20 / 25 (by trailing-90-day volume, as live)
  x min_score 5 / 6, all with 8 slots and 0.5% risk.
Reference: the live set-up (top 15, 5 checks, 5 slots, 1% risk).

Pass bar, decided before running: a combination is recommended over round
28's base (top 15, 5 checks, 8 x 0.5%) only if it has the higher Sharpe in
at least 9 of 12 cells and a 2022-26 median drawdown no deeper than the
base's plus 3 points. Universe sizes above 30 aren't possible with this
data (30 coins). Same simulator and costs as round 12.
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r29'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams

START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
CASES = [("LIVE: top15, 5 checks, 5 x 1%", dict(top=15, ms=5, n=5, r=0.01))]
CASES += [(f"top{t}, {ms} checks, 8 x 0.5%", dict(top=t, ms=ms, n=8, r=0.005)) for ms in (5, 6) for t in (10, 15, 20, 25)]
BASE = "top15, 5 checks, 8 x 0.5%"

res = {}
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for name, c in CASES:
            curve, trades = run(make=lambda ms=c['ms']: Opportunity(OppParams(min_score=ms)), top=c['top'],
                                max_open=c['n'], risk=c['r'], start=s, end=e)
            res[(o, half, name)] = metrics(curve, trades)

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
med = lambda xs: sorted(xs)[len(xs) // 2]
base_dd = med([res[(o, "2022-26", BASE)]['dd'] for o in OFFSETS])
L = ["Universe size x checks, with 8 slots at 0.5% risk; medians over six close times\n",
     f"{'case':32s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 22-26':>9s} {'trades 22-26':>12s} {'wins vs base':>12s} verdict"]
for name, c in CASES:
    a = [res[(o, "2018-21", name)] for o in OFFSETS]; b = [res[(o, "2022-26", name)] for o in OFFSETS]
    w = sum(res[(o, h, name)]['sharpe'] > res[(o, h, BASE)]['sharpe'] for o, h in cells)
    dd = med([m['dd'] for m in b])
    verdict = "BASE" if name == BASE else ("PASS" if w >= 9 and dd >= base_dd - 0.03 and not name.startswith("LIVE") else "")
    L.append(f"{name:32s} {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f} "
             f"{med([m['cagr'] for m in b]):+8.1%} / {med([m['sharpe'] for m in b]):4.2f} {dd:9.1%} {med([m['n'] for m in b]):12d} "
             f"{'' if name == BASE else f'{w} of 12':>12s} {verdict}")
print("\n".join(L))
