"""Research round 67: does it matter when a real account starts?

The owner plans to start real money after the demo period. The strategy
is currently in a losing stretch (testnet -6.1% since 2026-10-23, matching
the backtest, round 65). Is a 1-year result better when an account starts
after the strategy has fallen from its high (buying its dip), or after a
strong run (at a high)?

Method: steady set-up (8 x 0.5%, 6 of 8, top 15), round 12's simulator,
round 21's six close times; for every start day, the strategy's distance
below its previous equity high on that day, and the account's return over
the next 365 days. Starts grouped: at/near a high (within 2%), 2-5% below,
5-10% below, more than 10% below. Reported for 2018-21 and 2022-25 starts.

Pass bar, decided before running: "start after a drawdown" is recommended
if the median 1-year return of starts 5%+ below the high beats starts at a
high by at least 3 points in BOTH halves. Otherwise: the start date doesn't
matter in a useful way.
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r67'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams

START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
GROUPS = [("at/near a high (<2% below)", 0.0, 0.02), ("2-5% below", 0.02, 0.05), ("5-10% below", 0.05, 0.10), (">10% below", 0.10, 9)]
obs = {}
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    curve, _ = run(make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=0.005, start=START + o * H)
    eq = [e for _, e in curve]; ts = [t for t, _ in curve]
    peak = 0.0
    for i in range(len(eq) - 365):
        peak = max(peak, eq[i])
        dd = 1 - eq[i] / peak
        half = "2018-21" if ts[i] < SPLIT else "2022-25"
        obs.setdefault(half, []).append((dd, eq[i + 365] / eq[i] - 1))

med = lambda xs: sorted(xs)[len(xs) // 2] if xs else float('nan')
L = ["1-year return by how far the strategy was below its high on the start day; steady set-up, six close times pooled\n",
     f"{'start':28s} | {'2018-21: starts  median 1y  P(loss)':>36s} | {'2022-25: starts  median 1y  P(loss)':>36s}"]
table = {}
for gname, lo, hi in GROUPS:
    row = f"{gname:28s} |"
    for h in ("2018-21", "2022-25"):
        xs = [r for d, r in obs[h] if lo <= d < hi]
        table[(gname, h)] = med(xs)
        row += f" {len(xs):15d} {med(xs):+11.1%} {sum(r < 0 for r in xs) / max(1, len(xs)):8.0%} |"
    L.append(row)
ok = True
for h in ("2018-21", "2022-25"):
    deep = med([r for d, r in obs[h] if d >= 0.05])
    ok = ok and deep >= table[(GROUPS[0][0], h)] + 0.03
L.append(f"\nverdict: {'START AFTER A DRAWDOWN helps' if ok else 'the start timing does not matter in a useful way'}")
print("\n".join(L))
