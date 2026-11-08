"""Research round 56: spread the money over neighbouring settings (an ensemble)?

Round 55 found the live settings sit on a peak for 2022-26: nearby fast-EMA
and ATR lengths earned 3-4 points a year less. The usual remedy for tuning
luck is not to bet on one exact setting: split the capital equally over a
grid of neighbours, so the result is the average of the hill, not its top.

Ensemble: nine equal sub-accounts, fast EMA 15/20/25 x ATR 10/14/20, each
the steady set-up (8 slots, 0.5% risk, 6 of 8 checks, top 15) on a ninth of
the capital (equity = sum of the nine; no rebalancing). Compared with the
live setting alone (20, 14), on round 21's six close times x two halves,
round 12's simulator and costs. Note: nine sub-accounts trading the same
coins means the real account would hold the same coin in several of them;
in practice this is one position sized as the average. Fine for a backtest
of the idea.

Pass bar, decided before running: the ensemble is recommended if its
2022-26 median return is within 1 point of live AND its worst cell
(lowest Sharpe of the 12) is higher than live's worst cell (it is the
robustness that is wanted, not a higher peak). Reported also: how the
ensemble compares with the median single neighbour.
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r56'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams

START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
GRID = [(f, a) for f in (15, 20, 25) for a in (10, 14, 20)]
res = {}
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        curves, singles = [], []
        for f, a in GRID:
            curve, trades = run(make=lambda f=f, a=a: Opportunity(OppParams(min_score=6, fast=f, atr_period=a)), max_open=8, risk=0.005,
                                capital=10000.0 / len(GRID), start=s, end=e)
            curves.append(curve)
            m = metrics(curve, trades, capital=10000.0 / len(GRID))
            singles.append(m)
            if (f, a) == (20, 14):
                res[(o, half, "live")] = m
        ens = [(t, sum(c[k][1] for c in curves)) for k, (t, _) in enumerate(curves[0])]
        res[(o, half, "ensemble")] = metrics(ens, [])
        res[(o, half, "median neighbour")] = {k: sorted(m[k] for m in singles)[len(singles) // 2] for k in ("cagr", "sharpe", "dd")}

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
med = lambda xs: sorted(xs)[len(xs) // 2]
L = ["Nine-setting ensemble (fast EMA 15/20/25 x ATR 10/14/20, a ninth of the capital each) vs the live setting; steady 8 x 0.5%\n",
     f"{'':20s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 22-26':>9s} {'worst-cell Sharpe':>18s}"]
for name in ("live", "ensemble", "median neighbour"):
    a = [res[(o, "2018-21", name)] for o in OFFSETS]; b = [res[(o, "2022-26", name)] for o in OFFSETS]
    worst = min(res[(o, h, name)]['sharpe'] for o, h in cells)
    L.append(f"{name:20s} {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f} {med([m['cagr'] for m in b]):+8.1%} / "
             f"{med([m['sharpe'] for m in b]):4.2f} {med([m['dd'] for m in b]):9.1%} {worst:18.2f}")
lb = med([res[(o, "2022-26", "live")]['cagr'] for o in OFFSETS]); eb = med([res[(o, "2022-26", "ensemble")]['cagr'] for o in OFFSETS])
lw = min(res[c + ("live",)]['sharpe'] for c in cells); ew = min(res[c + ("ensemble",)]['sharpe'] for c in cells)
w = sum(res[c + ("ensemble",)]['sharpe'] > res[c + ("live",)]['sharpe'] for c in cells)
L.append(f"\nensemble beats live's Sharpe in {w} of 12 cells")
L.append(f"verdict: {'PASS: recommend the ensemble' if eb >= lb - 0.01 and ew > lw else 'FAIL: keep the single live setting'}")
print("\n".join(L))
