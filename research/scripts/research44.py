"""Research round 44: does "skip the 200-day trend check" also hold on the growth set-up?

Round 33 found that treating the trend_up check as always passed beat the
live rules on the steady set-up (8 x 0.5%): 10 of 12 cells, and both halves
of round 12's 55-coin pool. It is an app switch, off by default. The VPS
testnet runs the growth set-up (8 x 1%), so before anyone turns it on there,
check the same idea at 1% risk.

Cases: live (6 of 8) vs trend_up removed, growth set-up, top 15, round 12's
simulator and costs, on (a) round 21's six close times x two halves and
(b) round 12's 55-coin pool, two halves.

Pass bar, decided before running (same as round 33): higher Sharpe than live
in at least 10 of 12 cells, a 2022-26 median worst drop no more than 3 points
deeper, AND higher Sharpe in both halves of the 55-coin pool.
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r44'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams

START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
CASES = [("live (6 of 8)", ()), ("trend_up removed", ("trend_up",))]
RISK = 0.01
res = {}
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for name, ig in CASES:
            res[(o, half, name)] = metrics(*run(make=lambda ig=ig: Opportunity(OppParams(min_score=6, ignore=ig)), max_open=8, risk=RISK, start=s, end=e))

cells = [(o, h) for o in OFFSETS for h in ("2018-21", "2022-26")]
med = lambda xs: sorted(xs)[len(xs) // 2]
REF, ALT = CASES[0][0], CASES[1][0]
L = ["Growth set-up (8 x 1%, top 15): skip the 200-day trend check; medians over six close times\n",
     f"{'variant':20s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 18-21':>9s} {'DD 22-26':>9s} {'trades 22-26':>12s}"]
for name, _ in CASES:
    a = [res[(o, "2018-21", name)] for o in OFFSETS]; b = [res[(o, "2022-26", name)] for o in OFFSETS]
    L.append(f"{name:20s} {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f} {med([m['cagr'] for m in b]):+8.1%} / "
             f"{med([m['sharpe'] for m in b]):4.2f} {med([m['dd'] for m in a]):9.1%} {med([m['dd'] for m in b]):9.1%} {med([m['n'] for m in b]):12d}")
w1 = sum(res[(o, "2018-21", ALT)]['sharpe'] > res[(o, "2018-21", REF)]['sharpe'] for o in OFFSETS)
w2 = sum(res[(o, "2022-26", ALT)]['sharpe'] > res[(o, "2022-26", REF)]['sharpe'] for o in OFFSETS)
dd_ok = med([res[(o, "2022-26", ALT)]['dd'] for o in OFFSETS]) >= med([res[(o, "2022-26", REF)]['dd'] for o in OFFSETS]) - 0.03
L.append(f"\nSharpe wins for 'trend_up removed': {w1 + w2} of 12 ({w1}/{w2}); 2022-26 drop within 3 pts: {dd_ok}")

# second data set: round 12's 55-coin pool
src12 = open(_os.path.join(HERE, 'research12.py')).read()
ns12 = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r44d'}
exec(src12[:src12.index('\nL = []')], ns12)
L += ["", "Round 12's 55-coin pool:", f"{'variant':20s} {'2018-21 ret / Sh / DD':>24s} {'2022-26 ret / Sh / DD':>24s}"]
sh = {}
for name, ig in CASES:
    row = f"{name:20s}"
    for half, (s, e) in (("2018-21", (START, SPLIT)), ("2022-26", (SPLIT, None))):
        m = ns12['metrics'](*ns12['run'](make=lambda ig=ig: Opportunity(OppParams(min_score=6, ignore=ig)), max_open=8, risk=RISK, start=s, end=e))
        sh[(name, half)] = m['sharpe']
        row += f" {m['cagr']:+9.1%} / {m['sharpe']:4.2f} / {m['dd']:6.1%}"
    L.append(row)
pool_ok = all(sh[(ALT, h)] > sh[(REF, h)] for h in ("2018-21", "2022-26"))
ok = w1 + w2 >= 10 and dd_ok and pool_ok
L.append(f"\nverdict: {'PASS on the growth set-up too' if ok else 'FAIL on the growth set-up'} "
         f"(cells {w1 + w2}/12, drop ok {dd_ok}, 55-coin both halves {pool_ok})")
print("\n".join(L))
