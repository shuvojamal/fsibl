"""Research round 51: what should a 90-day demo show? (reading the owner's test period)

The owner runs the bots on demo/testnet for about 90 days before any real
money. Ninety days is short for a strategy that wins 41% of trades and makes
its money in a few strong months, so the demo result alone could mislead
either way. This measures the spread of 90-day results the live rules
produce, so the demo can be read against it.

Method: daily equity curves of steady (8 x 0.5%) and growth (8 x 1%), 6 of 8
checks, top 15, round 12's simulator and costs, on round 21's six close
times, 2018-03 .. 2026-10 (and the 2022-26 part separately); every 90-day
window (daily step). Reported: chance of a loss, median, 10th / 5th / 90th
percentiles, and the worst window.

Pass bar (an expectation test, decided before running): a losing 90-day
demo is "not evidence against the strategy" if at least 25% of 90-day
windows lose money. The 5th percentile is reported as the red-flag line: a
demo below it would be worth investigating (execution, bugs, data).
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r51'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams

START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("steady 8 x 0.5%", 0.005), ("growth 8 x 1%", 0.01)]
W = {(s, p): [] for s, _ in SETUPS for p in ("all", "2022-26")}
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    for sname, r in SETUPS:
        curve, _ = run(make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=r, start=START + o * H)
        eq = [e for _, e in curve]; ts = [t for t, _ in curve]
        for i in range(len(eq) - 90):
            x = eq[i + 90] / eq[i] - 1
            W[(sname, "all")].append(x)
            if ts[i] >= SPLIT:
                W[(sname, "2022-26")].append(x)

pc = lambda xs, q: sorted(xs)[min(len(xs) - 1, int(q * len(xs)))]
L = ["Every 90-day window (daily step), six close times pooled\n",
     f"{'set-up':16s} {'period':8s} {'windows':>8s} {'P(loss)':>8s} {'5th pct':>8s} {'10th':>7s} {'median':>7s} {'90th':>7s} {'worst':>7s}"]
verdict = True
for sname, _ in SETUPS:
    for p in ("all", "2022-26"):
        xs = W[(sname, p)]
        pl = sum(x < 0 for x in xs) / len(xs)
        L.append(f"{sname:16s} {p:8s} {len(xs):8d} {pl:8.0%} {pc(xs, .05):+8.1%} {pc(xs, .10):+7.1%} {pc(xs, .5):+7.1%} {pc(xs, .9):+7.1%} {min(xs):+7.1%}")
        if p == "2022-26":
            verdict = verdict and pl >= 0.25
L.append(f"\nverdict: {'a losing 90-day demo is NOT evidence against the strategy' if verdict else 'losing 90-day windows are rarer than assumed'}")
print("\n".join(L))
