"""Research round 63: is the current market unusually hard for the strategy?

The live accounts have started badly (testnet -6.1% in three weeks, five of
six trades lost). Rounds 48/51/60 say that is within normal luck. This
asks a different question: how did the strategy do in the most recent
months of the backtest data, and is that unusual for it? If recent months
were a rare bad patch, the live start reflects the market, not the bot.

Method: steady and growth (8 slots, 6 of 8, top 15), round 12's simulator
and costs, round 21's six close times up to the end of the cached data;
returns over the last 3, 6 and 12 months, placed among all windows of the
same length since 2018-03 (percentile).

Pass bar (descriptive, decided before running): recent conditions count as
"normal" if the last 6 months' median return sits between the 10th and
90th percentile of all 6-month windows; below the 10th, "unusually hard".
"""
import os as _os
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r63'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns)
raw, unpack, simulate, OFFSETS, H = ns['raw'], ns['unpack'], ns['simulate'], ns['OFFSETS'], ns['H']
from tradebot.opportunity import Opportunity, OppParams

START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SETUPS = [("steady 8 x 0.5%", 0.005), ("growth 8 x 1%", 0.01)]
LENS = [("3 months", 91), ("6 months", 182), ("12 months", 365)]
out = {}
end_date = None
for o in OFFSETS:
    run, metrics = simulate(unpack(raw[o]))
    for sname, r in SETUPS:
        curve, _ = run(make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=r, start=START + o * H)
        eq = [e for _, e in curve]
        end_date = datetime.fromtimestamp(curve[-1][0] / 1000, timezone.utc).strftime("%Y-%m-%d")
        for lname, n in LENS:
            allw = [eq[i + n] / eq[i] - 1 for i in range(len(eq) - n)]
            last = eq[-1] / eq[-1 - n] - 1
            pct = sum(x <= last for x in allw) / len(allw)
            out.setdefault((sname, lname), []).append((last, pct, sorted(allw)))

med = lambda xs: sorted(xs)[len(xs) // 2]
L = [f"Most recent months of the backtest (data to {end_date}), vs every window of the same length since 2018-03; medians of six close times\n",
     f"{'set-up':16s} {'period':10s} {'return':>8s} {'percentile':>11s} {'10th pct':>9s} {'median':>8s} {'90th pct':>9s}"]
verdict = {}
for sname, _ in SETUPS:
    for lname, _ in LENS:
        rows = out[(sname, lname)]
        last, pct = med([x[0] for x in rows]), med([x[1] for x in rows])
        w = rows[0][2]
        L.append(f"{sname:16s} {lname:10s} {last:+8.1%} {pct:11.0%} {w[int(.1 * len(w))]:+9.1%} {w[len(w) // 2]:+8.1%} {w[int(.9 * len(w))]:+9.1%}")
        if lname == "6 months":
            verdict[sname] = "normal" if 0.10 <= pct <= 0.90 else ("unusually hard" if pct < 0.10 else "unusually good")
L.append("")
L += [f"verdict {s}: recent conditions {v}" for s, v in verdict.items()]
print("\n".join(L))
