"""Research round 60: is the testnet's first three weeks within what the backtest expects?

The VPS testnet (growth set-up, 8 x 1%, 6 of 8 checks) started on
2026-10-23 at 5,000 USDT and stood at 4,700.28 on 2026-11-12 (-6.0% in 20
days; six closed trades, five losers). Rounds 48 and 51 say losing starts
are common; this places the actual result in the backtest's distribution
of 20-day returns, so a bad start is read for what it is.

Method: every 20-day window (daily step) of the growth set-up's equity
curve, round 12's simulator and costs, round 21's six close times,
2018-03 .. 2026-10 and the 2022-26 part. Reported: the percentile of -6.0%,
the 5th percentile and the chance of a 20-day loss of 6% or more.

Pass bar (a consistency test, decided before running): the live start is
"consistent with the backtest" if -6.0% is above the 5th percentile of
20-day windows in 2022-26. Below it would call for checking execution.
"""
import csv
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..'))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r60'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams

rows = list(csv.DictReader(open(_os.path.join(ROOT, 'binance_state', 'equity.csv'))))
live = float(rows[-1]['equity']) / 5000.0 - 1
t0 = datetime.strptime(rows[0]['time'][:10], "%Y-%m-%d"); t1 = datetime.strptime(rows[-1]['time'][:10], "%Y-%m-%d")
DAYS = (t1 - t0).days

START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
W = {"all": [], "2022-26": []}
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    curve, _ = run(make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=0.01, start=START + o * H)
    eq = [e for _, e in curve]; ts = [t for t, _ in curve]
    for i in range(len(eq) - DAYS):
        x = eq[i + DAYS] / eq[i] - 1
        W["all"].append(x)
        if ts[i] >= SPLIT:
            W["2022-26"].append(x)

pc = lambda xs, q: sorted(xs)[int(q * len(xs))]
L = [f"Live testnet (growth): {rows[0]['time'][:10]} -> {rows[-1]['time'][:10]} ({DAYS} days): {live:+.1%}\n"]
ok = None
for k in ("all", "2022-26"):
    xs = W[k]
    pct = sum(x <= live for x in xs) / len(xs)
    L.append(f"{k:8s} {len(xs)} windows of {DAYS} days: the live result is at the {pct:.0%} percentile; "
             f"5th pct {pc(xs, .05):+.1%}, median {pc(xs, .5):+.1%}; chance of {live:+.1%} or worse: {pct:.0%}")
    if k == "2022-26":
        ok = live > pc(xs, .05)
L.append(f"\nverdict: {'CONSISTENT with the backtest' if ok else 'BELOW the 5th percentile: check execution'}")
print("\n".join(L))
