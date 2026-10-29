"""Research round 46: what do missed days cost? (bot outages of days, not hours)

The OKX demo has not run since 2026-10-25 because GitHub stopped starting
its jobs (a billing block). Round 23 measured running hours late; this
measures whole days with no run at all: no stop checks, no trailing, no new
buys. Positions just sit; after the outage the bot sees only that day's
candle (a stop breached during the outage is caught only if the price is
still below it) and orders already queued fill late.

Cases (seeded random outage days, the same for every set-up): none; 5% of
days missed at random; one 3-day outage a month; one 7-day outage a month;
one 30-day outage a year. Steady set-up (8 x 0.5%, 6 checks, top 15), round
12's simulator and costs, round 21's six close times x two halves. No
backstop modelled (the Binance accounts don't have one).

Pass bar, decided before running (an "acceptable risk" test): an outage
pattern is tolerable if its 2022-26 median yearly return is no more than 3
points below no outages AND its median worst drop no more than 5 points
deeper. Patterns that fail it are the ones worth monitoring and fixing fast.
"""
import os as _os
import pickle
import random
from datetime import datetime, timezone

HERE = _os.path.dirname(_os.path.abspath(__file__))
src = open(_os.path.join(HERE, 'research21.py')).read()
ns21 = {'__file__': _os.path.join(HERE, 'research21.py'), '__name__': 'r46'}
exec(src[:src.index('\nL = [f"{len(raw[0])}')], ns21)
raw, unpack, OFFSETS, H, ROOT = ns21['raw'], ns21['unpack'], ns21['OFFSETS'], ns21['H'], ns21['ROOT']
from tradebot.opportunity import Opportunity, OppParams

src12 = open(_os.path.join(HERE, 'research12.py')).read()
head = src12[:src12.index('\nL = []')]
a = "    for t in times:\n"
assert head.count(a) == 1
head = head.replace(a, a + "        if (t - (t % 86_400_000)) in OUT:\n            curve.append((t, eq_of(t))); continue\n")


def simulate(data):
    pk = _os.path.join(ROOT, 'research', 'data', '_r46_tmp.pkl')
    pickle.dump(data, open(pk, 'wb'))
    ns = {'__file__': _os.path.join(HERE, 'research12.py'), '__name__': 'r46b', 'OUT': set()}
    exec(head.replace("cache = _os.path.join(OUT, 'daily_long.pkl')", f"cache = {pk!r}"), ns)
    _os.remove(pk)
    return ns


DAY = 86_400_000
START = int(datetime(2018, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
SPLIT = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
END = int(datetime(2026, 11, 1, tzinfo=timezone.utc).timestamp() * 1000)
days = list(range(START - START % DAY, END, DAY))
rng = random.Random(46)


def blocks(length, every):
    out = set()
    for s in range(0, len(days), every):
        k = s + rng.randrange(max(1, every - length))
        out.update(days[k:k + length])
    return out


PATTERNS = [("no outages", set()), ("5% of days at random", {d for d in days if rng.random() < 0.05}),
            ("3-day outage every month", blocks(3, 30)), ("7-day outage every month", blocks(7, 30)),
            ("30-day outage every year", blocks(30, 365))]
res = {}
for o in OFFSETS:
    ns = simulate(unpack(raw[o]))
    for half, (s, e) in (("2018-21", (START + o * H, SPLIT + o * H)), ("2022-26", (SPLIT + o * H, None))):
        for name, out in PATTERNS:
            ns['OUT'] = out
            res[(o, half, name)] = ns['metrics'](*ns['run'](make=lambda: Opportunity(OppParams(min_score=6)), max_open=8, risk=0.005, start=s, end=e))

med = lambda xs: sorted(xs)[len(xs) // 2]
REF = PATTERNS[0][0]
rb = med([res[(o, "2022-26", REF)]['cagr'] for o in OFFSETS]); rd = med([res[(o, "2022-26", REF)]['dd'] for o in OFFSETS])
L = ["Missed days (no run at all), steady set-up 8 x 0.5%, 6 checks, top 15; medians over six close times\n",
     f"{'outages':26s} {'days missed':>11s} {'2018-21 ret / Sh':>17s} {'2022-26 ret / Sh':>17s} {'DD 22-26':>9s} {'avg loss R 22-26':>20s} verdict"]
for name, out in PATTERNS:
    a = [res[(o, "2018-21", name)] for o in OFFSETS]; b = [res[(o, "2022-26", name)] for o in OFFSETS]
    ret, dd = med([m['cagr'] for m in b]), med([m['dd'] for m in b])
    worst = med([m['avg_loss'] for m in b])
    v = "REF" if name == REF else ("tolerable" if ret >= rb - 0.03 and dd >= rd - 0.05 else "NOT tolerable")
    L.append(f"{name:26s} {len(out) / len(days):11.0%} {med([m['cagr'] for m in a]):+8.1%} / {med([m['sharpe'] for m in a]):4.2f} "
             f"{ret:+8.1%} / {med([m['sharpe'] for m in b]):4.2f} {dd:9.1%} {worst:+20.2f} {v}")
print("\n".join(L))
